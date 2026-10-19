import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/backup_20_skill212_page.dart';
import 'package:juxing_components/experiments/backup_21_skill213_page.dart';

import 'support/fidelity_render_harness.dart';
import 'backup_20_source_details_test.dart' as details;

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  details.registerSourceDetailTests(loadFonts: false);

  testWidgets('skill 2.13 reuse case renders at the source canvas',
      (tester) async {
    await captureFidelityPage(
      tester,
      page: const Backup21Skill213Page(),
      size: Backup21Skill213Page.designSize,
      scale: 4,
      imageAssets: Backup20Skill212Assets.all,
      output: fidelityOutputPath('BACKUP_21_SKILL213_RENDER_OUTPUT'),
    );
  });

  testWidgets('reused controls remain interactive', (tester) async {
    tester.view.physicalSize = Backup21Skill213Page.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: Backup21Skill213Page(
        onReply: () => events.add('reply'),
        onProfile: (index) => events.add('profile:$index'),
        onNavigation: (index) => events.add('nav:$index'),
      ),
    ));
    expect(find.text('[语音] 7”'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('backup20-skill212-reply')));
    await tester.tap(find.byKey(const ValueKey('backup20-skill212-profile-2')));
    await tester
        .tap(find.byKey(const ValueKey('backup20-skill212-navigation-1')));
    expect(events, ['reply', 'profile:2', 'nav:1']);
  });
}
