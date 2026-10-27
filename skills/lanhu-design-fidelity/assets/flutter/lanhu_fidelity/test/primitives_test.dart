// Behaviour tests for every primitive: each mechanism has a positive case and
// a counter-example proving the assertion would fail without the mechanism.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lanhu_fidelity/lanhu_fidelity.dart';

import 'pixel_probe.dart';

const _red = Color(0xFFFF0000);
const _blue = Color(0xFF0000FF);
const _black = Color(0xFF000000);
const _white = Color(0xFFFFFFFF);

SourceBox _bordered(SourceBorderPosition position, {List<double> dash = const []}) =>
    SourceBox(
      fills: const [SourceFill.color(_blue)],
      borders: [
        SourceBorder(
          thickness: 4,
          fill: const SourceFill.color(_red),
          position: position,
          dash: dash,
        ),
      ],
    );

void main() {
  group('effect mapping', () {
    test('one shadow/blur conversion for every page', () {
      expect(LanhuEffectMapping.shadowSigma(10), 5);
      expect(LanhuEffectMapping.shadowSigma(0), 0);
      expect(LanhuEffectMapping.layerBlurSigma(9.54), closeTo(4.77, 1e-9));
      expect(LanhuEffectMapping.backgroundBlurSigma(-1), 0);
    });
  });

  group('border position (box spans x 30..70)', () {
    testWidgets('inside border stays within the fill frame', (tester) async {
      final px = await renderPixels(
          tester, probeSurface(_bordered(SourceBorderPosition.inside)));
      expect(px.isWhite(28, 50), isTrue, reason: 'nothing outside the frame');
      expect(px.isRed(32, 50), isTrue, reason: 'band 30..34');
      expect(px.isBlue(36, 50), isTrue);
    });

    testWidgets('center border straddles the edge', (tester) async {
      final px = await renderPixels(
          tester, probeSurface(_bordered(SourceBorderPosition.center)));
      expect(px.isWhite(26, 50), isTrue);
      expect(px.isRed(29, 50), isTrue, reason: 'band 28..32');
      expect(px.isRed(31, 50), isTrue);
      expect(px.isBlue(34, 50), isTrue);
      // Counter-example for the inside test: x=28 is painted here.
      expect(px.isWhite(28, 50), isFalse);
    });

    testWidgets('outside border keeps the full fill', (tester) async {
      final px = await renderPixels(
          tester, probeSurface(_bordered(SourceBorderPosition.outside)));
      expect(px.isWhite(24, 50), isTrue);
      expect(px.isRed(28, 50), isTrue, reason: 'band 26..30');
      expect(px.isBlue(31, 50), isTrue, reason: 'fill not shrunk');
      expect(px.isRed(32, 50), isFalse);
    });

    testWidgets('dash pattern breaks the stroke', (tester) async {
      final px = await renderPixels(tester,
          probeSurface(_bordered(SourceBorderPosition.outside, dash: [4, 4])));
      var transitions = 0;
      var previous = px.isRed(31, 28);
      for (var x = 32; x < 70; x++) {
        final current = px.isRed(x, 28);
        if (current != previous) transitions++;
        previous = current;
      }
      expect(transitions, greaterThanOrEqualTo(4));
    });
  });

  group('outer shadow', () {
    const translucent = Color(0x80FFFFFF);
    const shadow = SourceShadow(color: Color(0x80000000), blurRadius: 10);

    testWidgets('is knocked out under a translucent fill', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          fills: [SourceFill.color(translucent)],
          shadows: [shadow],
        )),
      );
      expect(px.isWhite(50, 50, tolerance: 1), isTrue,
          reason: 'shadow must not tint the interior');
      expect(px.luma(28, 50), lessThan(245), reason: 'shadow right outside');
      expect(px.isWhite(8, 50, tolerance: 3), isTrue,
          reason: 'fades within ~3 sigma');
    });

    testWidgets('counter-example: Flutter BoxShadow tints the interior',
        (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const DecoratedBox(
          decoration: BoxDecoration(
            color: translucent,
            boxShadow: [BoxShadow(color: Color(0x80000000), blurRadius: 10)],
          ),
        )),
      );
      expect(px.isWhite(50, 50, tolerance: 1), isFalse);
    });

    testWidgets('spread grows the casting outline', (tester) async {
      Future<Pixels> render(double spread) => renderPixels(
            tester,
            probeSurface(SourceBox(
              fills: const [SourceFill.color(_white)],
              shadows: [SourceShadow(color: _black, spread: spread)],
            )),
          );
      final withSpread = await render(4);
      expect(withSpread.isBlack(28, 50), isTrue, reason: 'band 26..30');
      expect(withSpread.isWhite(24, 50), isTrue);
      final without = await render(0);
      expect(without.isWhite(28, 50), isTrue);
    });

    testWidgets('offset moves the shadow', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          fills: [SourceFill.color(_white)],
          shadows: [SourceShadow(color: _black, offset: Offset(0, 6))],
        )),
      );
      expect(px.isBlack(50, 73), isTrue, reason: 'below: 70..76');
      expect(px.isWhite(50, 27), isTrue, reason: 'nothing above');
    });

    testWidgets('works for free paths with spread', (tester) async {
      const triangle = SourcePathShape(points: [
        SourcePathPoint(Offset(0, 1)),
        SourcePathPoint(Offset(0.5, 0)),
        SourcePathPoint(Offset(1, 1)),
      ]);
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          shape: triangle,
          fills: [SourceFill.color(_white)],
          shadows: [SourceShadow(color: _black, spread: 3)],
        )),
      );
      expect(px.isBlack(50, 72), isTrue, reason: 'below the base');
      expect(px.isWhite(50, 60), isTrue, reason: 'interior knocked out');
    });
  });

  group('inner shadow', () {
    testWidgets('offset inner shadow darkens the top band only', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          fills: [SourceFill.color(_white)],
          shadows: [
            SourceShadow(color: _black, offset: Offset(0, 4), inner: true),
          ],
        )),
      );
      expect(px.isBlack(50, 32), isTrue);
      expect(px.isWhite(50, 50), isTrue);
      expect(px.isWhite(50, 28), isTrue, reason: 'never outside the shape');
    });

    testWidgets('spread inner shadow forms a ring', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          fills: [SourceFill.color(_white)],
          shadows: [SourceShadow(color: _black, spread: 3, inner: true)],
        )),
      );
      expect(px.isBlack(31, 50), isTrue);
      expect(px.isBlack(68, 50), isTrue);
      expect(px.isWhite(50, 50), isTrue);
    });
  });

  group('fills and layer opacity', () {
    testWidgets('linear gradient follows normalised from/to', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(fills: [
          SourceFill.linear(SourceLinearGradient(
            from: Offset(0, 0.5),
            to: Offset(1, 0.5),
            stops: [SourceGradientStop(0, _red), SourceGradientStop(1, _blue)],
          )),
        ])),
      );
      expect(px.rgb(31, 50)[0], greaterThan(200));
      expect(px.rgb(69, 50)[2], greaterThan(200));
    });

    testWidgets('layer opacity composites fill and border once',
        (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          opacity: 0.5,
          fills: [SourceFill.color(_black)],
          borders: [
            SourceBorder(thickness: 4, fill: SourceFill.color(_black)),
          ],
        )),
      );
      final interior = px.luma(50, 50);
      final overlap = px.luma(31, 50);
      expect(interior, inInclusiveRange(120, 135));
      expect((overlap - interior).abs(), lessThanOrEqualTo(3),
          reason: 'per-paint opacity would darken the overlap to ~64');
    });

    testWidgets('radius is clamped to half the shorter side', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourceBox(
          shape: SourceRectShape.all(100),
          fills: [SourceFill.color(_black)],
        )),
      );
      expect(px.isWhite(31, 31), isTrue, reason: 'corner cut like a circle');
      expect(px.isBlack(50, 31), isTrue);
    });
  });

  group('text metrics', () {
    final style = sourceTextStyle(
      fontFamily: 'FlutterTest',
      fontSize: 12,
      lineHeight: 24,
      color: _black,
    );

    testWidgets('line box equals the source line height', (tester) async {
      await tester.pumpWidget(Directionality(
        textDirection: TextDirection.ltr,
        child: Center(child: SourceText('Line', style: style)),
      ));
      expect(tester.getSize(find.byType(SourceText)).height, 24);
    });

    testWidgets('mixed runs keep the forced strut', (tester) async {
      await tester.pumpWidget(Directionality(
        textDirection: TextDirection.ltr,
        child: Center(
          child: SourceText.rich([
            SourceTextRun('a', style),
            SourceTextRun('B', style.copyWith(fontSize: 20)),
          ], style: style),
        ),
      ));
      expect(tester.getSize(find.byType(SourceText)).height, 24);
    });

    testWidgets('ambient text styles do not leak', (tester) async {
      Future<Size> measure(Widget ambient) async {
        await tester.pumpWidget(Directionality(
          textDirection: TextDirection.ltr,
          child: Center(child: ambient),
        ));
        return tester.getSize(find.byType(SourceText));
      }

      final plain = await measure(SourceText('Leak', style: style));
      final themed = await measure(DefaultTextStyle(
        style: const TextStyle(letterSpacing: 10, fontSize: 40, height: 3),
        child: SourceText('Leak', style: style),
      ));
      expect(themed, plain);
    });
  });

  group('assets and placeholders', () {
    testWidgets('asset is placed by its export frame, not squeezed',
        (tester) async {
      await tester.pumpWidget(Directionality(
        textDirection: TextDirection.ltr,
        child: probeSurface(
          const SourceAsset(
            'test/assets/frame.png',
            exportRect: Rect.fromLTWH(-2, -3, 44, 46),
          ),
        ),
      ));
      expect(tester.getRect(find.byType(Image)),
          const Rect.fromLTWH(28, 27, 44, 46));
    });

    testWidgets('circle placeholder keeps the source outline', (tester) async {
      final px = await renderPixels(
        tester,
        probeSurface(const SourcePlaceholder(
          nodeId: 'N1',
          shape: SourcePlaceholderShape.circle,
        )),
      );
      expect(px.isWhite(31, 31), isTrue);
      expect(px.rgb(50, 36), SourcePlaceholder.fillColor.toRgbList());
    });
  });

  group('blur', () {
    Widget stripes() => CustomPaint(painter: _StripePainter());

    testWidgets('background blur smooths only inside its clip',
        (tester) async {
      Future<Pixels> render(double radius) => renderPixels(
            tester,
            probeSurface(
              SourceBackdropBlur(
                radius: radius,
                child: const SizedBox.expand(),
              ),
              background: stripes(),
            ),
          );
      final blurred = await render(10);
      expect((blurred.luma(50, 50) - blurred.luma(51, 50)).abs(),
          lessThan(40));
      expect((blurred.luma(10, 50) - blurred.luma(11, 50)).abs(),
          greaterThan(200), reason: 'outside the clip is untouched');
      final sharp = await render(0);
      expect((sharp.luma(50, 50) - sharp.luma(51, 50)).abs(),
          greaterThan(200), reason: 'counter-example without blur');
    });

    test('saturation matrix is identity at 1', () {
      final m = saturationMatrix(1);
      expect(m.sublist(0, 3), [closeTo(1, 1e-9), closeTo(0, 1e-9), closeTo(0, 1e-9)]);
      expect(m[18], 1);
    });
  });

  group('platform fonts', () {
    tearDown(() {
      debugDefaultTargetPlatformOverride = null;
      SourceFonts.useDesignFonts = false;
    });

    test('each platform resolves its production family', () {
      String? resolve(TargetPlatform platform) {
        debugDefaultTargetPlatformOverride = platform;
        return sourceFontFamily('SourcePingFang',
            ios: SourceFonts.system, android: 'NotoSansSC');
      }

      expect(resolve(TargetPlatform.iOS), isNull, reason: 'iOS system font');
      expect(resolve(TargetPlatform.android), 'NotoSansSC');
      expect(resolve(TargetPlatform.windows), 'SourcePingFang');
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      expect(sourceFontFamily('SourcePingFang'), 'SourcePingFang',
          reason: 'unmapped platforms keep the design family');
    });

    test('fidelity renders always use the design family', () {
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      SourceFonts.useDesignFonts = true;
      expect(sourceFontFamily('SourcePingFang', ios: SourceFonts.system),
          'SourcePingFang');
    });
  });

  group('structure', () {
    testWidgets('source keys expose node geometry', (tester) async {
      await tester.pumpWidget(Directionality(
        textDirection: TextDirection.ltr,
        child: probeSurface(
          SourceNode(nodeId: 'ABC', child: const SizedBox.expand()),
        ),
      ));
      expect(tester.getRect(find.byKey(sourceKey('ABC'))),
          const Rect.fromLTWH(30, 30, 40, 40));
      expect(sourceNodeIdOf(sourceKey('ABC')), 'ABC');
      expect(sourceNodeIdOf(const ValueKey('other')), isNull);
    });

    testWidgets('system chrome reserves source height without painting',
        (tester) async {
      await tester.pumpWidget(const Directionality(
        textDirection: TextDirection.ltr,
        child: MediaQuery(
          data: MediaQueryData(),
          child: Align(
            alignment: Alignment.topLeft,
            child: SystemChromeSlot(
                kind: SystemChromeKind.statusBar, sourceHeight: 44),
          ),
        ),
      ));
      expect(tester.getSize(find.byType(SystemChromeSlot)).height, 44);
      await tester.pumpWidget(const Directionality(
        textDirection: TextDirection.ltr,
        child: MediaQuery(
          data: MediaQueryData(padding: EdgeInsets.only(top: 30)),
          child: Align(
            alignment: Alignment.topLeft,
            child: SystemChromeSlot(
                kind: SystemChromeKind.statusBar, sourceHeight: 44),
          ),
        ),
      ));
      expect(tester.getSize(find.byType(SystemChromeSlot)).height, 30);
    });
  });
}

class _StripePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = _white);
    final black = Paint()..color = _black;
    for (var x = 0.0; x < size.width; x += 2) {
      canvas.drawRect(Rect.fromLTWH(x, 0, 1, size.height), black);
    }
  }

  @override
  bool shouldRepaint(_StripePainter oldDelegate) => false;
}

extension on Color {
  List<int> toRgbList() => <int>[
        (r * 255).round(),
        (g * 255).round(),
        (b * 255).round(),
      ];
}
