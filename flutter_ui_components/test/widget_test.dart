import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/components/login_components.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    final font = FontLoader('SourcePingFang');
    font.addFont(rootBundle.load('assets/fonts/PingFangSC-Regular.otf'));
    font.addFont(rootBundle.load('assets/fonts/PingFangSC-Semibold.otf'));
    await font.load();
  });

  testWidgets('375px canvas, source button geometry and real tap callback',
      (tester) async {
    String? tapped;
    await tester.pumpWidget(MaterialApp(
        home: Center(
            child: LoginComponentStage(onProviderTap: (id) => tapped = id))));
    await tester.pumpAndSettle();
    expect(
        tester.getSize(find.byType(LoginComponentStage)), const Size(375, 395));
    final stageOrigin = tester.getTopLeft(find.byType(LoginComponentStage));
    for (final spec in LoginDesign.providers) {
      final finder = find.byKey(ValueKey(spec.id));
      expect(tester.getSize(finder), const Size(299, 50));
      expect(tester.getTopLeft(finder) - stageOrigin, Offset(38, spec.y - 389));
    }
    await tester.tap(find.byKey(const ValueKey('wechat')));
    expect(tapped, 'wechat');
    expect(tester.takeException(), isNull);
  });

  for (final fixture in const <String, Rect>{
    'buttons': Rect.fromLTWH(24, 393, 327, 278),
    'agreement': Rect.fromLTWH(20, 729, 335, 52),
    'region': LoginDesign.stage,
  }.entries) {
    testWidgets('render ${fixture.key} at 4x for source comparison',
        (tester) async {
      final key = GlobalKey();
      await tester.pumpWidget(MaterialApp(
          home: Center(
              child: RepaintBoundary(
                  key: key,
                  child: LoginComponentStage(region: fixture.value)))));
      await tester.runAsync(() async {
        final context = key.currentContext!;
        for (final p in LoginDesign.providers) {
          await precacheImage(AssetImage(p.asset), context);
        }
        await precacheImage(const AssetImage(LoginDesign.ringAsset), context);
      });
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      final boundary =
          key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
      await tester.runAsync(() async {
        final image = await boundary.toImage(pixelRatio: 4);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        final out = File('../design_evidence/flutter-${fixture.key}-4x.png');
        await out.writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    });
  }
}
