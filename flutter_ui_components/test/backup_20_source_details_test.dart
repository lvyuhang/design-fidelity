import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/backup_20_skill212_page.dart';

import 'support/fidelity_render_harness.dart';

// Read the pinned MCP evidence, not constants copied from the implementation.
void main() {
  FidelityTestBinding();
  registerSourceDetailTests();
}

void registerSourceDetailTests({bool loadFonts = true}) {
  final nodes = <String, Map<String, dynamic>>{};
  setUpAll(() async {
    if (loadFonts) await loadDeclaredFidelityFonts();
    for (final file in Directory(
            '../design_evidence/backup-20-skill211/normalized-source')
        .listSync()
        .whereType<File>()
        .where((f) => f.path.contains('region-') && f.path.endsWith('.json'))) {
      for (final node in jsonDecode(file.readAsStringSync())['nodes'] as List) {
        nodes[node['node_id'] as String] = Map<String, dynamic>.from(node);
      }
    }
  });

  Color sourceColor(Map<String, dynamic> node) {
    final raw = node['raw_style'];
    final fill = raw['fills'][0];
    final color = fill['color'];
    return Color.fromARGB(
        ((raw['opacity'] ?? 100) /
                100 *
                (fill['opacity'] ?? 1) *
                color['a'] *
                255)
            .round(),
        color['r'] as int,
        color['g'] as int,
        color['b'] as int);
  }

  void expectFrame(WidgetTester tester, String key, Map<String, dynamic> node) {
    final actual = tester.getRect(find.byKey(ValueKey(key)));
    final b = node['bounds'];
    final expected = Rect.fromLTWH(
        (b['x'] as num).toDouble(),
        (b['y'] as num).toDouble(),
        (b['width'] as num).toDouble(),
        (b['height'] as num).toDouble());
    expect((actual.topLeft - expected.topLeft).distance, lessThan(0.000001),
        reason: '$key source position');
    expect((actual.bottomRight - expected.bottomRight).distance,
        lessThan(0.000001),
        reason: '$key source size');
  }

  testWidgets('presence layers retain MCP geometry paint and outside border',
      (tester) async {
    tester.view.physicalSize = Backup20Skill212Page.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: Backup20Skill212Page()));
    const backgrounds = [
      'E0206867-11BC-4914-8824-D09EA062668A',
      'DAB00984-04E8-41AD-91A3-A19AEA03503A',
      '4536E2D3-DD25-42C2-85AE-2DACE86B0928',
      '5DAD5376-75D2-4F73-8970-C5C58425CD14',
      'AAC6B26C-6B76-4E3F-B108-C4985714571D',
      'B24E551D-62C0-4883-855C-7AB42B05B495',
    ];
    for (var index = 0; index < backgrounds.length; index++) {
      final node = nodes[backgrounds[index]]!;
      final key = 'backup20-presence-$index';
      expectFrame(tester, key, node);
      final decoration = tester
          .widget<DecoratedBox>(find.byKey(ValueKey(key)))
          .decoration as BoxDecoration;
      expect(decoration.color, sourceColor(node),
          reason: '$key fill and alpha');
      expect(
          decoration.borderRadius,
          BorderRadius.circular(
              (node['raw_style']['radius'][0] as num).toDouble()));
      final text = nodes.values.singleWhere(
          (n) => n['parent_id'] == node['parent_id'] && n['text'] != null);
      expectFrame(tester, 'backup20-presence-text-$index', text);
    }
    final node = nodes['5ED6A986-C36F-4AF8-A9CE-1827B02D04B3']!;
    const key = 'backup20-avatar-online';
    expectFrame(tester, key, node);
    final decoration = tester
        .widget<DecoratedBox>(find.byKey(const ValueKey(key)))
        .decoration as BoxDecoration;
    expect(decoration.color, sourceColor(node));
    expect(decoration.shape, BoxShape.circle);
    final border = (decoration.border as Border).top;
    final source = node['raw_style']['borders'][0];
    expect(border.width, source['thickness']);
    expect(source['position'], '外边框');
    expect(border.strokeAlign, BorderSide.strokeAlignOutside);
    expect(tester.takeException(), isNull);
  });
}
