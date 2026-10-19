import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/complaint_record_empty_page.dart';

import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('complaint empty page renders at source canvas', (tester) async {
    await captureFidelityPage(
      tester,
      page: const ComplaintRecordEmptyPage(),
      size: ComplaintRecordEmptyPage.designSize,
      scale: 4,
      imageAssets: ComplaintRecordEmptyAssets.all,
      output: fidelityOutputPath('COMPLAINT_EMPTY_OUTPUT'),
    );
  });

  testWidgets('back interaction remains available', (tester) async {
    tester.view.physicalSize = ComplaintRecordEmptyPage.designSize;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var tapped = false;
    await tester.pumpWidget(MaterialApp(
      home: ComplaintRecordEmptyPage(onBack: () => tapped = true),
    ));
    await tester.tap(find.byKey(const ValueKey('complaint-empty-back')));
    expect(tapped, isTrue);
  });
}
