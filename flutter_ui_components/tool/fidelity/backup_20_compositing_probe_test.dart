// Diagnostic probe for the existing implementation, deliberately outside the
// accepted test suite. Read source evidence; do not bless current UI constants.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/backup_20_skill212_page.dart';

import '../../test/support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  final nodes = <String, dynamic>{};
  setUpAll(() async {
    await loadDeclaredFidelityFonts();
    for (final file in Directory(
            '../design_evidence/backup-20-skill211/normalized-source')
        .listSync()
        .whereType<File>()
        .where((f) => f.path.contains('region-') && f.path.endsWith('.json'))) {
      for (final node in jsonDecode(file.readAsStringSync())['nodes'] as List) {
        nodes[node['node_id']] = node;
      }
    }
  });

  Future<void> mount(WidgetTester tester) async {
    tester.view.physicalSize = Backup20Skill212Page.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: Backup20Skill212Page()));
  }

  testWidgets('navigation retains source fill alpha', (tester) async {
    await mount(tester);
    final source = nodes['F9324B1E-8DC1-438F-9B9E-E23B471E8E2A'];
    final frame = source['bounds'];
    final expected = Rect.fromLTWH(
        (frame['x'] as num).toDouble(), (frame['y'] as num).toDouble(),
        (frame['width'] as num).toDouble(), (frame['height'] as num).toDouble());
    final boxes = find.byType(DecoratedBox).evaluate().where((e) {
      final box = e.findRenderObject()! as RenderBox;
      return (box.localToGlobal(Offset.zero) & box.size) == expected;
    });
    expect(boxes, hasLength(1));
    final paint = (boxes.single.widget as DecoratedBox).decoration as BoxDecoration;
    final alpha = source['raw_style']['fills'][0]['color']['a'] as num;
    expect(paint.color!.a, closeTo(alpha.toDouble(), 1 / 255),
        reason: 'Source alpha must survive content placeholders');
  });

  testWidgets('navigation retains an actual background filter', (tester) async {
    await mount(tester);
    final source = nodes['F9324B1E-8DC1-438F-9B9E-E23B471E8E2A'];
    expect(source['raw_style']['blur']['type'], '背景模糊');
    expect(find.byType(BackdropFilter), findsWidgets,
        reason: 'BoxShadow blur does not filter the backdrop');
  });

  testWidgets('exported boundary overlay remains a separate image layer',
      (tester) async {
    await mount(tester);
    final manifest = jsonDecode(File(
            '../design_evidence/backup-20-skill211/source-bundle/install-receipt.json')
        .readAsStringSync());
    final asset = (manifest['assets'] as List).firstWhere((a) =>
        a['node_id'] == 'B99F5E54-8C35-4DE5-8FB1-06DDD20856CF');
    final filename = (asset['local_path'] as String).split('/').last;
    expect(find.byWidgetPredicate((w) => w is Image && w.image is AssetImage &&
        (w.image as AssetImage).assetName.endsWith(filename)), findsWidgets,
        reason: 'Missing portrait does not justify removing the exported rim');
  });
}
