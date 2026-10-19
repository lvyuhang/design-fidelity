import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/backup_20_skill212_page.dart';

import 'support/fidelity_render_harness.dart';
import 'backup_20_source_details_test.dart' as details;

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  details.registerSourceDetailTests(loadFonts: false);

  testWidgets('skill 2.12 rebuild renders at the source canvas',
      (tester) async {
    await captureFidelityPage(
      tester,
      page: const Backup20Skill212Page(),
      size: Backup20Skill212Page.designSize,
      scale: 4,
      imageAssets: Backup20Skill212Assets.all,
      output: fidelityOutputPath('BACKUP_20_SKILL212_RENDER_OUTPUT'),
    );
  });

  testWidgets('native controls remain interactive', (tester) async {
    tester.view.physicalSize = Backup20Skill212Page.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: Backup20Skill212Page(
        onReply: () => events.add('reply'),
        onProfile: (index) => events.add('profile:$index'),
        onNavigation: (index) => events.add('nav:$index'),
      ),
    ));
    await tester.tap(find.byKey(const ValueKey('backup20-skill212-reply')));
    await tester.tap(find.byKey(const ValueKey('backup20-skill212-profile-2')));
    await tester
        .tap(find.byKey(const ValueKey('backup20-skill212-navigation-1')));
    expect(events, ['reply', 'profile:2', 'nav:1']);
  });
}
