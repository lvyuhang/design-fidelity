import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/components_model_comparison_page.dart';
import 'package:juxing_components/experiments/social_sol56.dart';
import 'package:juxing_components/components/social_components.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Map<String, dynamic> report;
  late Map<String, dynamic> genderReport;
  setUpAll(() async {
    final fonts = FontLoader('SourcePingFang');
    for (final weight in ['Regular', 'Medium', 'Semibold']) {
      fonts.addFont(rootBundle.load('assets/fonts/PingFangSC-$weight.otf'));
    }
    await fonts.load();
    report = jsonDecode(await rootBundle
            .loadString('assets/experiments/components-sol56/evaluation.json'))
        as Map<String, dynamic>;
    genderReport = jsonDecode(await rootBundle
            .loadString('assets/experiments/gender-direct/evaluation.json'))
        as Map<String, dynamic>;
  });

  for (final width in [375.0, 1240.0]) {
    testWidgets('comparison keeps live 375px stages on $width viewport',
        (tester) async {
      tester.view.physicalSize = Size(width, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(MaterialApp(
        home: ComponentsModelComparisonPage(
          evaluationData: report,
          genderEvaluationData: genderReport,
        ),
      ));
      await tester.pumpAndSettle();

      expect(tester.getSize(find.byType(Sol56FeedComponentStage)).width, 375);
      expect(tester.getSize(find.byType(FeedComponentStage)).width, 375);
      expect(find.text('GPT-5.6 Sol · high'), findsOneWidget);
      expect(find.text('此前 GPT-6'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('sample and overlay controls switch the live comparison',
      (tester) async {
    tester.view.physicalSize = const Size(1240, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(MaterialApp(
      home: ComponentsModelComparisonPage(
        evaluationData: report,
        genderEvaluationData: genderReport,
      ),
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('sample-comments')));
    await tester.pumpAndSettle();
    expect(find.byType(Sol56CommentPanel), findsOneWidget);
    expect(find.byType(CommentPanel), findsOneWidget);

    await tester
        .ensureVisible(find.byKey(const ValueKey('mode-overlay-sol56')));
    await tester.tap(find.byKey(const ValueKey('mode-overlay-sol56')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('overlay-opacity')), findsOneWidget);
    expect(find.byType(Sol56CommentPanel), findsOneWidget);
    expect(find.byType(CommentPanel), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
