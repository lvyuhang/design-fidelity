import 'package:flutter/foundation.dart';

/// Production font families per platform for a design font.
///
/// Fidelity renders always use the design font loaded from disk by the test
/// harness (it is never bundled); apps ship whatever each platform may use:
/// e.g. the iOS system font (which is the design's PingFang) and a licensed
/// font on Android.
abstract final class SourceFonts {
  /// Pass for a platform to use its system font (`fontFamily: null`).
  static const String system = '';

  /// Set by the fidelity harness: every token resolves to the design family.
  static bool useDesignFonts = false;
}

/// Resolves the font family of a generated text token for the current
/// platform. Omitted platforms fall back to [design].
String? sourceFontFamily(String design, {String? ios, String? android}) {
  if (SourceFonts.useDesignFonts) return design;
  final family = switch (defaultTargetPlatform) {
        TargetPlatform.iOS || TargetPlatform.macOS => ios,
        TargetPlatform.android => android,
        _ => null,
      } ??
      design;
  return family.isEmpty ? null : family;
}
