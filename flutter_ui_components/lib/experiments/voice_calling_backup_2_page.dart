import 'dart:ui' as ui;

import 'package:flutter/material.dart';

class VoiceCallingBackup2Assets {
  static const _root = 'assets/lanhu/voice_calling_backup_2/assets';
  static const shield =
      '$_root/e4e467e6bab6852ac70c36d2b159fb5a0a730149ada97ffcc83dffd906683902.png';
  static const gift =
      '$_root/558d8e2c005694e3681dc3c9ec9863006e82b324a44114abed71e1d008aa5152.png';
  static const avatarRing =
      '$_root/dc893d0b1e3bc8139d1e511f5250f7290a0fbf689312bef2397e310b0ec37e56.png';
  static const relationship =
      '$_root/133b8e33c13b283abc95f060ebd21acf1ee75d7b90a8c1024baebafc282c82a5.png';
  static const all = [shield, gift, avatarRing, relationship];
}

class VoiceCallingBackup2Page extends StatelessWidget {
  const VoiceCallingBackup2Page({
    super.key,
    this.onMinimize,
    this.onMore,
    this.onClose,
    this.onRelationship,
    this.onMessage,
    this.onPhoto,
    this.onGift,
  });

  final VoidCallback? onMinimize;
  final VoidCallback? onMore;
  final VoidCallback? onClose;
  final VoidCallback? onRelationship;
  final VoidCallback? onMessage;
  final VoidCallback? onPhoto;
  final VoidCallback? onGift;

  static const size = Size(375, 812);
  static const gold = Color(0xFFE6B55E);

