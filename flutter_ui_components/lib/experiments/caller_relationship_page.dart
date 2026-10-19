import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';

class CallerRelationshipAssets {
  static const topFade =
      'assets/lanhu/caller_relationship/assets/724f5751b6438b10e1f13f9ba48349a39ce4d1e9ed616b6838b86b6ce9791e11.png';
  static const bottomFade =
      'assets/lanhu/caller_relationship/assets/c4230360431291bd733d3496f0a3029f71a18615047dcad1e7ba4aa5d3398a49.png';
  static const relation =
      'assets/lanhu/caller_relationship/assets/5859b2c3b9adbbf2f97f5176d19c6ac2f24293c8cacacb7c601e76a90ceb3c21.png';
  static const gift =
      'assets/lanhu/caller_relationship/assets/d8cc76f99f7becdebd771e7be0fac81ae8afe66257e7c9effa979da60364d235.png';
  static const shield =
      'assets/lanhu/caller_relationship/assets/5355d8346ce5e22f4be49f7731459ff6d76c15d1f4c773601d934b80078f237e.png';
  static const avatar = 'assets/fixtures/reply-avatar.png';
  static const miniVideo = 'assets/fixtures/feed-photo.png';

  static const all = [
    topFade,
    bottomFade,
    relation,
    gift,
    shield,
    avatar,
    miniVideo,
  ];
}

/// Native Flutter implementation of Lanhu artboard “拨打方-1备份 2”.
///
/// The live-video pixels are intentionally represented by a deterministic
/// placeholder because the Sketch bitmap layers have no exportable source
/// asset. Every foreground control and the relationship card remain native.
class CallerRelationshipScreen extends StatelessWidget {
  const CallerRelationshipScreen({
    super.key,
    this.onClose,
    this.onMessage,
    this.onGift,
    this.onOpenRelation,
  });

  final VoidCallback? onClose;
  final VoidCallback? onMessage;
  final VoidCallback? onGift;
  final VoidCallback? onOpenRelation;

