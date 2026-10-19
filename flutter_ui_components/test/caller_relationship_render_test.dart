import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/caller_relationship_page.dart';

class ProductionShadowTestBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

void main() {
  ProductionShadowTestBinding();

  setUpAll(() async {
    final fonts = FontLoader('SourcePingFang');
    for (final weight in ['Regular', 'Medium', 'Semibold']) {
      fonts.addFont(rootBundle.load('assets/fonts/PingFangSC-$weight.otf'));
    }
    await fonts.load();
  });

  testWidgets('caller relationship screen renders at source 2x',
      (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final boundaryKey = GlobalKey();
    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        home: ColoredBox(
          color: Colors.black,
          child: Center(
            child: RepaintBoundary(
              key: boundaryKey,
              child: const CallerRelationshipScreen(),
            ),
          ),
        ),
      ),
    );
    await tester.runAsync(() async {
      for (final asset in CallerRelationshipAssets.all) {
        await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
      }
    });
    await tester.pumpAndSettle();

    expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
    expect(tester.takeException(), isNull);

    await tester.runAsync(() async {
      final boundary = boundaryKey.currentContext!.findRenderObject()!
          as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 2);
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final output = File(
        Platform.environment['CALLER_RENDER_OUTPUT'] ??
            '../design_evidence/caller-relationship/r0/render.png',
      );
      await output.parent.create(recursive: true);
      await output.writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('caller foreground actions remain interactive', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var close = 0;
    var message = 0;
    var gift = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Center(
          child: CallerRelationshipScreen(
            onClose: () => close++,
            onMessage: () => message++,
            onGift: () => gift++,
          ),
        ),
      ),
    );
    await tester.tap(find.bySemanticsLabel('关闭关系详情'));
    await tester.tap(find.bySemanticsLabel('发送文字'));
    await tester.tap(find.bySemanticsLabel('送礼物'));
    expect((close, message, gift), (1, 1, 1));
    expect(tester.takeException(), isNull);
  });
}
