import 'dart:io';
import 'dart:convert';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/gender_direct.dart';
import 'package:juxing_components/experiments/gender_experiment_page.dart';
import 'package:juxing_components/experiments/gender_sol56_direct.dart';
import 'package:juxing_components/components/social_components.dart';

class GenderProductionShadowBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

void main() {
  GenderProductionShadowBinding();
  late Map<String, dynamic> report;
  setUpAll(() async {
    report = jsonDecode(await rootBundle
            .loadString('assets/experiments/gender-direct/evaluation.json'))
        as Map<String, dynamic>;
    final fonts = FontLoader('SourcePingFang');
    for (final weight in ['Regular', 'Medium', 'Semibold']) {
      fonts.addFont(rootBundle.load('assets/fonts/PingFangSC-$weight.otf'));
    }
    await fonts.load();
  });
  testWidgets(
      'direct gender stays controlled and emits both selection callbacks',
      (tester) async {
    final actions = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: Center(child: DirectGenderSelection(onSelect: actions.add))));
    expect(tester.getSize(find.byType(DirectGenderSelection)),
        const Size(375, 350));
    await tester.tap(find.text('男生'));
    await tester.tap(find.text('女生'));
    expect(actions, ['male', 'female']);
    expect(find.text('选择性别提交后将不可修改'), findsNothing);
    await tester.pumpWidget(MaterialApp(
        home: Center(
            child: DirectGenderSelection(
                femaleSelected: true, onSelect: actions.add))));
    expect(find.text('选择性别提交后将不可修改'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('5.6 Sol frozen gender emits both selection callbacks',
      (tester) async {
    final actions = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: Center(child: Sol56GenderSelection(onSelect: actions.add))));
    expect(tester.getSize(find.byType(Sol56GenderSelection)),
        const Size(375, 350));
    await tester.tap(find.text('男生'));
    await tester.tap(find.text('女生'));
    expect(actions, ['male', 'female']);
    await tester.pumpWidget(MaterialApp(
        home: const Center(child: Sol56GenderSelection(femaleSelected: true))));
    expect(find.text('选择性别提交后将不可修改'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  for (final width in [375.0, 1240.0]) {
    testWidgets(
        'gender comparison switches both fixtures and overlay at $width',
        (tester) async {
      tester.view.physicalSize = Size(width, 1100);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
          MaterialApp(home: GenderExperimentPage(evaluationData: report)));
      await tester.pumpAndSettle();
      expect(tester.getSize(find.byType(DirectGenderSelection)),
          const Size(375, 350));
      expect(tester.getSize(find.byType(Sol56GenderSelection)),
          const Size(375, 350));
      expect(
          tester.getSize(find.byType(GenderSelection)), const Size(375, 350));
      await tester.tap(find.byKey(const ValueKey('state-female')));
      await tester.pumpAndSettle();
      expect(
          tester
              .widget<DirectGenderSelection>(find.byType(DirectGenderSelection))
              .femaleSelected,
          isTrue);
      expect(
          tester
              .widget<Sol56GenderSelection>(find.byType(Sol56GenderSelection))
              .femaleSelected,
          isTrue);
      expect(
          tester
              .widget<GenderSelection>(find.byType(GenderSelection))
              .femaleSelected,
          isTrue);
      expect(find.text('选择性别提交后将不可修改'), findsNWidgets(3));
      await tester.tap(find.byKey(const ValueKey('mode-overlay-sol56')));
      await tester.pumpAndSettle();
      expect(find.byType(GenderSelection), findsNothing);
      expect(find.byType(DirectGenderSelection), findsNothing);
      expect(tester.getSize(find.byType(Sol56GenderSelection)),
          const Size(375, 350));
      await tester.tap(find.byKey(const ValueKey('state-none')));
      await tester.pumpAndSettle();
      expect(
          tester
              .widget<Sol56GenderSelection>(find.byType(Sol56GenderSelection))
              .femaleSelected,
          isFalse);
      expect(find.text('选择性别提交后将不可修改'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }
  for (final state in ['none', 'female']) {
    for (final variant in ['sol56', 'direct', 'calibrated']) {
      testWidgets('render frozen $state $variant at native 4x', (tester) async {
        final key = GlobalKey();
        final selected = state == 'female';
        await tester.pumpWidget(MaterialApp(
            home: Center(
                child: RepaintBoundary(
                    key: key,
                    child: switch (variant) {
                      'sol56' => Sol56GenderSelection(femaleSelected: selected),
                      'direct' =>
                        DirectGenderSelection(femaleSelected: selected),
                      _ => GenderSelection(femaleSelected: selected),
                    }))));
        await tester.runAsync(() async {
          for (final asset in [
            DirectGenderSelection.maleAsset,
            DirectGenderSelection.femaleAsset,
            DirectGenderSelection.selectedAsset,
            DirectGenderSelection.checkAsset,
            DirectGenderSelection.warningAsset,
            if (selected && variant == 'calibrated')
              'assets/fixtures/warning-shield.png'
          ]) {
            await precacheImage(AssetImage(asset), key.currentContext!);
          }
        });
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        await tester.runAsync(() async {
          final boundary =
              key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
          final img = await boundary.toImage(pixelRatio: 4);
          final bytes = await img.toByteData(format: ui.ImageByteFormat.png);
          await File('../design_evidence/gender-direct/$state-$variant-4x.png')
              .writeAsBytes(bytes!.buffer.asUint8List());
          img.dispose();
        });
      });
    }
  }
}
