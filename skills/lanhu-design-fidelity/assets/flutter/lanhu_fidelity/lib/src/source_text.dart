import 'package:flutter/widgets.dart';

/// Text style for a Lanhu text run.
///
/// * `inherit: false` - ambient Material/DefaultTextStyle letter spacing,
///   decoration or height must not leak into source text;
/// * `height = lineHeight / fontSize` with even leading distribution, which
///   matches Sketch's fixed line box (half the extra leading above, half
///   below);
/// * letter spacing is explicit (Sketch `kern`), default 0.
TextStyle sourceTextStyle({
  required String fontFamily,
  required double fontSize,
  required Color color,
  FontWeight fontWeight = FontWeight.w400,
  double? lineHeight,
  double letterSpacing = 0,
  TextDecoration decoration = TextDecoration.none,
  List<String>? fontFamilyFallback,
  String? package,
}) {
  return TextStyle(
    inherit: false,
    fontFamily: fontFamily,
    fontFamilyFallback: fontFamilyFallback,
    package: package,
    fontSize: fontSize,
    fontWeight: fontWeight,
    height: lineHeight == null ? null : lineHeight / fontSize,
    leadingDistribution: TextLeadingDistribution.even,
    letterSpacing: letterSpacing,
    color: color,
    decoration: decoration,
    textBaseline: TextBaseline.alphabetic,
  );
}

/// One styled range of a mixed-style Lanhu text node.
@immutable
class SourceTextRun {
  const SourceTextRun(this.text, this.style);

  final String text;

  /// Full style of the run (not a delta); build it with [sourceTextStyle].
  final TextStyle style;
}

/// Text that reproduces a Lanhu text box's line metrics.
///
/// When the base style has a line height, a forced strut fixes every line box
/// to that height even for mixed runs/fallback glyphs, as Sketch does.
/// Text scaling is NOT disabled: the fidelity harness pins it to 1.0, while the
/// shipped app keeps accessibility scaling (see the multi-size checks).
class SourceText extends StatelessWidget {
  const SourceText(
    String this.text, {
    super.key,
    required this.style,
    this.textAlign = TextAlign.left,
    this.softWrap = false,
    this.maxLines,
    this.overflow = TextOverflow.visible,
    this.semanticsLabel,
  }) : runs = null;

  const SourceText.rich(
    List<SourceTextRun> this.runs, {
    super.key,
    required this.style,
    this.textAlign = TextAlign.left,
    this.softWrap = false,
    this.maxLines,
    this.overflow = TextOverflow.visible,
    this.semanticsLabel,
  }) : text = null;

  final String? text;
  final List<SourceTextRun>? runs;

  /// Base paragraph style; also defines the strut.
  final TextStyle style;
  final TextAlign textAlign;

  /// Sketch auto-width text (textBehaviour 0) is single line: keep false.
  final bool softWrap;
  final int? maxLines;
  final TextOverflow overflow;
  final String? semanticsLabel;

  StrutStyle? get strutStyle {
    final height = style.height;
    if (height == null) return null;
    return StrutStyle(
      fontFamily: style.fontFamily,
      fontFamilyFallback: style.fontFamilyFallback,
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      height: height,
      leadingDistribution: TextLeadingDistribution.even,
      forceStrutHeight: true,
    );
  }

  @override
  Widget build(BuildContext context) {
    final span = runs == null
        ? TextSpan(text: text, style: style)
        : TextSpan(style: style, children: [
            for (final run in runs!) TextSpan(text: run.text, style: run.style),
          ]);
    return Text.rich(
      span,
      textAlign: textAlign,
      softWrap: softWrap,
      maxLines: maxLines,
      overflow: overflow,
      strutStyle: strutStyle,
      semanticsLabel: semanticsLabel,
      textHeightBehavior: const TextHeightBehavior(
        leadingDistribution: TextLeadingDistribution.even,
      ),
    );
  }
}
