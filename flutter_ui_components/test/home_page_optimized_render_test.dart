import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/components/expanded_components.dart';
import 'package:juxing_components/components/source_primitives.dart';
import 'package:juxing_components/experiments/home_page_optimized.dart';

import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('home page optimized renders at the source canvas',
      (tester) async {
    await captureFidelityPage(
      tester,
      page: const HomePageOptimized(),
      size: HomePageOptimized.designSize,
      scale: 4,
      imageAssets: HomePageAssets.all,
      output: fidelityOutputPath('HOME_PAGE_OPTIMIZED_OUTPUT'),
    );
  });

  testWidgets('home page actions remain available', (tester) async {
    tester.view.physicalSize = HomePageOptimized.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: HomePageOptimized(
        onCard: (index) => events.add('card:$index'),
        onCompose: () => events.add('compose'),
        onNavigation: (index) => events.add('nav:$index'),
      ),
    ));
    await tester.tap(find.byKey(const ValueKey('home-card-1')));
    await tester.tap(find.byKey(const ValueKey('home-compose')));
    await tester.tap(find.byKey(const ValueKey('nav-0')));
    expect(events, ['card:1', 'compose', 'nav:0']);
  });

  testWidgets('author status line keeps the measured gap under long content',
      (tester) async {
    tester.view.physicalSize = const Size(90, 24);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(
      home: Align(
        alignment: Alignment.topLeft,
        child: SizedBox(
          width: 90,
          child: AuthorStatusLine(
            name: '这是一个超过可用宽度的用户名',
            status: '忙碌',
            statusColor: Color(0xFFF94F2D),
          ),
        ),
      ),
    ));
    final name =
        tester.getRect(find.byKey(const ValueKey('author-status-name')));
    final chip =
        tester.getRect(find.byKey(const ValueKey('author-status-chip')));
    expect(chip.left - name.right, closeTo(2, .01));
    expect(name.right, lessThanOrEqualTo(chip.left));
    expect(chip.width, 33);
  });

  testWidgets('three-character source name is not prematurely ellipsized',
      (tester) async {
    tester.view.physicalSize = const Size(90, 24);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(
      home: Align(
        alignment: Alignment.topLeft,
        child: SizedBox(
          width: 90,
          child: AuthorStatusLine(
            name: '少年葩',
            status: '在线',
            statusColor: Color(0xFF1EBA3E),
          ),
        ),
      ),
    ));
    final name =
        tester.getRect(find.byKey(const ValueKey('author-status-name')));
    final chip =
        tester.getRect(find.byKey(const ValueKey('author-status-chip')));
    expect(chip.left - name.right, closeTo(2, .01));
    expect(name.width, greaterThanOrEqualTo(33));
    expect(chip.left, lessThanOrEqualTo(57));
  });

  testWidgets(
      'navigation overlay excludes root background and retains alpha stops',
      (tester) async {
    await tester.pumpWidget(const Directionality(
      textDirection: TextDirection.ltr,
      child: NavigationComponentStage(includeCanvasBackground: false),
    ));
    final ids = tester
        .widgetList<CustomPaint>(find.byType(CustomPaint))
        .map((widget) => widget.painter)
        .whereType<SourceShapePainter>()
        .map((painter) => painter.spec['sourceId'])
        .toSet();
    expect(ids, contains('F2083B30-CFB9-4FC7-A05B-047A7D0A2FBA'));
    expect(ids, isNot(contains('401D0155-DFE5-4E09-9C2D-89EBA74145FC')));
    final fade = sourceNode('nav', 'F2083B30-CFB9-4FC7-A05B-047A7D0A2FBA');
    final stops = ((fade['fills'] as List).single['gradient']
        as Map<String, dynamic>)['colorStops'] as List;
    expect(stops.first['color']['a'], 0);
    expect(stops.last['color']['a'], 1);
  });
}