  @override
  Widget build(BuildContext context) => SizedBox(
        width: size.width,
        height: size.height,
        child: ClipRect(
          child: DefaultTextStyle(
            style: const TextStyle(fontFamily: 'SourcePingFang'),
            child: Stack(
              children: [
                const Positioned.fill(
                    child: CustomPaint(painter: _BackgroundPainter())),
                _statusBar(),
                _roundControl(
                    236, '最小化语音通话', _ControlKind.minimize, onMinimize),
                _roundControl(283, '更多操作', _ControlKind.more, onMore),
                _roundControl(329, '结束语音通话', _ControlKind.close, onClose),
                _text('14s后开始产生奖励', 120, 109, 150, 22, 16, 22, Colors.white,
                    weight: FontWeight.w600),
                _text(
                    '语音通话中', 160, 135, 80, 17, 12, 17, const Color(0xCCFFFFFF)),
                const Positioned(
                    left: 34,
                    top: 199,
                    width: 85,
                    height: 38,
                    child: CustomPaint(painter: _WavePainter(reverse: false))),
                const Positioned(
                    left: 257,
                    top: 199,
                    width: 85,
                    height: 38,
                    child: CustomPaint(painter: _WavePainter(reverse: true))),
                Positioned(
                  left: 148,
                  top: 178,
                  width: 80,
                  height: 80,
                  child: Semantics(
                    image: true,
                    label: '设计素材未切图：通话头像',
                    child: const DecoratedBox(
                      decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Color(0xFFFFE5EA),
                          border: Border.fromBorderSide(
                              BorderSide(color: Color(0xFFFF4D6D)))),
                      child: Center(
                          child: Text('未切图',
                              style: TextStyle(
                                  fontFamily: 'SourcePingFang',
                                  fontSize: 10,
                                  color: Color(0xFFC52245)))),
                    ),
                  ),
                ),
                Positioned(
                    left: 138,
                    top: 168,
                    width: 100,
                    height: 100,
                    child: Image.asset(VoiceCallingBackup2Assets.avatarRing,
                        fit: BoxFit.fill, filterQuality: FilterQuality.high)),
                const Positioned(
                    left: 138,
                    top: 168,
                    width: 100,
                    height: 100,
                    child: DecoratedBox(
                        decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.fromBorderSide(
                                BorderSide(color: Color(0x2CE8C77B), width: 1)),
                            boxShadow: [
                          BoxShadow(
                              color: Color(0x2CE8C77B),
                              blurRadius: 4,
                              offset: Offset(2, 2)),
                          BoxShadow(
                              color: Color(0x2CE8C77B),
                              blurRadius: 4,
                              offset: Offset(-2, -2))
                        ]))),
                const Positioned(
                    left: 141,
                    top: 171,
                    width: 94,
                    height: 94,
                    child: DecoratedBox(
                        decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.fromBorderSide(
                                BorderSide(color: Color(0x2CE8C77B), width: 1)),
                            boxShadow: [
                          BoxShadow(
                              color: Color(0x2CE8C77B),
                              blurRadius: 4,
                              offset: Offset(2, 2)),
                          BoxShadow(
                              color: Color(0x2CE8C77B),
                              blurRadius: 4,
                              offset: Offset(-2, -2))
                        ]))),
                _text('变形金钢', 158, 280, 80, 21, 15, 21, Colors.white,
                    weight: FontWeight.w600),
                _relationshipButton(),
                _safetyNotice(),
                _dialogue(),
                _messageButton(),
                _photoButton(),
                _giftButton(),
                const Positioned(
                    left: 121,
                    top: 799,
                    width: 134,
                    height: 5,
                    child: DecoratedBox(
                        decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius:
                                BorderRadius.all(Radius.circular(3))))),
              ],
            ),
          ),
        ),
      );

  Widget _relationshipButton() => Positioned(
        left: 137,
        top: 308,
        width: 100,
        height: 22,
        child: Semantics(
          button: true,
          label: '查看和Ta的关系',
          child: GestureDetector(
            key: const ValueKey('voice-relationship'),
            behavior: HitTestBehavior.opaque,
            onTap: onRelationship,
            child: DecoratedBox(
              decoration: BoxDecoration(
                  color: const Color(0x0DFFF8EA),
                  borderRadius: BorderRadius.circular(16),
                  border:
                      Border.all(color: const Color(0x6BE7C98F), width: .5)),
              child: Stack(
                children: [
                  Positioned(
                      left: 8,
                      top: 4,
                      width: 14,
                      height: 14,
                      child: Image.asset(VoiceCallingBackup2Assets.relationship,
                          fit: BoxFit.fill, filterQuality: FilterQuality.high)),
                  const Positioned(
                      left: 23,
                      top: 3,
                      child: Text('和Ta的关系',
                          style: TextStyle(
                              fontFamily: 'SourcePingFang',
                              fontSize: 11,
                              height: 16 / 11,
                              color: gold))),
                  const Positioned(
                      left: 88,
                      top: 8,
                      width: 3,
                      height: 6,
                      child: CustomPaint(painter: _RelationshipArrowPainter())),
                ],
              ),
            ),
          ),
        ),
      );

  Widget _safetyNotice() => Stack(
        children: [
          Positioned(
              left: 14,
              top: 611,
              width: 278,
              height: 45,
              child: DecoratedBox(
                  decoration: BoxDecoration(
                      color: const Color(0x1A000000),
                      borderRadius: BorderRadius.circular(10)))),
          Positioned(
              left: 24,
              top: 620,
              width: 10,
              height: 11,
              child: Image.asset(VoiceCallingBackup2Assets.shield,
                  fit: BoxFit.fill)),
          _text('平台严禁涉黄、低俗、欺诈，如有发现请及时\n举报，平台会对其严肃警告或封号处理', 38, 617, 247, 34, 12,
              17, const Color(0xFFA49A8C)),
        ],
      );

  Widget _dialogue() => Stack(
        children: [
          Positioned(
              left: 14,
              top: 664,
              width: 241,
              height: 26,
              child: DecoratedBox(
                  decoration: BoxDecoration(
                      color: const Color(0x1A000000),
                      borderRadius: BorderRadius.circular(8)))),
          Positioned(
              left: 14,
              top: 694,
              width: 223,
              height: 26,
              child: DecoratedBox(
                  decoration: BoxDecoration(
                      color: const Color(0x1A000000),
                      borderRadius: BorderRadius.circular(8)))),
          _text('变形金钢：', 25, 669, 62, 17, 12, 17, const Color(0xFFFFCF63)),
          _text('你在干什么啊？不方便说话吗？', 81, 669, 175, 17, 12, 17, Colors.white),
          _text('我：', 25, 699, 25, 17, 12, 17, const Color(0xFFA8B5FF)),
          _text('在外面不方便讲话，你声音好好听', 47, 699, 190, 17, 12, 17, Colors.white,
              leftAlpha: .85),
        ],
      );

  Widget _messageButton() => Positioned(
        left: 14,
        top: 732,
        width: 189,
        height: 40,
        child: Semantics(
          button: true,
          label: '不方便讲话，可以发文字',
          child: GestureDetector(
            key: const ValueKey('voice-message'),
            behavior: HitTestBehavior.opaque,
            onTap: onMessage,
            child: CustomPaint(
              painter: const _MessageGlassPainter(),
              child: Stack(children: [
                const Positioned(
                    left: 12,
                    top: 11,
                    width: 18,
                    height: 18,
                    child: CustomPaint(painter: _MessagePainter())),
                _text('不方便讲话，可以发文字', 36, 12, 140, 17, 12, 17,
                    const Color(0xFF9B8B76)),
              ]),
            ),
          ),
        ),
      );

  Widget _photoButton() => Positioned(
        left: 213,
        top: 731,
        width: 40,
        height: 40,
        child: _GlassButton(
            label: '发送图片',
            onTap: onPhoto,
            child: const CustomPaint(painter: _PhotoPainter())),
      );

  Widget _giftButton() => Positioned(
        left: 263,
        top: 731,
        width: 40,
        height: 40,
        child: _GlassButton(
            label: '送礼物',
            onTap: onGift,
            child: Center(
                child: Transform.translate(
                    offset: const Offset(0, 1),
                    child: Image.asset(VoiceCallingBackup2Assets.gift,
                        width: 20, height: 18, fit: BoxFit.fill)))),
      );

  static Widget _roundControl(
          double x, String label, _ControlKind kind, VoidCallback? onTap) =>
      Positioned(
        left: x,
        top: 52,
        width: 32,
        height: 32,
        child: Semantics(
          button: true,
          label: label,
          child: GestureDetector(
            key: ValueKey('voice-control-${kind.name}'),
            behavior: HitTestBehavior.opaque,
            onTap: onTap,
            child: CustomPaint(painter: _RoundControlPainter(kind)),
          ),
        ),
      );

  static Widget _statusBar() => Stack(children: [
        const Positioned(
            left: 37.25,
            top: 17.25,
            width: 41,
            height: 18,
            child: Text('9:41',
                textAlign: TextAlign.left,
                textScaler: TextScaler.noScaling,
                style: TextStyle(
                    inherit: false,
                    fontFamily: 'SourcePingFang',
                    fontSize: 15,
                    height: 18 / 15,
                    letterSpacing: .4,
                    color: Colors.white))),
        const Positioned(
            left: 287,
            top: 19,
            width: 70,
            height: 14,
            child: CustomPaint(painter: _StatusPainter())),
      ]);

  static Widget _text(String value, double x, double y, double width,
      double height, double fontSize, double lineHeight, Color color,
      {FontWeight weight = FontWeight.w400,
      double letterSpacing = 0,
      double? leftAlpha}) {
    final foreground = leftAlpha == null
        ? null
        : (Paint()
          ..shader = ui.Gradient.linear(Offset.zero, Offset(width, 0),
              [color.withValues(alpha: leftAlpha), color], const [0, 1]));
    final text = Text(value,
        textScaler: TextScaler.noScaling,
        overflow: TextOverflow.visible,
        style: TextStyle(
            inherit: false,
            decoration: TextDecoration.none,
            fontFamily: 'SourcePingFang',
            fontSize: fontSize,
            height: lineHeight / fontSize,
            leadingDistribution: TextLeadingDistribution.even,
            fontWeight: weight,
            letterSpacing: letterSpacing,
            color: foreground == null ? color : null,
            foreground: foreground));
    return Positioned(
        left: x, top: y, width: width, height: height, child: text);
  }
}

