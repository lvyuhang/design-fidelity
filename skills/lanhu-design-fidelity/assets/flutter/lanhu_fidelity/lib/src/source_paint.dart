import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

/// Where Sketch strokes a border relative to the shape edge.
///
/// Lanhu exports the Chinese labels 内边框 / 中心边框 / 外边框.
enum SourceBorderPosition { inside, center, outside }

/// A geometric outline in the node's own layout frame.
@immutable
abstract class SourceShape {
  const SourceShape();

  /// Outline for [rect], grown outward by [grow] logical px (negative shrinks).
  ///
  /// Rect and oval shapes grow exactly. Free paths return the unmodified
  /// outline; painters emulate growth with a round-joined stroke instead, see
  /// [supportsExactGrow].
  Path path(Rect rect, {double grow = 0});

  bool get supportsExactGrow => true;

  /// Open paths cannot be inside/outside stroked; Sketch centres them.
  bool get isClosed => true;
}

/// Rectangle with per-corner radii (top-left, top-right, bottom-right,
/// bottom-left). Sketch clamps each radius to half of the shorter side.
class SourceRectShape extends SourceShape {
  const SourceRectShape({this.radii = const <double>[0, 0, 0, 0]})
      : assert(radii.length == 4),
        _uniform = null;

  const SourceRectShape.all(double radius)
      : radii = const <double>[0, 0, 0, 0],
        _uniform = radius;

  final List<double> radii;
  final double? _uniform;

  double _radius(int index, Rect rect) {
    final value = _uniform ?? radii[index];
    return math.max(0, math.min(value, rect.shortestSide / 2));
  }

  RRect rrect(Rect rect, {double grow = 0}) {
    // Radii are clamped on the source rect, then grown with the rect so that a
    // spread shadow keeps a concentric outline (CSS/Sketch behaviour).
    Radius r(int i) => Radius.circular(math.max(0, _radius(i, rect) + grow));
    return RRect.fromRectAndCorners(
      rect.inflate(grow),
      topLeft: r(0),
      topRight: r(1),
      bottomRight: r(2),
      bottomLeft: r(3),
    );
  }

  @override
  Path path(Rect rect, {double grow = 0}) =>
      Path()..addRRect(rrect(rect, grow: grow));

  @override
  bool operator ==(Object other) =>
      other is SourceRectShape &&
      other._uniform == _uniform &&
      _listEquals(other.radii, radii);

  @override
  int get hashCode => Object.hash(_uniform, Object.hashAll(radii));
}

class SourceOvalShape extends SourceShape {
  const SourceOvalShape();

  @override
  Path path(Rect rect, {double grow = 0}) =>
      Path()..addOval(rect.inflate(grow));

  @override
  bool operator ==(Object other) => other is SourceOvalShape;

  @override
  int get hashCode => (SourceOvalShape).hashCode;
}

/// One Sketch path vertex in normalised (0..1) node coordinates.
@immutable
class SourcePathPoint {
  const SourcePathPoint(this.point, {this.curveFrom, this.curveTo});

  final Offset point;

  /// Outgoing control point, when the source has `hasCurveFrom`.
  final Offset? curveFrom;

  /// Incoming control point, when the source has `hasCurveTo`.
  final Offset? curveTo;

  @override
  bool operator ==(Object other) =>
      other is SourcePathPoint &&
      other.point == point &&
      other.curveFrom == curveFrom &&
      other.curveTo == curveTo;

  @override
  int get hashCode => Object.hash(point, curveFrom, curveTo);
}

/// A complete source vector path (no screenshot tracing, no icon fonts).
class SourcePathShape extends SourceShape {
  const SourcePathShape({
    required this.points,
    this.closed = true,
    this.evenOdd = false,
  });

  final List<SourcePathPoint> points;
  final bool closed;
  final bool evenOdd;

  @override
  bool get supportsExactGrow => false;

  @override
  bool get isClosed => closed;

  @override
  Path path(Rect rect, {double grow = 0}) {
    final result = Path()
      ..fillType = evenOdd ? PathFillType.evenOdd : PathFillType.nonZero;
    if (points.isEmpty) return result;
    Offset p(Offset v) =>
        Offset(rect.left + v.dx * rect.width, rect.top + v.dy * rect.height);
    final first = p(points.first.point);
    result.moveTo(first.dx, first.dy);
    final count = closed ? points.length + 1 : points.length;
    for (var i = 1; i < count; i++) {
      final previous = points[(i - 1) % points.length];
      final current = points[i % points.length];
      final end = p(current.point);
      if (previous.curveFrom != null || current.curveTo != null) {
        final c1 = p(previous.curveFrom ?? previous.point);
        final c2 = p(current.curveTo ?? current.point);
        result.cubicTo(c1.dx, c1.dy, c2.dx, c2.dy, end.dx, end.dy);
      } else {
        result.lineTo(end.dx, end.dy);
      }
    }
    if (closed) result.close();
    return result;
  }

  @override
  bool operator ==(Object other) =>
      other is SourcePathShape &&
      other.closed == closed &&
      other.evenOdd == evenOdd &&
      _listEquals(other.points, points);

