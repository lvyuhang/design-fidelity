import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/platform_intro_optimized_page.dart';
import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  testWidgets('optimized platform introduction at source canvas',
      (tester) async {
    await captureFidelityPage(tester,
        page: const PlatformIntroOptimizedPage(),
        size: PlatformIntroOptimizedPage.designSize,
        scale: 4,
        imageAssets: PlatformIntroOptimizedAssets.all,
        output: fidelityOutputPath('PLATFORM_OPTIMIZED_OUTPUT'));
  });
  testWidgets('skip and start remain interactive', (tester) async {
    tester.view.physicalSize = PlatformIntroOptimizedPage.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: PlatformIntroOptimizedPage(
            onSkip: () => events.add('skip'),
            onStart: () => events.add('start'))));
    await tester.tap(find.byKey(const ValueKey('platform-optimized-skip')));
    await tester.tap(find.byKey(const ValueKey('platform-optimized-start')));
    expect(events, ['skip', 'start']);
  });
}