  static const size = Size(375, 812);
  static const gold = Color(0xFFE6B55E);
  static const chartGold = Color(0xFFE8C77B);
  static const secondary = Color(0xFFA6AAB5);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size.width,
      height: size.height,
      child: ClipRect(
        child: Stack(
          children: [
            const Positioned.fill(
              child: CustomPaint(painter: _VideoPlaceholderPainter()),
            ),
            _asset(CallerRelationshipAssets.topFade, 0, 0, 375, 132),
            _topCallChrome(),
            _miniVideo(),
            _asset(CallerRelationshipAssets.bottomFade, 0, 604, 375, 208),
            _bottomCallChrome(),
            const Positioned(
              left: 0,
              top: 1,
              width: 375,
              height: 811,
              child: IgnorePointer(
                child: ColoredBox(color: Color(0x66000000)),
              ),
            ),
            _relationshipCard(),
          ],
        ),
      ),
    );
  }

  Widget _topCallChrome() {
    return Stack(
      children: [
        _text('9:41', 37, 16, 54, 18, 15, 18, Colors.white,
            weight: FontWeight.w600, family: 'SourcePingFang'),
        const Positioned(
          left: 287,
          top: 19,
          width: 70,
          height: 14,
          child: CustomPaint(painter: _StatusPainter()),
        ),
        Positioned(
          left: 18,
          top: 45,
          width: 152,
          height: 40,
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xD92B2520), Color(0x002B2520)],
              ),
              borderRadius: BorderRadius.circular(24),
            ),
          ),
        ),
        Positioned(
          left: 22,
          top: 50,
          width: 30,
          height: 30,
          child: DecoratedBox(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: .8),
              boxShadow: const [
                BoxShadow(color: Color(0xCCE8C77B), blurRadius: 6),
              ],
            ),
            child: ClipOval(
              child: Image.asset(
                CallerRelationshipAssets.avatar,
                fit: BoxFit.cover,
                filterQuality: FilterQuality.high,
              ),
            ),
          ),
        ),
        _text('变形金钢', 59, 48, 76, 18, 13, 18, const Color(0xFFE0D5C7),
            weight: FontWeight.w600),
        Positioned(
          left: 58,
          top: 67,
          width: 72,
          height: 16,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0x33B27A31),
              borderRadius: BorderRadius.circular(11),
            ),
          ),
        ),
        _asset(CallerRelationshipAssets.relation, 63.76, 69.79, 10.08, 10.41),
        _text('和Ta的关系', 77.08, 69.88, 42, 11, 7.92, 11, gold),
        const Positioned(
          left: 236,
          top: 50,
          width: 32,
          height: 32,
          child: CustomPaint(painter: _RoundControlPainter(kind: 0)),
        ),
        const Positioned(
          left: 283,
          top: 50,
          width: 32,
          height: 32,
          child: CustomPaint(painter: _RoundControlPainter(kind: 1)),
        ),
        Positioned(
          left: 329,
          top: 50,
          width: 32,
          height: 32,
          child: Semantics(
            button: true,
            label: '结束通话',
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onClose,
              child: const CustomPaint(painter: _RoundControlPainter(kind: 2)),
            ),
          ),
        ),
        _text('00:00:04', 19, 96, 92, 22, 16, 22, Colors.white,
            weight: FontWeight.w600,
            shadows: const [
              Shadow(
                  color: Color(0x52000000),
                  offset: Offset(0, 1),
                  blurRadius: 2),
            ]),
      ],
    );
  }

  Widget _miniVideo() => Positioned(
        left: 249,
        top: 104,
        width: 110,
        height: 147,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(7),
          child: Stack(
            fit: StackFit.expand,
            children: [
              Image.asset(
                CallerRelationshipAssets.miniVideo,
                fit: BoxFit.cover,
                alignment: const Alignment(.05, -.55),
                filterQuality: FilterQuality.high,
              ),
              const Positioned(
                left: 80,
                top: 5,
                child: SizedBox(
                  width: 24,
                  height: 24,
                  child: CustomPaint(painter: _SwitchCameraPainter()),
                ),
              ),
            ],
          ),
        ),
      );

  Widget _bottomCallChrome() {
    return Stack(
      children: [
        Positioned(
          left: 14,
          top: 670,
          width: 278,
          height: 45,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0x1A000000),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        ),
        _asset(CallerRelationshipAssets.shield, 24, 679, 10, 10.77),
        _text(
          '平台严禁涉黄、低俗、欺诈，如有发现请及时\n举报，平台会对其严肃警告或封号处理',
          38,
          676,
          247,
          34,
          12,
          17,
          const Color(0xFFA49A8C),
        ),
        Positioned(
          left: 14,
          top: 732,
          width: 189,
          height: 40,
          child: Semantics(
            button: true,
            label: '发送文字',
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onMessage,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.bottomLeft,
                    end: Alignment.topRight,
                    colors: [
                      Color(0x1CFFFFFF),
                      Color(0x06FFFFFF),
                      Color(0x0DC59B54)
                    ],
                    stops: [0, .56, 1],
                  ),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0x3DE8C77B), width: .6),
                ),
              ),
            ),
          ),
        ),
        const Positioned(
          left: 26,
          top: 743,
          width: 18,
          height: 18,
          child: CustomPaint(painter: _MessagePainter()),
        ),
        _text('不方便讲话，可以发文字', 50, 744, 138, 17, 12, 17, const Color(0xFF9B8B76)),
        Positioned(
          left: 212,
          top: 731,
          width: 40,
          height: 40,
          child: Semantics(
            button: true,
            label: '送礼物',
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onGift,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0x38FFFFFF),
                      Color(0x0DFFFFFF),
                      Color(0x1AC59B54)
                    ],
                  ),
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0x3DE8C77B), width: .5),
                ),
                child: Center(
                  child: Image.asset(
                    CallerRelationshipAssets.gift,
                    width: 16,
                    height: 16,
                    fit: BoxFit.fill,
                    filterQuality: FilterQuality.high,
                  ),
                ),
              ),
            ),
          ),
        ),
        Positioned(
          left: 121,
          top: 799,
          width: 134,
          height: 5,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(99),
            ),
          ),
        ),
      ],
    );
  }

  Widget _relationshipCard() {
    return Stack(
      children: [
        Positioned(
          left: 23,
          top: 178,
          width: 330,
          height: 420,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: BackdropFilter(
              filter: ui.ImageFilter.blur(sigmaX: 8, sigmaY: 8),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xD910131B),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0xFF604D3C), width: 1),
                  boxShadow: const [
                    BoxShadow(color: Color(0x1A171717), blurRadius: 15),
                  ],
                ),
              ),
            ),
          ),
        ),
        const Positioned(
          left: 46,
          top: 199,
          width: 18,
          height: 18,
          child: CustomPaint(painter: _RelationTitlePainter()),
        ),
        _text('关系详情', 71, 197, 90, 22, 16, 22, gold, weight: FontWeight.w600),
        Positioned(
          left: 314,
          top: 195,
          width: 24,
          height: 24,
          child: Semantics(
            button: true,
            label: '关闭关系详情',
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onClose,
              child: const CustomPaint(painter: _CardClosePainter()),
            ),
          ),
        ),
        _text('备注昵称', 44, 238, 56, 17, 12, 17, secondary),
        _text('大哥', 119, 236, 48, 20, 14, 20, Colors.white),
        _text('详细备注', 44, 265, 56, 17, 12, 17, secondary),
        _text('周末常聊，偏好语音陪伴', 119, 263, 190, 20, 14, 20, Colors.white),
        _text('关系标签', 44, 296, 56, 17, 12, 17, secondary),
        _pill(119, 292, 54, 22, '常聊', const Color(0xFFDCC7A6), 12),
        _pill(190, 292, 54, 22, '客户', const Color(0xFFDCC7A6), 12),
        _text('关系信息', 44, 328, 56, 17, 12, 17, secondary),
        _pill(118, 328, 46, 18, '生人', const Color(0xFFF2A48A), 10),
        _pill(174, 328, 58, 18, '我关注的', const Color(0xFF76B4FF), 10),
        const Positioned(
          left: 44,
          top: 354,
          width: 288,
          height: 1,
          child: ColoredBox(color: Color(0xFF2D2C2B)),
        ),
        _text('活跃时间段偏好', 44, 364, 120, 18, 13, 18, const Color(0xFFEAEBF0)),
        _text('近7天 · 各小时平均在线时长', 44, 384, 185, 16, 11, 16,
            const Color(0xFF91919B)),
        const Positioned(
          left: 44,
          top: 402,
          width: 288,
          height: 94,
          child: CustomPaint(painter: _ActivityChartPainter()),
        ),
        _text('0', 62, 482, 12, 14, 10, 14, const Color(0x99EAEBF0)),
        _text('12', 183, 482, 18, 14, 10, 14, const Color(0x99EAEBF0)),
        _text('24时', 305, 482, 26, 14, 10, 14, const Color(0x99EAEBF0)),
        Positioned(
          left: 44,
          top: 505,
          width: 288,
          height: 70,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xFF252527),
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
        _text('最近一次通话', 58, 521, 88, 16, 11, 16, const Color(0x99A6AAB5)),
        _text('近7天通话次数', 149, 521, 83, 16, 11, 16, const Color(0x99A6AAB5)),
        _text('累计通话时长', 250, 521, 75, 16, 11, 16, const Color(0x99A6AAB5)),
        _text('今天 10:15', 58, 543, 83, 20, 14, 20, chartGold,
            weight: FontWeight.w600),
        _text('3次', 175, 543, 42, 20, 14, 20, chartGold,
            weight: FontWeight.w600),
        _text('02：12', 261, 543, 60, 20, 14, 20, chartGold,
            weight: FontWeight.w600),
        Positioned(
          left: 58,
          top: 67,
          width: 72,
          height: 16,
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: onOpenRelation,
          ),
        ),
      ],
    );
  }

  Widget _pill(double x, double y, double width, double height, String value,
      Color color, double fontSize) {
    return Positioned(
      left: x,
      top: y,
      width: width,
      height: height,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0x0DFFFFFF),
          borderRadius: BorderRadius.circular(99),
          border: Border.all(color: const Color(0x14FFFFFF), width: .55),
        ),
        child: Center(
          child: Text(
            value,
            textScaler: TextScaler.noScaling,
            style: TextStyle(
              inherit: false,
              fontFamily: 'SourcePingFang',
              fontSize: fontSize,
              height: (fontSize + 5) / fontSize,
              color: color,
            ),
          ),
        ),
      ),
    );
  }

  static Widget _asset(
      String asset, double x, double y, double width, double height) {
    return Positioned(
      left: x,
      top: y,
      width: width,
      height: height,
      child: Image.asset(
        asset,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      ),
    );
  }

  static Widget _text(
    String value,
    double x,
    double y,
    double width,
    double height,
    double fontSize,
    double lineHeight,
    Color color, {
    FontWeight weight = FontWeight.w400,
    String family = 'SourcePingFang',
    List<Shadow>? shadows,
  }) {
    return Positioned(
      left: x,
      top: y,
      width: width,
      height: height,
      child: IgnorePointer(
        child: Text(
          value,
          softWrap: true,
          overflow: TextOverflow.visible,
          textScaler: TextScaler.noScaling,
          style: TextStyle(
            inherit: false,
            decoration: TextDecoration.none,
            fontFamily: family,
            fontSize: fontSize,
            height: lineHeight / fontSize,
            leadingDistribution: TextLeadingDistribution.even,
            fontWeight: weight,
            color: color,
            shadows: shadows,
          ),
        ),
      ),
    );
  }
}

