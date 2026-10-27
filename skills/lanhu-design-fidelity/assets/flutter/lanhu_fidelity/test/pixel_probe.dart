import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/rendering.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

/// Rendered RGBA pixels of a test surface at 1 logical px = 1 pixel.
class Pixels {
  Pixels(this.width, this.height, this._bytes);

  final int width;
  final int height;
  final ByteData _bytes;

  /// Opaque backgrounds are used throughout, so premultiplication is moot.
  List<int> rgb(int x, int y) {
    final offset = (y * width + x) * 4;
    return <int>[
      _bytes.getUint8(offset),
      _bytes.getUint8(offset + 1),
      _bytes.getUint8(offset + 2),
    ];
  }

  int luma(int x, int y) {
    final c = rgb(x, y);
    return ((c[0] + c[1] + c[2]) / 3).round();
  }

  bool isWhite(int x, int y, {int tolerance = 6}) =>
      rgb(x, y).every((v) => v >= 255 - tolerance);

  bool isRed(int x, int y) {
    final c = rgb(x, y);
    return c[0] > 200 && c[1] < 70 && c[2] < 70;
  }

  bool isBlue(int x, int y) {
    final c = rgb(x, y);
    return c[2] > 200 && c[0] < 70 && c[1] < 70;
  }

  bool isBlack(int x, int y) => rgb(x, y).every((v) => v < 50);
}

/// Places [child] at (30, 30) with [childSize] on a [canvas] surface.
Widget probeSurface(
  Widget child, {
  Size canvas = const Size(100, 100),
  Size childSize = const Size(40, 40),
  Offset origin = const Offset(30, 30),
  Widget? background,
}) {
  return Stack(
    children: [
      Positioned.fill(
          child: background ?? const ColoredBox(color: Color(0xFFFFFFFF))),
      Positioned(
        left: origin.dx,
        top: origin.dy,
        width: childSize.width,
        height: childSize.height,
        child: child,
      ),
    ],
  );
}

Future<Pixels> renderPixels(
  WidgetTester tester,
  Widget surface, {
  Size canvas = const Size(100, 100),
}) async {
  final key = GlobalKey();
  await tester.pumpWidget(
    Directionality(
      textDirection: TextDirection.ltr,
      child: Align(
        alignment: Alignment.topLeft,
        child: RepaintBoundary(
          key: key,
          child: SizedBox.fromSize(size: canvas, child: surface),
        ),
      ),
    ),
  );
  await tester.pump();
  final boundary = tester.renderObject<RenderRepaintBoundary>(find.byKey(key));
  final pixels = await tester.runAsync(() async {
    final image = await boundary.toImage(pixelRatio: 1);
    try {
      final data = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
      return Pixels(image.width, image.height, data!);
    } finally {
      image.dispose();
    }
  });
  return pixels!;
}
