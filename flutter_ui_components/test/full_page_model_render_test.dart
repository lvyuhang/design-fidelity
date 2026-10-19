import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/full_page_gpt6.dart';
import 'package:juxing_components/experiments/full_page_sol56.dart';

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

  const imageAssets = <String>[
    'assets/lanhu/full_page/hero.png',
    'assets/lanhu/full_page/title_art.png',
    'assets/lanhu/full_page/capability_badge.png',
    'assets/lanhu/full_page/capability_1.png',
    'assets/lanhu/full_page/capability_2.png',
    'assets/lanhu/full_page/capability_3.png',
    'assets/lanhu/full_page/capability_4.png',
    'assets/lanhu/full_page/reward_badge.png',
    'assets/lanhu/full_page/reward_1.png',
    'assets/lanhu/full_page/reward_2.png',
    'assets/lanhu/full_page/reward_3.png',
  ];

  final variants = <String, Widget>{
    'sol56': const Sol56PlatformIntroPage(),
    'gpt6': const Gpt6PlatformIntroPage(),
  };

  for (final variant in variants.entries) {
    testWidgets('frozen first render ${variant.key} at source 4x',
        (tester) async {
      tester.view.physicalSize = const Size(375, 812);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final boundaryKey = GlobalKey();
      await tester.pumpWidget(
        MaterialApp(
          debugShowCheckedModeBanner: false,
          home: Center(
            child: RepaintBoundary(
              key: boundaryKey,
              child: variant.value,
            ),
          ),
        ),
      );
      await tester.runAsync(() async {
        for (final asset in imageAssets) {
          await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
        }
      });
      await tester.pumpAndSettle();
      expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
      expect(tester.takeException(), isNull);

      await tester.runAsync(() async {
        final boundary = boundaryKey.currentContext!.findRenderObject()!
            as RenderRepaintBoundary;
        final image = await boundary.toImage(pixelRatio: 4);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        final out = File(
          '../design_evidence/full-page-models/${variant.key}-4x.png',
        );
        await out.parent.create(recursive: true);
        await out.writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    });
  }
}