class CallerRelationshipPage extends StatefulWidget {
  const CallerRelationshipPage({super.key});

  @override
  State<CallerRelationshipPage> createState() => _CallerRelationshipPageState();
}

class _CallerRelationshipPageState extends State<CallerRelationshipPage> {
  String mode = 'compare';
  double opacity = .5;
  String? eventText;

  Widget _source() => Image.asset(
        'assets/reference/caller_relationship.png',
        width: 375,
        height: 812,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );

  Widget _implementation() => CallerRelationshipScreen(
        onClose: () => setState(() => eventText = '已触发关闭 / 结束通话'),
        onMessage: () => setState(() => eventText = '已触发发送文字'),
        onGift: () => setState(() => eventText = '已触发送礼物'),
        onOpenRelation: () => setState(() => eventText = '已触发关系入口'),
      );

  Widget _panel(String label, String badge, Widget child) => SizedBox(
        width: 375,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                children: [
                  Expanded(
                    child: Text(label,
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                  ),
                  Text(badge,
                      style: const TextStyle(
                          fontSize: 11, color: Color(0xFF65717E))),
                ],
              ),
            ),
            DecoratedBox(
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFDDE1E6)),
                boxShadow: const [
                  BoxShadow(
                      color: Color(0x16000000),
                      blurRadius: 16,
                      offset: Offset(0, 6)),
                ],
              ),
              child: SizedBox(width: 375, height: 812, child: child),
            ),
          ],
        ),
      );

  Widget _row(List<Widget> panels) => LayoutBuilder(
        builder: (context, constraints) => SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: math.max(constraints.maxWidth, panels.length * 399 - 24),
            child: Wrap(
              alignment: WrapAlignment.center,
              spacing: 24,
              runSpacing: 24,
              children: panels,
            ),
          ),
        ),
      );

  Widget _result() {
    if (mode == 'compare') {
      return _row([
        _panel('蓝湖原稿', '固定版本 · 2×', _source()),
        _panel('Flutter 原生实现', '375 × 812', _implementation()),
      ]);
    }
    if (mode == 'source') {
      return _row([_panel('蓝湖原稿', '固定版本 · 2×', _source())]);
    }
    if (mode == 'flutter') {
      return _row([_panel('Flutter 原生实现', '375 × 812', _implementation())]);
    }
    return Column(
      children: [
        _row([
          _panel(
            '叠加：蓝湖 / Flutter',
            '原稿 ${(opacity * 100).round()}%',
            Stack(
              children: [
                _implementation(),
                IgnorePointer(
                    child: Opacity(opacity: opacity, child: _source())),
              ],
            ),
          ),
        ]),
        SizedBox(
          width: 375,
          child: Slider(
            key: const ValueKey('caller-overlay-opacity'),
            value: opacity,
            onChanged: (value) => setState(() => opacity = value),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('拨打方-1备份 2 · Flutter 还原')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 36),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('蓝湖固定快照 / Flutter 原生页面',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              const Text(
                '画布固定 375×812。关系卡片、曲线、文字、标签、状态栏和底部操作区均由 Flutter 绘制；蓝湖未提供可导出的实时视频位图，因此人物画面使用确定性占位，不计入视频像素验收。',
                style: TextStyle(color: Color(0xFF65717E), height: 1.55),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final item in const [
                    ('compare', '左右对比'),
                    ('source', '只看原稿'),
                    ('flutter', '只看 Flutter'),
                    ('overlay', '叠加对照'),
                  ])
                    ChoiceChip(
                      key: ValueKey('caller-mode-${item.$1}'),
                      label: Text(item.$2),
                      selected: mode == item.$1,
                      onSelected: (_) => setState(() => mode = item.$1),
                    ),
                ],
              ),
              if (eventText != null) ...[
                const SizedBox(height: 10),
                Text(eventText!,
                    style: const TextStyle(color: Color(0xFF137A52))),
              ],
              const SizedBox(height: 18),
              _result(),
            ],
          ),
        ),
      );
}

