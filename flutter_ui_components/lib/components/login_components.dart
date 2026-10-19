import 'dart:ui' as ui;
import 'package:flutter/material.dart';

// All baseline values come from design_evidence/login-source.json.
// Snapshot ed07411fb68b9878b1395ab190b98915; version 18f1a6ed-585a-4b77-801b-7a9d5e726810.
class LoginDesign {
  static const canvasWidth = 375.0;
  static const stage = Rect.fromLTWH(0, 389, 375, 395);
  static const button = Size(299, 50);
  static const fill = Color.fromRGBO(255, 253, 249, .85);
  static const border = Color(0xFFEEDCC4);
  static const text = Color(0xFF22242A);
  static const agreementText = Color(0xFF91919B);
  static const shadow = Color.fromRGBO(216, 155, 71, .1);
  static const ringAsset =
      'assets/lanhu/assets/9d0654e6ecfa4fe81881a272ab3990f51329b81d32eaecc985c37e6084f234c8.png';
  static const agreement = '我已阅读并同意《用户协议》、《隐私协议》、《用户违规行为管理办法》、《运营商认证服务条款》';
  static const providers = [
    LoginProvider('微信登录', 'wechat', 405, Offset(103, 16), Size(23, 19),
        '05d568660f8b15118112812d36654cc19a41abfa447fcaf5aa60ea9eba71a8db.png'),
    LoginProvider('QQ登录', 'qq', 473, Offset(105, 16), Size(19, 19),
        '6ae1b2c8ae7ea66059d0dc46e6197f7ea99ea82ac2cddc0c66beb254b8d1798d.png'),
    LoginProvider('手机号登录', 'phone', 541, Offset(108, 15), Size(14, 20),
        'aa419996555f658c1ee97725d7f9fa542e2992af291636eff79e96e9dfa5855d.png'),
    LoginProvider('苹果登录', 'apple', 609, Offset(108, 16), Size(16, 19),
        '9b1e35de0078f86a5139ce45acbb9fae30e8548c2fa8029fb8116dce58924a87.png'),
  ];
}

class LoginProvider {
  const LoginProvider(this.label, this.id, this.y, this.iconOffset,
      this.iconSize, this.filename);
  final String label, id, filename;
  final double y;
  final Offset iconOffset;
  final Size iconSize;
  String get asset => 'assets/lanhu/assets/$filename';
}

/// Native text, border, fill and shadow; only the designer's icon is an image.
class LoginProviderButton extends StatelessWidget {
  const LoginProviderButton(
      {required this.provider, this.onPressed, super.key});
  final LoginProvider provider;
  final VoidCallback? onPressed;
  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: provider.label,
        enabled: onPressed != null,
        child: MouseRegion(
          cursor:
              onPressed == null ? MouseCursor.defer : SystemMouseCursors.click,
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: onPressed,
            child: SizedBox.fromSize(
              size: LoginDesign.button,
              child: CustomPaint(
                painter: const _LoginButtonPainter(),
                child: Stack(children: [
                  // Export frame rounds up the tighter vector bounds; preserve its transparent padding.
                  Positioned(
                      left: provider.iconOffset.dx,
                      top: provider.iconOffset.dy,
                      width: provider.iconSize.width,
                      height: provider.iconSize.height,
                      child: Image.asset(provider.asset,
                          fit: BoxFit.fill, filterQuality: FilterQuality.high)),
                  Positioned(
                      left: 134,
                      top: 15,
                      height: 20,
                      right: 0,
                      child: Text(provider.label,
                          textScaler: TextScaler.noScaling,
                          style: const TextStyle(
                              inherit: false,
                              letterSpacing: 0,
                              decoration: TextDecoration.none,
                              fontFamily: 'SourcePingFang',
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              height: 20 / 14,
                              leadingDistribution: TextLeadingDistribution.even,
                              color: LoginDesign.text))),
                ]),
              ),
            ),
          ),
        ),
      );
}

class _LoginButtonPainter extends CustomPainter {
  const _LoginButtonPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final bounds = Offset.zero & size;
    final shape = RRect.fromRectAndRadius(bounds, const Radius.circular(25));
    // Sketch outer shadows knock out the shape interior. A regular Flutter
    // BoxShadow would darken this 85%-opaque fill from underneath.
    canvas.save();
    canvas.clipPath(Path()
      ..fillType = PathFillType.evenOdd
      ..addRect(bounds.inflate(80))
      ..addRRect(shape));
    canvas.drawRRect(
        shape.shift(const Offset(0, 6)),
        Paint()
          ..color = LoginDesign.shadow
          ..maskFilter =
              const MaskFilter.blur(BlurStyle.normal, 12 * .57735 + .5));
    canvas.restore();
    canvas.drawRRect(shape, Paint()..color = LoginDesign.fill);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            bounds.deflate(.5), const Radius.circular(24.5)),
        Paint()
          ..color = LoginDesign.border
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1);
  }

  @override
  bool shouldRepaint(_LoginButtonPainter oldDelegate) => false;
}

