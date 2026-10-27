import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'effects.dart';
import 'source_paint.dart';

/// A Sketch shape layer: outer shadows, fills, inner shadows, borders.
///
/// Semantics that hand-written pages repeatedly got wrong are fixed here:
/// * inside / center / outside borders keep the fill geometry unchanged;
/// * outer shadows are knocked out under the shape, so a translucent fill is
///   not tinted by its own shadow (CSS/Sketch behaviour, unlike BoxShadow);
/// * shadow spread grows the casting outline before blurring;
/// * layer opacity applies to the composited layer, not per paint.
///
/// [child] is laid out in the same box. Set [clipChild] to clip it to the
/// shape (e.g. a photo inside a rounded card).
class SourceBox extends StatelessWidget {
  const SourceBox({
    super.key,
    this.shape = const SourceRectShape(),
    this.fills = const <SourceFill>[],
    this.borders = const <SourceBorder>[],
    this.shadows = const <SourceShadow>[],
    this.opacity = 1,
    this.clipChild = false,
    this.child,
  }) : assert(opacity >= 0 && opacity <= 1);

  final SourceShape shape;
  final List<SourceFill> fills;
  final List<SourceBorder> borders;
  final List<SourceShadow> shadows;
  final double opacity;
  final bool clipChild;
  final Widget? child;

  @override
  Widget build(BuildContext context) {
    Widget? content = child;
    if (content != null && clipChild) {
      content = ClipPath(clipper: SourceShapeClipper(shape), child: content);
    }
    return CustomPaint(
      painter: SourceBoxPainter(
        shape: shape,
        fills: fills,
        borders: borders,
        shadows: shadows,
        opacity: opacity,
      ),
      child: content ?? const SizedBox.expand(),
    );
  }
}

class SourceBoxPainter extends CustomPainter {
  const SourceBoxPainter({
    required this.shape,
    this.fills = const <SourceFill>[],
    this.borders = const <SourceBorder>[],
    this.shadows = const <SourceShadow>[],
    this.opacity = 1,
  });

  final SourceShape shape;
  final List<SourceFill> fills;
  final List<SourceBorder> borders;
  final List<SourceShadow> shadows;
  final double opacity;

  /// Margin that contains every shadow and outside border of this layer.
  double get paintExtent {
    var extent = 0.0;
    for (final shadow in shadows) {
      if (shadow.inner) continue;
      extent = math.max(
          extent,
          LanhuEffectMapping.shadowExtent(shadow.blurRadius, shadow.spread) +
              math.max(shadow.offset.dx.abs(), shadow.offset.dy.abs()));
    }
    for (final border in borders) {
      extent = math.max(extent, border.thickness);
    }
    return extent + 2;
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (opacity <= 0) return;
    final rect = Offset.zero & size;
    final outline = shape.path(rect);
    final layerBounds = rect.inflate(paintExtent);
    final grouped = opacity < 1;
    if (grouped) {
      canvas.saveLayer(
          layerBounds, Paint()..color = Color.fromRGBO(0, 0, 0, opacity));
    }
    for (final shadow in shadows) {
      if (!shadow.inner) _paintOuterShadow(canvas, rect, outline, shadow);
    }
    for (final fill in fills) {
      canvas.drawPath(outline, fill.toPaint(rect));
    }
    for (final shadow in shadows) {
      if (shadow.inner) _paintInnerShadow(canvas, rect, outline, shadow);
    }
    for (final border in borders) {
      _paintBorder(canvas, rect, outline, border);
    }
    if (grouped) canvas.restore();
  }

  void _paintOuterShadow(
      Canvas canvas, Rect rect, Path outline, SourceShadow shadow) {
    final extent =
        LanhuEffectMapping.shadowExtent(shadow.blurRadius, shadow.spread) +
            shadow.offset.distance +
            2;
    final bounds = rect.inflate(extent);
    canvas.save();
    // Knock out the shape interior: the shadow only exists outside the shape.
    canvas.clipPath(Path()
      ..fillType = PathFillType.evenOdd
      ..addRect(bounds)
      ..addPath(outline, Offset.zero));
    _beginEffectLayer(canvas, bounds, shadow.color, shadow.blurRadius);
    final solid = Paint()..color = _opaque(shadow.color);
    _drawGrown(canvas, rect.shift(shadow.offset), shadow.spread, solid);
    canvas.restore(); // effect layer
    canvas.restore(); // clip
  }