class _VideoPlaceholderPainter extends CustomPainter {
  const _VideoPlaceholderPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawRect(
      rect,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF8B836E), Color(0xFF615948), Color(0xFF24221F)],
          stops: [0, .48, 1],
        ).createShader(rect),
    );
    canvas.drawRect(
      const Rect.fromLTWH(0, 0, 175, 812),
      Paint()..color = const Color(0x337E7563),
    );
    canvas.drawOval(
      const Rect.fromLTWH(133, 73, 166, 178),
      Paint()..color = const Color(0xFF151514),
    );
    canvas.drawOval(
      const Rect.fromLTWH(159, 101, 126, 159),
      Paint()..color = const Color(0xFF72604F),
    );
    final body = Path()
      ..moveTo(95, 332)
      ..quadraticBezierTo(186, 276, 282, 339)
      ..lineTo(343, 812)
      ..lineTo(39, 812)
      ..close();
    canvas.drawPath(body, Paint()..color = const Color(0xFF20201F));
    canvas.drawPath(
      Path()
        ..moveTo(174, 320)
        ..lineTo(208, 320)
        ..lineTo(224, 812)
        ..lineTo(155, 812)
        ..close(),
      Paint()..color = const Color(0xFF2E2E2C),
    );
    for (final y in [600.0, 707.0]) {
      canvas.drawCircle(
          Offset(188, y), 6, Paint()..color = const Color(0xFF69665E));
    }
    canvas.drawRect(rect, Paint()..color = const Color(0x26000000));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _StatusPainter extends CustomPainter {
  const _StatusPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final white = Paint()..color = Colors.white;
    for (var i = 0; i < 4; i++) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(i * 4.65, 10 - i * 2.2, 3.0, 4 + i * 2.2),
          const Radius.circular(1),
        ),
        white,
      );
    }
    final wifi = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(23, 0, 15.33, 12), math.pi * 1.18,
        math.pi * .64, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(26, 4, 9.33, 7), math.pi * 1.18,
        math.pi * .64, false, wifi);
    canvas.drawCircle(const Offset(30.67, 10.5), 1.25, white);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(45.33, .33, 22, 11.33),
          const Radius.circular(2.5)),
      Paint()
        ..color = const Color(0x59FFFFFF)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(47.33, 2.33, 18, 7.33),
          const Radius.circular(1)),
      white,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(68.33, 4, 1.33, 4),
        const Radius.circular(.65),
      ),
      Paint()..color = const Color(0x99FFFFFF),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _RoundControlPainter extends CustomPainter {
  const _RoundControlPainter({required this.kind});
  final int kind;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawCircle(
      const Offset(16, 16),
      15.7,
      Paint()
        ..shader = const LinearGradient(
          colors: [Color(0x38FFFFFF), Color(0x0DFFFFFF), Color(0x1AC59B54)],
        ).createShader(rect),
    );
    canvas.drawCircle(
      const Offset(16, 16),
      15.7,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = .6
        ..color = const Color(0x40FFFFFF),
    );
    final icon = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..strokeWidth = 1.5;
    if (kind == 0) {
      canvas.drawLine(const Offset(10.5, 21.5), const Offset(15, 17), icon);
      canvas.drawLine(const Offset(15, 17), const Offset(15, 21), icon);
      canvas.drawLine(const Offset(15, 17), const Offset(11, 17), icon);
      canvas.drawLine(const Offset(17, 15), const Offset(21.5, 10.5), icon);
      canvas.drawLine(const Offset(17, 15), const Offset(17, 11), icon);
      canvas.drawLine(const Offset(17, 15), const Offset(21, 15), icon);
    } else if (kind == 1) {
      for (final x in [10.5, 16.0, 21.5]) {
        canvas.drawCircle(Offset(x, 16), 1.4, Paint()..color = Colors.white);
      }
    } else {
      canvas.drawLine(
          const Offset(11, 11), const Offset(21, 21), icon..strokeWidth = 2);
      canvas.drawLine(const Offset(21, 11), const Offset(11, 21), icon);
    }
  }

  @override
  bool shouldRepaint(covariant _RoundControlPainter oldDelegate) =>
      oldDelegate.kind != kind;
}

