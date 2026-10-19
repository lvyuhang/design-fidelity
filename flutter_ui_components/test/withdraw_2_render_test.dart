import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/withdraw_2_page.dart';
import 'package:juxing_components/main.dart';
import 'package:flutter/rendering.dart';

import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('production theme keeps withdrawal title on a single line',
      (tester) async {
    tester.view.physicalSize = const Size(1100, 1100);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester
        .pumpWidget(const ComponentLab(caseName: 'withdraw-2-skill2186'));
    await tester.pumpAndSettle();
    final paragraph = tester.renderObject<RenderParagraph>(find.text('提现'));
    final boxes = paragraph.getBoxesForSelection(
        const TextSelection(baseOffset: 0, extentOffset: 2));
    expect(boxes.length, 1,
        reason: 'Title must not wrap within the source frame');
    // Font ascent/descent may extend a fraction beyond the logical line box.
    expect(boxes.single.bottom, lessThanOrEqualTo(paragraph.size.height + .5));
  });

  testWidgets('withdraw 2 renders at 4x source resolution', (tester) async {
    await captureFidelityPage(
      tester,
      page: const Withdraw2Page(),
      size: Withdraw2Page.designSize,
      scale: 4,
      imageAssets: Withdraw2Assets.all,
      output: fidelityOutputPath('WITHDRAW_2_OUTPUT'),
      appBuilder: (child) => ComponentLab(pageOverride: child),
    );
  });

  testWidgets('withdraw 2 preserves back and confirm interactions',
      (tester) async {
    tester.view.physicalSize = Withdraw2Page.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var back = false;
    var confirm = false;
    await tester.pumpWidget(MaterialApp(
        home: Withdraw2Page(
      onBack: () => back = true,
      onConfirm: () => confirm = true,
    )));
    await tester.tap(find.byKey(const ValueKey('withdraw-2-back')));
    await tester.tap(find.byKey(const ValueKey('withdraw-2-confirm')));
    expect(back, isTrue);
    expect(confirm, isTrue);
  });
}
