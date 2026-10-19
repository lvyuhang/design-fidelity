import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/full_page_gpt6.dart';
import 'package:juxing_components/experiments/full_page_gpt6_r1.dart';
import 'package:juxing_components/experiments/full_page_gpt6_r2.dart';
import 'package:juxing_components/experiments/full_page_model_comparison_page.dart';
import 'package:juxing_components/experiments/full_page_sol56.dart';
import 'package:juxing_components/experiments/full_page_sol56_r1.dart';
import 'package:juxing_components/experiments/full_page_sol56_r2.dart';

void main() {
  final report = <String, dynamic>{
    'regions': {
      'whole': {
        'sol56': {'mean_abs_rgb_0_255': 10.0},
        'gpt6': {'mean_abs_rgb_0_255': 11.0},
        'sol56_r1': {'mean_abs_rgb_0_255': 8.0},
        'gpt6_r1': {'mean_abs_rgb_0_255': 9.0},
        'sol56_r2': {'mean_abs_rgb_0_255': 6.0},
        'gpt6_r2': {'mean_abs_rgb_0_255': 7.0},
      },
      'native': {
        'sol56': {'mean_abs_rgb_0_255': 12.0},
        'gpt6': {'mean_abs_rgb_0_255': 13.0},
        'sol56_r1': {'mean_abs_rgb_0_255': 9.0},
        'gpt6_r1': {'mean_abs_rgb_0_255': 10.0},
        'sol56_r2': {'mean_abs_rgb_0_255': 7.0},
        'gpt6_r2': {'mean_abs_rgb_0_255': 8.0},
      },
    },
  };

  for (final width in [375.0, 1240.0]) {
    testWidgets('full page comparison keeps 375px canvases at $width',
        (tester) async {
      tester.view.physicalSize = Size(width, 1200);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: FullPageModelComparisonPage(evaluationData: report),
        ),
      );
      await tester.pumpAndSettle();

      expect(tester.getSize(find.byType(Sol56PlatformIntroPageR2)).width, 375);
      expect(tester.getSize(find.byType(Gpt6PlatformIntroPageR2)).width, 375);
      expect(find.text('GPT-5.6 Sol · high'), findsOneWidget);
      expect(find.text('GPT-6 · high'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('overlay modes and live callbacks work', (tester) async {
    tester.view.physicalSize = const Size(1240, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: FullPageModelComparisonPage(evaluationData: report),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(
      find.descendant(
        of: find.byType(Sol56PlatformIntroPageR2),
        matching: find.text('开始入驻'),
      ),
    );
    await tester.pump();
    expect(find.text('GPT-5.6 Sol R2：onStart'), findsOneWidget);

    await tester.ensureVisible(
      find.byKey(const ValueKey('full-page-mode-overlay-gpt6')),
    );
    await tester.tap(find.byKey(const ValueKey('full-page-mode-overlay-gpt6')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('full-page-overlay-opacity')),
        findsOneWidget);
    expect(find.byType(Gpt6PlatformIntroPageR2), findsOneWidget);
    expect(find.byType(Sol56PlatformIntroPageR2), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('R1 switch replaces both live implementations', (tester) async {
    tester.view.physicalSize = const Size(1240, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: FullPageModelComparisonPage(evaluationData: report),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(
      find.byKey(const ValueKey('full-page-revision-r1')),
    );
    await tester.pumpAndSettle();
    expect(find.byType(Sol56PlatformIntroPageR1), findsOneWidget);
    expect(find.byType(Gpt6PlatformIntroPageR1), findsOneWidget);
    expect(find.byType(Sol56PlatformIntroPage), findsNothing);
    expect(find.byType(Gpt6PlatformIntroPage), findsNothing);
    expect(find.text('视觉修正 R1 · 1 轮'), findsNWidgets(2));
    expect(tester.takeException(), isNull);
  });
}