  @override
  int get hashCode => Object.hash(closed, evenOdd, Object.hashAll(points));
}

@immutable
class SourceGradientStop {
  const SourceGradientStop(this.position, this.color);

  final double position;
  final Color color;

  @override
  bool operator ==(Object other) =>
      other is SourceGradientStop &&
      other.position == position &&
      other.color == color;

  @override
  int get hashCode => Object.hash(position, color);
}

/// Linear gradient with `from`/`to` in normalised node coordinates.
@immutable
class SourceLinearGradient {
  const SourceLinearGradient({
    required this.from,
    required this.to,
    required this.stops,
  });

  final Offset from;
  final Offset to;
  final List<SourceGradientStop> stops;

  @override
  bool operator ==(Object other) =>
      other is SourceLinearGradient &&
      other.from == from &&
      other.to == to &&
      _listEquals(other.stops, stops);

  @override
  int get hashCode => Object.hash(from, to, Object.hashAll(stops));
}

/// A Sketch fill: a solid colour or a linear gradient, times `opacity`.
@immutable
class SourceFill {
  const SourceFill.color(Color this.color, {this.opacity = 1})
      : gradient = null;

  const SourceFill.linear(SourceLinearGradient this.gradient, {this.opacity = 1})
      : color = null;

  final Color? color;
  final SourceLinearGradient? gradient;
  final double opacity;

  Paint toPaint(Rect bounds) {
    final paint = Paint()..isAntiAlias = true;
    final g = gradient;
    if (g != null) {
      Offset p(Offset v) => Offset(
          bounds.left + v.dx * bounds.width, bounds.top + v.dy * bounds.height);
      paint.shader = ui.Gradient.linear(
        p(g.from),
        p(g.to),
        [for (final stop in g.stops) _scaleAlpha(stop.color, opacity)],
        [for (final stop in g.stops) stop.position],
      );
    } else {
      paint.color = _scaleAlpha(color!, opacity);
    }
    return paint;
  }

  @override
  bool operator ==(Object other) =>
      other is SourceFill &&
      other.color == color &&
      other.gradient == gradient &&
      other.opacity == opacity;

  @override
  int get hashCode => Object.hash(color, gradient, opacity);
}

@immutable
class SourceBorder {
  const SourceBorder({
    required this.thickness,
    required this.fill,
    this.position = SourceBorderPosition.center,
    this.cap = StrokeCap.butt,
    this.join = StrokeJoin.miter,
    this.dash = const <double>[],
  });

  final double thickness;
  final SourceFill fill;
  final SourceBorderPosition position;
  final StrokeCap cap;
  final StrokeJoin join;

  /// Alternating dash/gap lengths in logical px; empty means solid.
  final List<double> dash;

  @override
  bool operator ==(Object other) =>
      other is SourceBorder &&
      other.thickness == thickness &&
      other.fill == fill &&
      other.position == position &&
      other.cap == cap &&
      other.join == join &&
      _listEquals(other.dash, dash);

  @override
  int get hashCode =>
      Object.hash(thickness, fill, position, cap, join, Object.hashAll(dash));
}

/// Outer (外阴影) or inner (内阴影) shadow with Sketch blur/spread semantics.
@immutable
class SourceShadow {
  const SourceShadow({
    required this.color,
    this.offset = Offset.zero,
    this.blurRadius = 0,
    this.spread = 0,
    this.inner = false,
  });

  final Color color;
  final Offset offset;
  final double blurRadius;
  final double spread;
  final bool inner;

  @override
  bool operator ==(Object other) =>
      other is SourceShadow &&
      other.color == color &&
      other.offset == offset &&
      other.blurRadius == blurRadius &&
      other.spread == spread &&
      other.inner == inner;

  @override
  int get hashCode => Object.hash(color, offset, blurRadius, spread, inner);
}

/// Clips a child to a [SourceShape] in its own box.
class SourceShapeClipper extends CustomClipper<Path> {
  const SourceShapeClipper(this.shape);

  final SourceShape shape;

  @override
  Path getClip(Size size) => shape.path(Offset.zero & size);

  @override
  bool shouldReclip(SourceShapeClipper oldClipper) => oldClipper.shape != shape;
}

Color _scaleAlpha(Color color, double factor) =>
    factor >= 1 ? color : color.withValues(alpha: color.a * factor);

/// Applies a dash pattern along [path]; returns [path] when [dash] is empty.
Path dashPath(Path path, List<double> dash) {
  if (dash.isEmpty || dash.every((value) => value <= 0)) return path;
  final result = Path();
  for (final metric in path.computeMetrics()) {
    var distance = 0.0;
    var index = 0;
    var draw = true;
    while (distance < metric.length) {
      final length = math.max(0.0, dash[index % dash.length]);
      final next = math.min(distance + length, metric.length);
      if (draw && next > distance) {
        result.addPath(metric.extractPath(distance, next), Offset.zero);
      }
      distance = next;
      draw = !draw;
      index++;
    }
  }
  return result;
}

bool _listEquals<T>(List<T> a, List<T> b) {
  if (identical(a, b)) return true;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}
