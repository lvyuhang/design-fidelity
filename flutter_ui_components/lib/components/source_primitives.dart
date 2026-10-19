import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'source_specs.g.dart';

Map<String, dynamic> sourceNode(String category, String id) =>
    Map<String, dynamic>.from(sourceSpecs[category]![id]!);
Rect sourceFrame(Map<String, dynamic> node) {
  final v = (node['frame'] as List).cast<num>();
  return Rect.fromLTWH(
      v[0].toDouble(), v[1].toDouble(), v[2].toDouble(), v[3].toDouble());
}

Color sourceColor(Map c, [double opacity = 1]) => Color.fromRGBO(
    (c['r'] as num).round(),
    (c['g'] as num).round(),
    (c['b'] as num).round(),
    (c['a'] as num).toDouble() * opacity);

/// Source absolute coordinates are confined to the component's local coordinate space.
Widget sourceLayer(String category, String id, Offset origin,
    {String? text,
    bool wrap = false,
    VoidCallback? onTap,
    String? actionLabel}) {
  final n = sourceNode(category, id), f = sourceFrame(sourceNode(category, id));
  Widget child = n.containsKey('text')
      ? Text.rich(
          TextSpan(children: [
            if (text == null && n['runs'] is List)
              for (final run in n['runs'] as List)
                TextSpan(
                    text: run['text'],
                    style: TextStyle(color: sourceColor(run['color'])))
            else
              TextSpan(text: text ?? n['text'] as String),
          ]),
          softWrap: wrap,
          overflow: TextOverflow.visible,
          textScaler: TextScaler.noScaling,
          // Sketch stores NSTextAlignment: 2 = center, not right.
          textAlign: switch (n['align']) {
            1 => TextAlign.right,
            2 => TextAlign.center,
            _ => TextAlign.left
          },
          style: TextStyle(
              inherit: false,
              decoration: TextDecoration.none,
              fontFamily: 'SourcePingFang',
              fontSize: (n['fontSize'] as num).toDouble(),
              fontWeight: switch (n['weight']) {
                600 => FontWeight.w600,
                500 => FontWeight.w500,
                _ => FontWeight.w400
              },
              height: (n['lineHeight'] as num) / (n['fontSize'] as num),
              leadingDistribution: TextLeadingDistribution.even,
              letterSpacing: 0,
              color: sourceColor(n['color'] as Map)))
      : CustomPaint(painter: SourceShapePainter(n));
  if (n['flipX'] == true || n['flipY'] == true) {
    child = Transform.flip(
        flipX: n['flipX'] == true, flipY: n['flipY'] == true, child: child);
  }
  if (onTap != null) {
    child = Semantics(
        button: true,
        label: actionLabel,
        child: MouseRegion(
            cursor: SystemMouseCursors.click,
            child: GestureDetector(
                key: ValueKey(actionLabel),
                behavior: HitTestBehavior.opaque,
                onTap: onTap,
                child: child)));
  }
  return Positioned(
      left: f.left - origin.dx,
      top: f.top - origin.dy,
      width: f.width,
      height: f.height,
      child: child);
}

