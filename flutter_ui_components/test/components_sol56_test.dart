import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/components/expanded_components.dart';
import 'package:juxing_components/components/login_components.dart';
import 'package:juxing_components/components/social_components.dart';
import 'package:juxing_components/experiments/login_sol56.dart';
import 'package:juxing_components/experiments/social_sol56.dart';
import 'package:juxing_components/experiments/utility_sol56.dart';

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

  const sizes = <String, Size>{
    'feed': Size(375, 342),
    'comments': Size(375, 374),
    'modal': Size(375, 280),
    'nav': Size(375, 98),
    'appeal': Size(375, 125),
    'login': Size(375, 395),
  };

  const imageAssets = <String>[
    'assets/fixtures/comment-avatar.png',
    'assets/fixtures/feed-avatar.png',
    'assets/fixtures/feed-photo.png',
    'assets/fixtures/reply-avatar.png',
    'assets/lanhu/appeal/assets/3c01e52ce3c5fd7658e2bb85964bf19046d219e3f4f0a6e2e1562aefded0f5b4.png',
    'assets/lanhu/nav/assets/a8071fdef24e364d65fb5159f6ac36f47d869667d188aca77e99a1fa52207622.png',
    'assets/lanhu/assets/05d568660f8b15118112812d36654cc19a41abfa447fcaf5aa60ea9eba71a8db.png',
    'assets/lanhu/assets/6ae1b2c8ae7ea66059d0dc46e6197f7ea99ea82ac2cddc0c66beb254b8d1798d.png',
    'assets/lanhu/assets/9b1e35de0078f86a5139ce45acbb9fae30e8548c2fa8029fb8116dce58924a87.png',
    'assets/lanhu/assets/9d0654e6ecfa4fe81881a272ab3990f51329b81d32eaecc985c37e6084f234c8.png',
    'assets/lanhu/assets/aa419996555f658c1ee97725d7f9fa542e2992af291636eff79e96e9dfa5855d.png',
  ];

  final variants = <String, Map<String, Widget>>{
    'feed': {
      'sol56': const Sol56FeedComponentStage(),
      'gpt6': const FeedComponentStage(),
    },
    'comments': {
      'sol56': const Sol56CommentPanel(),
      'gpt6': const CommentPanel(),
    },
    'modal': {
      'sol56': const Sol56ModalComponentStage(),
      'gpt6': const ModalComponentStage(),
    },
    'nav': {
      'sol56': const Sol56NavigationComponentStage(),
      'gpt6': const NavigationComponentStage(),
    },
    'appeal': {
      'sol56': const Sol56AppealComponentStage(),
      'gpt6': const AppealComponentStage(),
    },
    'login': {
      'sol56': const Sol56LoginComponentStage(),
      'gpt6': const LoginComponentStage(),
    },
  };

  for (final sample in variants.entries) {
    for (final variant in sample.value.entries) {
      testWidgets('first render ${sample.key} ${variant.key} at source 4x',
          (tester) async {
        final boundaryKey = GlobalKey();
        await tester.pumpWidget(MaterialApp(
          debugShowCheckedModeBanner: false,
          home: Center(
            child: RepaintBoundary(key: boundaryKey, child: variant.value),
          ),
        ));
        await tester.runAsync(() async {
          for (final asset in imageAssets) {
            await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
          }
        });
        await tester.pumpAndSettle();
        expect(
          tester.getSize(find.byKey(boundaryKey)),
          sizes[sample.key],
        );
        expect(tester.takeException(), isNull);

        await tester.runAsync(() async {
          final boundary = boundaryKey.currentContext!.findRenderObject()!
              as RenderRepaintBoundary;
          final image = await boundary.toImage(pixelRatio: 4);
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          final out = File(
            '../design_evidence/components-sol56/${sample.key}-${variant.key}-4x.png',
          );
          await out.parent.create(recursive: true);
          await out.writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
      });
    }
  }
}