/// This source contains the unchecked state only. A checked style needs its own specimen.
class AgreementConsent extends StatelessWidget {
  const AgreementConsent({super.key});
  @override
  Widget build(BuildContext context) => Semantics(
        checked: false,
        label: LoginDesign.agreement,
        child: SizedBox(
            width: 321,
            height: 32,
            child: Stack(children: [
              Positioned(
                  left: 0,
                  top: 1,
                  width: 14,
                  height: 14,
                  child: Image.asset(LoginDesign.ringAsset,
                      filterQuality: FilterQuality.high)),
              const Positioned(
                  left: 20,
                  top: 0,
                  width: 301,
                  height: 32,
                  child: Text(LoginDesign.agreement,
                      textScaler: TextScaler.noScaling,
                      style: TextStyle(
                          inherit: false,
                          letterSpacing: 0,
                          decoration: TextDecoration.none,
                          fontFamily: 'SourcePingFang',
                          fontSize: 11,
                          fontWeight: FontWeight.w400,
                          height: 16 / 11,
                          leadingDistribution: TextLeadingDistribution.even,
                          color: LoginDesign.agreementText))),
            ])),
      );
}

/// A crop of a 375-unit source canvas, never expanded to browser width.
class LoginComponentStage extends StatelessWidget {
  const LoginComponentStage(
      {this.region = LoginDesign.stage, this.onProviderTap, super.key});
  final Rect region;
  final ValueChanged<String>? onProviderTap;
  @override
  Widget build(BuildContext context) => SizedBox(
        width: region.width,
        height: region.height,
        child: ClipRect(
            child: Stack(clipBehavior: Clip.none, children: [
          Positioned.fill(child: CustomPaint(painter: LoginBackground(region))),
          for (final provider in LoginDesign.providers)
            Positioned(
                left: 38 - region.left,
                top: provider.y - region.top,
                child: LoginProviderButton(
                    key: ValueKey(provider.id),
                    provider: provider,
                    onPressed: onProviderTap == null
                        ? null
                        : () => onProviderTap!(provider.id))),
          Positioned(
              left: 28 - region.left,
              top: 740 - region.top,
              child: const AgreementConsent()),
        ])),
      );
}

class LoginBackground extends CustomPainter {
  const LoginBackground(this.region);
  final Rect region;
  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(-region.left, -region.top);
    const bounds = Rect.fromLTWH(0, 0, 375, 812);
    canvas.clipRect(bounds);
    canvas.drawRect(bounds, Paint()..color = const Color(0xFFFAF6F0));
    canvas.drawRect(
        bounds,
        Paint()
          ..shader = ui.Gradient.linear(
              const Offset(0, 406),
              const Offset(375, 406),
              const [Color(0xFFFFFDF9), Color(0xFFFFFBF2), Colors.white],
              const [0, .557473776223776, 1]));
    _glow(
        canvas,
        const Rect.fromLTWH(143.129770992367, -85.8802816901408,
            314.885496183206, 314.894366197183),
        .42,
        9.54198473282443);
    _glow(
        canvas,
        const Rect.fromLTWH(-124.045801526718, 522.915492957746,
            353.053435114504, 353.06338028169),
        .50,
        11.4503816793893);
    canvas.restore();
  }

  void _glow(Canvas canvas, Rect bounds, double opacity, double blurRadius) {
    // layerOriginFrame preserves the off-canvas ellipse before clipping.
    final colors = [
      Color.fromRGBO(242, 205, 116, .28 * opacity),
      Color.fromRGBO(255, 241, 216, .13 * opacity),
      const Color(0x00FFFFFF)
    ];
    canvas.drawOval(
        bounds,
        Paint()
          ..shader = ui.Gradient.radial(bounds.center, bounds.width / 2, colors,
              const [0, .560000002384186, 1])
          ..maskFilter = MaskFilter.blur(BlurStyle.normal, blurRadius / 2));
  }

  @override
  bool shouldRepaint(LoginBackground oldDelegate) =>
      oldDelegate.region != region;
}
