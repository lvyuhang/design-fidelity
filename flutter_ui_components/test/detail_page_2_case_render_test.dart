import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/detail_page_2_case.dart';

import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('detail page 2 renders at 4x source resolution', (tester) async {
    await captureFidelityPage(
      tester,
      page: const DetailPage2Case(),
      size: DetailPage2Case.designSize,
      scale: 4,
      imageAssets: DetailPage2Assets.all,
      output: fidelityOutputPath('DETAIL_PAGE_2_OUTPUT'),
    );
  });

  testWidgets('detail page preserves primary interactions', (tester) async {
    tester.view.physicalSize = DetailPage2Case.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var back = false;
    var comment = false;
    await tester.pumpWidget(MaterialApp(
        home: DetailPage2Case(
      onBack: () => back = true,
      onComment: () => comment = true,
    )));
    await tester.tap(find.byKey(const ValueKey('detail-page-2-back')));
    await tester.tap(find.byKey(const ValueKey('detail-page-2-comment-input')));
    expect(back, isTrue);
    expect(comment, isTrue);
  });
}