/// Native paths, gradients, inside borders and knocked-out outer shadows.
class SourceShapePainter extends CustomPainter {
  const SourceShapePainter(this.spec);
  final Map<String, dynamic> spec;
  Path path(Size size) {
    final radii = spec['radius'] as List?;
    if (radii != null && radii.isNotEmpty) {
      double r(int i) =>
          (radii.length == 1 ? radii[0] : radii[i] as num).toDouble();
      return Path()
        ..addRRect(RRect.fromRectAndCorners(Offset.zero & size,
            topLeft: Radius.circular(r(0)),
            topRight: Radius.circular(r(1)),
            bottomRight: Radius.circular(r(2)),
            bottomLeft: Radius.circular(r(3))));
    }
    final points = spec['points'] as List?;
    if (points == null || points.isEmpty)
      throw StateError('Missing source path: ${spec['sourceId']}');
    Offset p(Map v) =>
        Offset((v['x'] as num) * size.width, (v['y'] as num) * size.height);
    final result = Path()
      ..moveTo(p(points[0]['point']).dx, p(points[0]['point']).dy);
    final count = spec['isClosed'] == true ? points.length + 1 : points.length;
    for (var i = 1; i < count; i++) {
      final previous = points[(i - 1) % points.length],
          current = points[i % points.length];
      final end = p(current['point']);
      if (previous['hasCurveFrom'] == true || current['hasCurveTo'] == true) {
        final c1 = p(
            previous[previous['hasCurveFrom'] == true ? 'curveFrom' : 'point']);
        final c2 =
            p(current[current['hasCurveTo'] == true ? 'curveTo' : 'point']);
        result.cubicTo(c1.dx, c1.dy, c2.dx, c2.dy, end.dx, end.dy);
      } else {
        result.lineTo(end.dx, end.dy);
      }
    }
    if (spec['isClosed'] == true) result.close();
    return result;
  }

  Paint _paint(Map fill, Size size, double opacity) {
    final paint = Paint();
    final amount = (fill['opacity'] as num? ?? 1).toDouble() * opacity;
    if (fill['gradient'] case final Map gradient) {
      Offset p(Map v) =>
          Offset((v['x'] as num) * size.width, (v['y'] as num) * size.height);
      final stops = gradient['colorStops'] as List;
      paint.shader = ui.Gradient.linear(
          p(gradient['from']),
          p(gradient['to']),
          [for (final s in stops) sourceColor(s['color'], amount)],
          [for (final s in stops) (s['position'] as num).toDouble()]);
    } else {
      paint.color = sourceColor(fill['color'], amount);
    }
    return paint;
  }

  @override
  void paint(Canvas canvas, Size size) {
    final shape = path(size);
    final opacity = (spec['opacity'] as num? ?? 100) / 100;
    for (final shadow in spec['shadow'] as List? ?? []) {
      if (shadow['isEnabled'] != true) continue;
      canvas.save();
      canvas.clipPath(Path()
        ..fillType = PathFillType.evenOdd
        ..addRect((Offset.zero & size).inflate(150))
        ..addPath(shape, Offset.zero));
      final blur = (shadow['blurRadius'] as num).toDouble();
      canvas.drawPath(
          shape.shift(Offset((shadow['offsetX'] as num).toDouble(),
              (shadow['offsetY'] as num).toDouble())),
          Paint()
            ..color = sourceColor(shadow['color'], opacity)
            ..maskFilter =
                MaskFilter.blur(BlurStyle.normal, blur * .57735 + .5));
      canvas.restore();
    }
    for (final fill in spec['fills'] as List? ?? []) {
      if (fill['isEnabled'] == true)
        canvas.drawPath(shape, _paint(fill, size, opacity));
    }
    for (final border in spec['borders'] as List? ?? []) {
      if (border['isEnabled'] != true) continue;
      final inside = border['position'] == '内边框';
      final options = spec['borderOptions'] as Map? ?? {};
      final paint = _paint(border, size, opacity)
        ..style = PaintingStyle.stroke
        ..strokeWidth =
            (border['thickness'] as num).toDouble() * (inside ? 2 : 1)
        ..strokeCap = switch (options['lineCapStyle']) {
          1 => StrokeCap.round,
          2 => StrokeCap.square,
          _ => StrokeCap.butt
        }
        ..strokeJoin = switch (options['lineJoinStyle']) {
          1 => StrokeJoin.round,
          2 => StrokeJoin.bevel,
          _ => StrokeJoin.miter
        };
      canvas.save();
      if (inside) canvas.clipPath(shape);
      canvas.drawPath(shape, paint);
      canvas.restore();
    }
  }

  @override
  bool shouldRepaint(SourceShapePainter oldDelegate) =>
      oldDelegate.spec != spec;
}
