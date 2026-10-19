import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/backup_20_page.dart';

import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('backup 20 renders at the source canvas', (tester) async {
    await captureFidelityPage(
      tester,
      page: const Backup20Page(),
      size: Backup20Page.designSize,
      scale: 4,
      imageAssets: Backup20Assets.all,
      output: fidelityOutputPath('BACKUP_20_RENDER_OUTPUT'),
    );
  });

  testWidgets('backup 20 interactions remain available', (tester) async {
    tester.view.physicalSize = Backup20Page.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: Backup20Page(
        onReply: () => events.add('reply'),
        onProfile: (index) => events.add('profile:$index'),
        onNavigation: (index) => events.add('nav:$index'),
      ),
    ));
    await tester.tap(find.byKey(const ValueKey('backup20-reply')));
    await tester.tap(find.byKey(const ValueKey('backup20-profile-2')));
    await tester.tap(find.byKey(const ValueKey('backup20-navigation-1')));
    expect(events, ['reply', 'profile:2', 'nav:1']);
  });
}
