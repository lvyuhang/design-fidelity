/// Verified Flutter rendering primitives for Lanhu (Sketch) design data.
///
/// Every source effect that has a dedicated primitive here must be rendered
/// through it, so one calibrated implementation is shared by all pages.
/// `scripts/generate_flutter.py` emits code against this API and
/// `scripts/dart_fidelity_lint.py` rejects hand-rolled equivalents.
library design_fidelity;

export 'src/effects.dart';
export 'src/source_asset.dart';
export 'src/source_blur.dart';
export 'src/source_box.dart';
export 'src/source_fonts.dart';
export 'src/source_key.dart';
export 'src/source_paint.dart';
export 'src/source_text.dart';
export 'src/system_chrome.dart';
