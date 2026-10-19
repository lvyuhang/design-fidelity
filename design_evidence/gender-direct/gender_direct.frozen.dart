import 'dart:ui' as ui;
import 'package:flutter/material.dart';

/// Independent MCP first pass. Frozen before rendering; see gender-direct/protocol.json.
/// Source canvas 375 x 812, crop (0, 146, 375, 350).
class DirectGenderSelection extends StatelessWidget {
  const DirectGenderSelection(
      {super.key, this.femaleSelected = false, this.onSelect});
  final bool femaleSelected;
  final ValueChanged<String>? onSelect;
  static const maleAsset =
      'assets/lanhu/gender_none/assets/a25cff5f9aabb90c8c6f286be1a49d34401850108d0459495065cdf59093df43.png';
  static const femaleAsset =
      'assets/lanhu/gender_none/assets/d2855e7611728cfc07b1476da674344d477abedc8d9fbc67f9087bba0c093a49.png';
  static const selectedAsset =
      'assets/lanhu/gender_female/assets/eacdc3db8eff06ddcc26f3a404612bc55bc07315ac2ef98900c27fabedff1272.png';
  static const checkAsset =
      'assets/lanhu/gender_female/assets/946fd6e0fb04feeae95ea8730b2c3eb280c50393cc9848ac36ac39e1282fec1f.png';
  static const warningAsset =
      'assets/lanhu/gender_female/assets/10416d514d09343fe90359c1170c63f1b6a2a75432844bdc11e568ac56157832.png';

  @override
  Widget build(BuildContext context) => SizedBox(
      width: 375,
      height: 350,
      child: ClipRect(
          child: Stack(clipBehavior: Clip.none, children: [
        const Positioned.fill(
            child: DecoratedBox(
                decoration: BoxDecoration(
                    gradient: LinearGradient(
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                        colors: [
              Color(0xFFFFFDF9),
              Color(0xFFFFFBF2),
              Colors.white
            ],
                        stops: [
              0,
              0.5574737762237763,
              1
            ])))),
        Positioned(
            left: 143.1297709923665,
            top: -85.8802816901408 - 146,
            width: 314.88549618320576,
            height: 314.8943661971831,
            child: Opacity(
                opacity: .42,
                child: ImageFiltered(
                    imageFilter: ui.ImageFilter.blur(
                        sigmaX: 9.541984732824428 / 2,
                        sigmaY: 9.541984732824428 / 2),
                    child: const DecoratedBox(
                        decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: RadialGradient(colors: [
                              Color.fromRGBO(242, 205, 116, .28),
                              Color.fromRGBO(255, 241, 216, .13),
                              Color(0x00FFFFFF)
                            ], stops: [
                              0,
                              .5600000023841858,
                              1
                            ])))))),
        _text('选择你的性别', 27, 1, 180, 42, 30, const Color(0xFF18181B),
            FontWeight.w600),
        _text('用于为你推荐更合适的互动内容', 30, 45, 168, 17, 12, const Color(0xFF9A9AA2)),
        _option(30, false, '男生', 'male', maleAsset),
        _option(206, femaleSelected, '女生', 'female',
            femaleSelected ? selectedAsset : femaleAsset),
        if (femaleSelected) ...[
          _image(checkAsset, 315, 113, 25, 25),
          Positioned(
              left: 33,
              top: 297,
              width: 307,
              height: 36,
              child: ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: Stack(children: [
                    Positioned.fill(
                        child: DecoratedBox(
                            decoration: BoxDecoration(
                                color: const Color(0xFFFEEFE9),
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                    color: const Color(0xFFF9CBC3),
                                    width: 1)))),
                    // Only the two available source paths. Boolean fill geometry is absent.
                    const Positioned(
                        left: 265.00004766042093,
                        top: 5,
                        width: 29.99990478719792,
                        height: 34,
                        child: Opacity(
                            opacity: .37,
                            child:
                                CustomPaint(painter: _AvailableShieldPaths()))),
                  ]))),
          _image(warningAsset, 46, 302, 26, 26),
          _text('选择性别提交后将不可修改', 80, 306, 156, 18, 13, const Color(0xFFD12C29)),
        ],
      ])));

  Widget _option(
          double x, bool selected, String label, String value, String asset) =>
      Positioned(
          left: x,
          top: 117,
          width: 134,
          height: 164,
          child: Semantics(
              button: true,
              selected: selected,
              label: label,
              child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () => onSelect?.call(value),
                  child: Stack(clipBehavior: Clip.none, children: [
                    // Source specifies an outer shadow: exclude the transparent card interior.
                    Positioned.fill(
                        child: ClipPath(
                            clipper: _OutsideCard(),
                            child: DecoratedBox(
                                decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(22),
                                    boxShadow: const [
                                  BoxShadow(
                                      color: Color.fromRGBO(216, 155, 71, .1),
                                      offset: Offset(0, 6),
                                      blurRadius: 12)
                                ])))),
                    Positioned.fill(
                        child: DecoratedBox(
                            decoration: BoxDecoration(
                                color: selected
                                    ? const Color(0xFFFFF9EC)
                                    : const Color.fromRGBO(255, 253, 249, .3),
                                borderRadius: BorderRadius.circular(22),
                                border: Border.all(
                                    color: selected
                                        ? const Color(0xFFDDAA5A)
                                        : const Color(0xFFEEDCC4),
                                    width: 1)))),
                    _image(asset, 35, 46, 64, 64),
                    _text(label, 53, 123, 28, 22, 14, const Color(0xFF171718)),
                  ]))));

  static Widget _image(String asset, double x, double y, double w, double h) =>
      Positioned(
          left: x,
          top: y,
          width: w,
          height: h,
          child: Image.asset(asset,
              fit: BoxFit.fill, filterQuality: FilterQuality.high));

  static Widget _text(String value, double x, double y, double w, double h,
          double size, Color color, [FontWeight weight = FontWeight.w400]) =>
      Positioned(
          left: x,
          top: y,
          width: w,
          height: h,
          child: Text(value,
              maxLines: 1,
              softWrap: false,
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                  inherit: false,
                  fontFamily: 'SourcePingFang',
                  fontSize: size,
                  height: h / size,
                  fontWeight: weight,
                  color: color,
                  letterSpacing: 0,
                  leadingDistribution: TextLeadingDistribution.even)));
}

