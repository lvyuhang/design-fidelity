/// The single place where Sketch/Lanhu effect radii become Flutter sigmas.
///
/// Before this package, pages used `r * 0.57735 + 0.5`, `r / 2` and hard-coded
/// sigmas for the same source field. Keep every conversion here; if a renderer
/// calibration proves a different factor, change it once and re-run the
/// package tests plus the affected page gates.
class FidelityEffectMapping {
  const FidelityEffectMapping._();

  /// Sketch shadow `blurRadius` follows CSS `box-shadow` blur semantics, whose
  /// Gaussian standard deviation is half of the blur value.
  static const double shadowSigmaPerRadius = 0.5;

  /// Sketch Gaussian layer blur (`blurType: 0`, 高斯模糊). Calibrated against the
  /// project's gender-selection reference (radius 9.54 -> sigma 4.77).
  static const double layerBlurSigmaPerRadius = 0.5;

  /// Sketch background blur (`blurType: 3`, 背景模糊).
  static const double backgroundBlurSigmaPerRadius = 0.5;

  static double shadowSigma(double blurRadius) =>
      blurRadius <= 0 ? 0 : blurRadius * shadowSigmaPerRadius;

  static double layerBlurSigma(double radius) =>
      radius <= 0 ? 0 : radius * layerBlurSigmaPerRadius;

  static double backgroundBlurSigma(double radius) =>
      radius <= 0 ? 0 : radius * backgroundBlurSigmaPerRadius;

  /// Visible extent of a Gaussian beyond the source edge (~3 sigma).
  static double shadowExtent(double blurRadius, double spread) =>
      shadowSigma(blurRadius) * 3 + spread.abs();
}
