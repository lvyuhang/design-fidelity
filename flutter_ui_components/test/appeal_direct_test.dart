import 'dart:io';
import 'dart:convert';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/appeal_direct.dart';
import 'package:juxing_components/experiments/appeal_experiment_page.dart';
import 'package:juxing_components/components/expanded_components.dart';

class ProductionShadowTestBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

void main() {
  ProductionShadowTestBinding();
  late Map<String, dynamic> report;
  setUpAll(() async {
    report = jsonDecode(await rootBundle
            .loadString('assets/experiments/appeal-direct/evaluation.json'))
        as Map<String, dynamic>;
    final fonts = FontLoader('SourcePingFang');
    for (final weight in ['Regular', 'Medium', 'Semibold']) {
      fonts.addFont(rootBundle.load('assets/fonts/PingFangSC-$weight.otf'));
    }
    await fonts.load();
  });
  testWidgets('frozen direct card keeps 375px stage and appeal callback',
      (tester) async {
    var actions = 0;
    await tester.pumpWidget(MaterialApp(
        home: Center(child: DirectAppealStage(onAppeal: () => actions++))));
    expect(
        tester.getSize(find.byType(DirectAppealStage)), const Size(375, 125));
    expect(tester.getSize(find.byType(DirectAppealCard)), const Size(343, 116));
    await tester.tapAt(tester.getCenter(find.text('申诉')));
    expect(actions, 1);
    expect(tester.takeException(), isNull);
  });
  for (final width in [375.0, 1240.0]) {
    testWidgets('experiment keeps actual-size stages on $width viewport',
        (tester) async {
      tester.view.physicalSize = Size(width, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
          MaterialApp(home: AppealExperimentPage(evaluationData: report)));
      await tester.pumpAndSettle();
      expect(
          tester.getSize(find.byType(DirectAppealStage)), const Size(375, 125));
      expect(tester.getSize(find.byType(AppealComponentStage)),
          const Size(375, 125));
      expect(find.text('局部放大，查看偏差'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
  for (final entry in <String, Widget>{
    'direct': const DirectAppealStage(),
    'calibrated': const AppealComponentStage(),
  }.entries) {
    testWidgets('evaluate frozen ${entry.key} at source 4x', (tester) async {
      final key = GlobalKey();
      await tester.pumpWidget(MaterialApp(
          home: Center(child: RepaintBoundary(key: key, child: entry.value))));
      await tester.runAsync(() async {
        await precacheImage(const AssetImage(DirectAppealCard.shieldAsset),
            key.currentContext!);
      });
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.runAsync(() async {
        final boundary =
            key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
        final img = await boundary.toImage(pixelRatio: 4);
        final bytes = await img.toByteData(format: ui.ImageByteFormat.png);
        await File('../design_evidence/appeal-direct/${entry.key}-4x.png')
            .writeAsBytes(bytes!.buffer.asUint8List());
        img.dispose();
      });
    });
  }
}