class _GlassButton extends StatelessWidget {
  const _GlassButton(
      {required this.label, required this.onTap, required this.child});
  final String label;
  final VoidCallback? onTap;
  final Widget child;
  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: label,
        child: GestureDetector(
          key: ValueKey('voice-glass-$label'),
          behavior: HitTestBehavior.opaque,
          onTap: onTap,
          child: CustomPaint(
            painter: const _GlassButtonPainter(),
            child: Padding(padding: const EdgeInsets.all(10), child: child),
          ),
        ),
      );
}

class _GlassButtonPainter extends CustomPainter {
  const _GlassButtonPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawCircle(
        size.center(Offset.zero),
        size.shortestSide / 2,
        Paint()
          ..shader = const RadialGradient(
              center: Alignment(-.3, -.6),
              radius: .9,
              colors: [Color(0x38FFFFFF), Color(0x0DFFFFFF), Color(0x1AC59B54)],
              stops: [0, .56, 1]).createShader(rect));
    canvas.drawCircle(
        size.center(Offset.zero),
        size.shortestSide / 2 - .25,
        Paint()
          ..shader = const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0x9EFFFFFF), Color(0x1FFFFFFF), Color(0x6BD5AA5C)],
              stops: [0, .5, 1]).createShader(rect)
          ..style = PaintingStyle.stroke
          ..strokeWidth = .5);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MessageGlassPainter extends CustomPainter {
  const _MessageGlassPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final shape =
        RRect.fromRectAndRadius(rect, Radius.circular(size.height / 2));
    canvas.drawRRect(
        shape,
        Paint()
          ..shader = const RadialGradient(
              center: Alignment.topLeft,
              radius: 1.9,
              colors: [Color(0x24FFFFFF), Color(0x06FFFFFF), Color(0x0DC59B54)],
              stops: [0, .56, 1]).createShader(rect));
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            rect.deflate(.3), Radius.circular(size.height / 2)),
        Paint()
          ..shader = const LinearGradient(
              begin: Alignment(-1.0343708657, -4.237356186),
              end: Alignment(.9295221567, 2.6805098057),
              colors: [Color(0x9EFFFFFF), Color(0x1FFFFFFF), Color(0x6BD5AA5C)],
              stops: [0, .5, 1]).createShader(rect)
          ..style = PaintingStyle.stroke
          ..strokeWidth = .6);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _BackgroundPainter extends CustomPainter {
  const _BackgroundPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawRect(
        rect,
        Paint()
          ..shader = const LinearGradient(
              begin: Alignment(-4.6886684895, -1),
              end: Alignment(4.6886682510, 1),
              colors: [Color(0xFF0C0B0A), Color(0xFF17130F), Color(0xFF2A211A)],
              stops: [0, .52, 1]).createShader(rect));

    // MCP gradient: 375×660 radial layer, center=(.5,.33), radius=.5w.
    final fieldRect = const Rect.fromLTWH(0, 17, 375, 660);
    canvas.drawRect(
        fieldRect,
        Paint()
          ..shader = ui.Gradient.radial(
              const Offset(187.5, 234.8),
              187.5,
              const [Color(0x47D8A957), Color(0x1A8E632E), Color(0x00000000)],
              const [.0, .52, 1]));

    // The two soft fields are explicit blurred ellipse nodes in the source.
    final softField = Paint()
      ..color = const Color(0x14C19042)
      ..maskFilter = const ui.MaskFilter.blur(ui.BlurStyle.normal, 52);
    canvas.drawOval(const Rect.fromLTWH(75.5, 172, 224, 208), softField);
    canvas.drawOval(
        const Rect.fromLTWH(156.5, 491, 218.5, 321),
        Paint()
          ..color = const Color(0x14C19042)
          ..maskFilter = const ui.MaskFilter.blur(ui.BlurStyle.normal, 62));
    final dot = Paint()..color = const Color(0xFFE7B45E);
    canvas.drawCircle(const Offset(86, 159), 2, dot);
    canvas.drawCircle(const Offset(295, 159), 2, dot);
    canvas.drawCircle(
        const Offset(212, 112), 2, dot..color = const Color(0x80E7B45E));
    canvas.drawCircle(
        const Offset(103, 175), 2, dot..color = const Color(0x4DE7B45E));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _RelationshipArrowPainter extends CustomPainter {
  const _RelationshipArrowPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(0, 0)
      ..lineTo(size.width, size.height * .5)
      ..lineTo(0, size.height);
    canvas.drawPath(
        path,
        Paint()
          ..color = VoiceCallingBackup2Page.gold
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _WavePainter extends CustomPainter {
  const _WavePainter({required this.reverse});
  final bool reverse;
  @override
  void paint(Canvas canvas, Size size) {
    // Bounds come from the nine source waveform nodes.  Keeping the source
    // centers matters here: an earlier evenly-spaced approximation shifted
    // the whole waveform about nine pixels to the left.
    const centers = [
      10.5,
      19.625,
      28.75,
      37.875,
      47.125,
      56.125,
      65.375,
      74.5,
      83.625
    ];
    const heights = [11.5, 12.5, 21.0, 11.5, 16.0, 28.5, 21.0, 25.5, 38.0];
    final p = Paint()
      ..color = const Color(0x997A4E18)
      ..strokeWidth = 2.7
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < heights.length; i++) {
      final index = reverse ? heights.length - 1 - i : i;
      final h = heights[index];
      final x = centers[i];
      canvas.drawLine(Offset(x, (size.height - h) / 2),
          Offset(x, (size.height + h) / 2), p);
    }
  }

  @override
  bool shouldRepaint(covariant _WavePainter oldDelegate) =>
      oldDelegate.reverse != reverse;
}

enum _ControlKind { minimize, more, close }

class _RoundControlPainter extends CustomPainter {
  const _RoundControlPainter(this.kind);
  final _ControlKind kind;
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawCircle(
        size.center(Offset.zero),
        16,
        Paint()
          ..shader = const RadialGradient(center: Alignment.topLeft, colors: [
            Color(0x4DFFFFFF),
            Color(0x0DFFFFFF),
            Color(0x263D2A13)
          ]).createShader(rect));
    canvas.drawCircle(
        size.center(Offset.zero),
        15.6,
        Paint()
          ..color = const Color(0x55C2B69F)
          ..style = PaintingStyle.stroke
          ..strokeWidth = .6);
    final p = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = kind == _ControlKind.minimize ? 1.25 : 1.8
      ..strokeCap = StrokeCap.round;
    if (kind == _ControlKind.close) {
      canvas.drawLine(const Offset(11, 11), const Offset(21, 21), p);
      canvas.drawLine(const Offset(21, 11), const Offset(11, 21), p);
    } else if (kind == _ControlKind.more) {
      for (final x in [9.75, 15.25, 21.25])
        canvas.drawCircle(Offset(x, 16.25), 1.5, Paint()..color = Colors.white);
    } else {
      final upperDiagonal = Path()
        ..moveTo(17.4166666667, 14.5833333333)
        ..lineTo(22, 10);
      final upperCorner = Path()
        ..moveTo(17.4166666667, 10.9166666667)
        ..lineTo(17.4166666667, 14.5833333333)
        ..lineTo(21.0833333333, 14.5833333333);
      final lowerDiagonal = Path()
        ..moveTo(14.5833333333, 17.4166666667)
        ..lineTo(10, 22);
      final lowerCorner = Path()
        ..moveTo(14.5833333333, 21.0833333333)
        ..lineTo(14.5833333333, 17.4166666667)
        ..lineTo(10.9166666667, 17.4166666667);
      canvas.drawPath(upperDiagonal, p);
      canvas.drawPath(upperCorner, p);
      canvas.drawPath(lowerDiagonal, p);
      canvas.drawPath(lowerCorner, p);
    }
  }

  @override
  bool shouldRepaint(covariant _RoundControlPainter oldDelegate) =>
      oldDelegate.kind != kind;
}

class _StatusPainter extends CustomPainter {
  const _StatusPainter();
  @override
  void paint(Canvas canvas, Size size) {
    const c = Colors.white;
    final p = Paint()..color = c;
    for (var i = 0; i < 4; i++)
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.0, 10 - i * 2.4, 3, 4 + i * 2.4),
              const Radius.circular(1)),
          p);
    final wifi = Path()
      ..moveTo(23, 5)
      ..quadraticBezierTo(30.5, -1, 38, 5)
      ..moveTo(26, 8)
      ..quadraticBezierTo(30.5, 4, 35, 8)
      ..moveTo(29, 11)
      ..quadraticBezierTo(30.5, 9.5, 32, 11);
    canvas.drawPath(
        wifi,
        Paint()
          ..color = c
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..strokeCap = StrokeCap.round);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(44, 1, 22, 11), const Radius.circular(3)),
        Paint()
          ..color = c.withValues(alpha: .35)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(46, 3, 18, 7), const Radius.circular(1.5)),
        p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MessagePainter extends CustomPainter {
  const _MessagePainter();
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawCircle(
        size.center(Offset.zero),
        9,
        Paint()
          ..shader = const LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0xFFFFE5C3), Color(0xFFBC914A)])
              .createShader(Offset.zero & size));
    final p = Paint()..color = const Color(0xFF18181B);
    for (final x in [5.7, 9.0, 12.3]) {
      canvas.drawCircle(Offset(x, 9), .85, p);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _PhotoPainter extends CustomPainter {
  const _PhotoPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = const Color(0xFFE6B55E)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.4571428571
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawRRect(
        RRect.fromRectAndRadius(const Rect.fromLTWH(1, 4, 17, 13.7619047619),
            const Radius.circular(3.2380952381)),
        Paint()
          ..shader = const LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0xFFFFE5C3), Color(0xFFBC914A)])
              .createShader(Offset.zero & size)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.4571428571);
    canvas.drawCircle(const Offset(4.8571428571, 7.6907439446), 1.5833333333,
        Paint()..color = const Color(0xFFE6B55E));
    final path = Path()
      ..moveTo(1, 15.5384948097)
      ..lineTo(6.5, 10.5973183391)
      ..lineTo(10, 13.2)
      ..lineTo(13, 10.9)
      ..lineTo(18, 15.5);
    canvas.drawPath(path, p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