class _SwitchCameraPainter extends CustomPainter {
  const _SwitchCameraPainter();

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawCircle(
        const Offset(12, 12), 12, Paint()..color = const Color(0x45000000));
    final p = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(7, 8, 9, 8), const Radius.circular(2)),
      p,
    );
    canvas.drawArc(const Rect.fromLTWH(4, 5, 15, 15), math.pi * .75,
        math.pi * .75, false, p);
    canvas.drawArc(const Rect.fromLTWH(5, 4, 15, 15), -math.pi * .25,
        math.pi * .75, false, p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _RelationTitlePainter extends CustomPainter {
  const _RelationTitlePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFFEFD29B), Color(0xFFAE8336)],
      ).createShader(Offset.zero & size)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round;
    const points = [Offset(9, 3), Offset(4, 12.5), Offset(14, 12.5)];
    canvas.drawLine(points[0], points[1], stroke);
    canvas.drawLine(points[1], points[2], stroke);
    canvas.drawLine(points[2], points[0], stroke);
    final fill = Paint()..shader = stroke.shader;
    for (final point in points) {
      canvas.drawCircle(point, 2.15, fill);
      canvas.drawCircle(point, 2.8, stroke);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _CardClosePainter extends CustomPainter {
  const _CardClosePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = const Color(0xFF5B544E)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(const Offset(7, 7), const Offset(17, 17), p);
    canvas.drawLine(const Offset(17, 7), const Offset(7, 17), p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ActivityChartPainter extends CustomPainter {
  const _ActivityChartPainter();

  static const points = <Offset>[
    Offset(20.143, 71.029),
    Offset(39.613, 71.029),
    Offset(64.5, 58),
    Offset(92, 58),
    Offset(109, 46),
    Offset(125.5, 35),
    Offset(152, 46),
    Offset(175.5, 35),
    Offset(196, 35),
    Offset(208, 19.922),
    Offset(241, 13.863),
    Offset(266.613, 1.883),
    Offset(288, 19.922),
  ];

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawLine(
      const Offset(0, 73.266),
      Offset(size.width, 73.266),
      Paint()
        ..color = const Color(0x45979797)
        ..strokeWidth = .5,
    );
    final line = Path()..moveTo(points.first.dx, points.first.dy);
    for (final point in points.skip(1)) {
      line.lineTo(point.dx, point.dy);
    }
    final area = Path()
      ..moveTo(0, 71.029)
      ..lineTo(points.first.dx, points.first.dy);
    for (final point in points.skip(1)) {
      area.lineTo(point.dx, point.dy);
    }
    area
      ..lineTo(size.width, 75.532)
      ..lineTo(0, 75.532)
      ..close();
    canvas.drawPath(
      area,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xC98C5F35), Color(0x006B3D16)],
        ).createShader(Offset.zero & size),
    );
    canvas.drawPath(
      line,
      Paint()
        ..color = const Color(0xFFE8C77B)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..strokeJoin = StrokeJoin.round,
    );
    for (final point in points.take(points.length - 1).skip(1)) {
      canvas.drawCircle(
        point,
        2.5,
        Paint()
          ..color = const Color(0xFFFFEFB7)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2.5),
      );
      canvas.drawCircle(
        point,
        1.75,
        Paint()..color = const Color(0xFFFFEFB7),
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MessagePainter extends CustomPainter {
  const _MessagePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawCircle(
      const Offset(9, 9),
      9,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFFFFE5C3), Color(0xFFBC914A)],
        ).createShader(rect),
    );
    canvas.drawOval(const Rect.fromLTWH(3.4, 7.7, 2, 2),
        Paint()..color = const Color(0xFF18181B));
    canvas.drawOval(const Rect.fromLTWH(8, 7.7, 2, 2),
        Paint()..color = const Color(0xFF18181B));
    canvas.drawOval(const Rect.fromLTWH(12.6, 7.7, 2, 2),
        Paint()..color = const Color(0xFF18181B));
    final tail = Path()
      ..moveTo(12, 15)
      ..lineTo(15.5, 17)
      ..lineTo(15, 13)
      ..close();
    canvas.drawPath(tail, Paint()..color = const Color(0xFFBC914A));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
