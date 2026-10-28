import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'effects.dart';
import 'source_paint.dart';

/// Sketch background blur (`blurType: 3`, 背景模糊) clipped to the layer shape.
///
/// Blurs what is painted *behind* this widget; put the layer's own
/// translucent fill in [child] (usually a [SourceBox]). A foreground blur or a
/// BoxShadow cannot substitute for this effect.
class SourceBackdropBlur extends StatelessWidget {
  const SourceBackdropBlur({
    super.key,
    required this.radius,
    this.shape = const SourceRectShape(),
    this.saturation = 1,
    required this.child,
  });

  final double radius;
  final SourceShape shape;

  /// Sketch background-blur saturation; 1 leaves colours unchanged.
  final double saturation;
  final Widget child;

  ui.ImageFilter get filter {
    final sigma = FidelityEffectMapping.backgroundBlurSigma(radius);
    final blur = ui.ImageFilter.blur(
        sigmaX: sigma, sigmaY: sigma, tileMode: TileMode.clamp);
    if ((saturation - 1).abs() < 1e-6) return blur;
    return ui.ImageFilter.compose(
        outer: ui.ColorFilter.matrix(saturationMatrix(saturation)),
        inner: blur);
  }

  @override
  Widget build(BuildContext context) => ClipPath(
        clipper: SourceShapeClipper(shape),
        child: BackdropFilter(filter: filter, child: child),
      );
}

/// Sketch Gaussian layer blur (`blurType: 0`, 高斯模糊) of the layer itself.
class SourceLayerBlur extends StatelessWidget {
  const SourceLayerBlur({super.key, required this.radius, required this.child});

  final double radius;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final sigma = FidelityEffectMapping.layerBlurSigma(radius);
    if (sigma <= 0) return child;
    return ImageFiltered(
      imageFilter: ui.ImageFilter.blur(
          sigmaX: sigma, sigmaY: sigma, tileMode: TileMode.decal),
      child: child,
    );
  }
}

/// Standard luminance-preserving saturation matrix (Rec. 709 weights).
List<double> saturationMatrix(double s) {
  const r = 0.2126, g = 0.7152, b = 0.0722;
  return <double>[
    r + (1 - r) * s, g - g * s, b - b * s, 0, 0, //
    r - r * s, g + (1 - g) * s, b - b * s, 0, 0, //
    r - r * s, g - g * s, b + (1 - b) * s, 0, 0, //
    0, 0, 0, 1, 0,
  ];
}