class _OutsideCard extends CustomClipper<Path> {
  @override
  Path getClip(Size size) => Path()
    ..fillType = PathFillType.evenOdd
    ..addRect((Offset.zero & size).inflate(40))
    ..addRRect(
        RRect.fromRectAndRadius(Offset.zero & size, const Radius.circular(22)));
  @override
  bool shouldReclip(_OutsideCard oldClipper) => false;
}

class _AvailableShieldPaths extends CustomPainter {
  const _AvailableShieldPaths();
  @override
  void paint(Canvas canvas, Size size) {
    final outline = Path()..moveTo(16.662439273276, 0.633463375270);
    outline.cubicTo(20.695437075466, 4.225512593985, 24.725935066787,
        6.190736740828, 28.758932868977, 6.526630103588);
    outline.cubicTo(29.456591100937, 6.555020153522, 30.005834238441,
        7.133054763079, 29.999856507589, 7.832601785660);
    outline.cubicTo(29.734658403268, 21.689438819885, 25.031162331403,
        30.357483029366, 15.889362927595, 33.836732387543);
    outline.cubicTo(15.317188763930, 34.054421186447, 14.685217622269,
        34.054421186447, 14.113042564537, 33.836732387543);
    outline.cubicTo(4.966241303826, 30.357483029366, 0.262743779103,
        21.689438819885, 0.000048438526, 7.832601785660);
    outline.cubicTo(-0.005929799615, 7.134438395500, 0.542194649860,
        6.557525485754, 1.238469313394, 6.529136449099);
    outline.cubicTo(5.271468121409, 6.190736740828, 9.304466817665,
        4.225512593985, 13.337466407988, 0.633463375270);
    outline.cubicTo(14.285492857693, -0.211154447868, 15.714411929505,
        -0.211154447868, 16.662439273276, 0.633463375270);
    outline.close();
    final check = Path()..moveTo(22.744461709474, 12.086410148574);
    check.cubicTo(23.232802363248, 12.575836080972, 23.232802363248,
        13.369195557122, 22.744461709474, 13.858621449904);
    check.lineTo(14.635931731232, 21.985225170946);
    check.cubicTo(14.147443504958, 22.474504013992, 13.355604583182,
        22.474504013992, 12.867116356908, 21.985225170946);
    check.lineTo(7.555666826280, 16.671098045054);
    check.cubicTo(7.066531124178, 16.181023422074, 7.066531131592,
        15.386455063982, 7.555666855936, 14.896380124085);
    check.cubicTo(8.044802580280, 14.406305501105, 8.837848298715,
        14.406305501105, 9.326983993402, 14.896380124085);
    check.lineTo(13.747771147275, 19.328161924917);
    check.lineTo(20.978147950006, 12.083903489320);
    check.cubicTo(21.466348148925, 11.596293593443, 22.256261510555,
        11.596293593443, 22.744461709474, 12.083903489320);
    check.lineTo(22.744461709474, 12.086410148574);
    check.close();
    canvas.drawPath(
        outline,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3
          ..shader = ui.Gradient.linear(
              Offset.zero,
              const Offset(0, 34 * .8498391509056091),
              const [Color(0xFFF6C1BE), Color.fromRGBO(251, 226, 224, .76)]));
    canvas.drawPath(check, Paint()..color = const Color(0xFFF6C1BE));
  }

  @override
  bool shouldRepaint(_AvailableShieldPaths oldDelegate) => false;
}
