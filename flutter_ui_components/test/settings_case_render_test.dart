import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/settings_case_page.dart';

import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('settings page renders at 4x source resolution', (tester) async {
    await captureFidelityPage(
      tester,
      page: const SettingsCasePage(),
      size: SettingsCasePage.designSize,
      scale: 4,
      imageAssets: SettingsCaseAssets.all,
      output: fidelityOutputPath('SETTINGS_CASE_OUTPUT'),
    );
  });

  testWidgets('settings rows preserve component interaction', (tester) async {
    tester.view.physicalSize = SettingsCasePage.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    String? tapped;
    await tester.pumpWidget(
        MaterialApp(home: SettingsCasePage(onItemTap: (v) => tapped = v)));
    await tester.tap(find.byKey(const ValueKey('settings-row-青少年模式')));
    expect(tapped, '青少年模式');
  });

  testWidgets('page title has an unclipped centered layout box',
      (tester) async {
    tester.view.physicalSize = SettingsCasePage.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: SettingsCasePage()));
    final title = find.byKey(const ValueKey('settings-case-title'));
    expect(find.text('设置'), findsOneWidget);
    expect(tester.getSize(title).width, 375);
    expect(tester.getCenter(title).dx, 187.5);
  });
}