  void _paintInnerShadow(
      Canvas canvas, Rect rect, Path outline, SourceShadow shadow) {
    final extent =
        LanhuEffectMapping.shadowExtent(shadow.blurRadius, shadow.spread) +
            shadow.offset.distance +
            2;
    final bounds = rect.inflate(extent);
    canvas.save();
    canvas.clipPath(outline);
    _beginEffectLayer(canvas, bounds, shadow.color, shadow.blurRadius);
    final solid = Paint()..color = _opaque(shadow.color);
    canvas.drawRect(bounds, solid);
    // Cut the (offset, shrunk-by-spread) shape out of the solid surround.
    final cleared = Paint()..blendMode = BlendMode.clear;
    final hole = rect.shift(shadow.offset);
    if (shape.supportsExactGrow) {
      canvas.drawPath(shape.path(hole, grow: -shadow.spread), cleared);
    } else {
      canvas.drawPath(shape.path(hole), cleared);
      if (shadow.spread > 0) {
        canvas.drawPath(shape.path(hole), _stroke(solid, shadow.spread * 2));
      }
    }
    canvas.restore(); // effect layer
    canvas.restore(); // clip
  }

  void _paintBorder(
      Canvas canvas, Rect rect, Path outline, SourceBorder border) {
    if (border.thickness <= 0) return;
    final position =
        shape.isClosed ? border.position : SourceBorderPosition.center;
    final width = position == SourceBorderPosition.center
        ? border.thickness
        : border.thickness * 2;
    final paint = border.fill.toPaint(rect)
      ..style = PaintingStyle.stroke
      ..strokeWidth = width
      ..strokeCap = border.cap
      ..strokeJoin = border.join;
    canvas.save();
    switch (position) {
      case SourceBorderPosition.inside:
        canvas.clipPath(outline);
      case SourceBorderPosition.outside:
        canvas.clipPath(Path()
          ..fillType = PathFillType.evenOdd
          ..addRect(rect.inflate(border.thickness * 2 + 2))
          ..addPath(outline, Offset.zero));
      case SourceBorderPosition.center:
        break;
    }
    canvas.drawPath(dashPath(outline, border.dash), paint);
    canvas.restore();
  }

  /// Draws the shape on [rect] grown by [grow] with an opaque paint.
  void _drawGrown(Canvas canvas, Rect rect, double grow, Paint solid) {
    if (shape.supportsExactGrow || grow == 0) {
      canvas.drawPath(shape.path(rect, grow: grow), solid);
      return;
    }
    final path = shape.path(rect);
    canvas.drawPath(path, solid);
    if (grow > 0) canvas.drawPath(path, _stroke(solid, grow * 2));
    // Negative spread on free paths is not representable without path
    // offsetting; the generator reports it as an unsupported effect.
  }

  /// Opens a layer that blurs and applies the effect colour's alpha once, so
  /// overlapping solid draws inside it never double-blend.
  void _beginEffectLayer(
      Canvas canvas, Rect bounds, Color color, double blurRadius) {
    final sigma = LanhuEffectMapping.shadowSigma(blurRadius);
    final layer = Paint()..color = Color.fromRGBO(0, 0, 0, color.a);
    if (sigma > 0) {
      layer.imageFilter = ui.ImageFilter.blur(
          sigmaX: sigma, sigmaY: sigma, tileMode: TileMode.decal);
    }
    canvas.saveLayer(bounds, layer);
  }

  static Color _opaque(Color color) => color.withValues(alpha: 1);

  static Paint _stroke(Paint base, double width) => Paint()
    ..color = base.color
    ..style = PaintingStyle.stroke
    ..strokeWidth = width
    ..strokeJoin = StrokeJoin.round
    ..strokeCap = StrokeCap.round;

  @override
  bool shouldRepaint(SourceBoxPainter oldDelegate) =>
      oldDelegate.shape != shape ||
      oldDelegate.opacity != opacity ||
      !_same(oldDelegate.fills, fills) ||
      !_same(oldDelegate.borders, borders) ||
      !_same(oldDelegate.shadows, shadows);

  static bool _same<T>(List<T> a, List<T> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }
}
