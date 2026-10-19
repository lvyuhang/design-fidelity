import 'package:flutter/material.dart';

class PlatformIntroOptimizedAssets {
  static const root = 'assets/lanhu/full_page/';
  static const all = <String>[
    '${root}hero.png',
    '${root}title_art.png',
    '${root}capability_badge.png',
    '${root}capability_1.png',
    '${root}capability_2.png',
    '${root}capability_3.png',
    '${root}capability_4.png',
    '${root}reward_badge.png',
    '${root}reward_1.png',
    '${root}reward_2.png',
    '${root}reward_3.png',
  ];
}

class PlatformIntroOptimizedPage extends StatelessWidget {
  const PlatformIntroOptimizedPage({super.key, this.onSkip, this.onStart});

  static const designSize = Size(375, 812);
  final VoidCallback? onSkip;
  final VoidCallback? onStart;

  static const _ink = Color(0xFF1E2026);
  static const _muted = Color(0xFF9FA3AD);
  static const _gold = Color(0xFFE0AF55);

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 375,
        height: 812,
        child: ClipRect(
          child: ColoredBox(
            color: Colors.white,
            child: Stack(children: [
              const Positioned(
                left: 0,
                top: 0,
                width: 375,
                height: 230,
                child: Image(
                  image: AssetImage(
                      '${PlatformIntroOptimizedAssets.root}hero.png'),
                  fit: BoxFit.fill,
                ),
              ),
              const Positioned(
                left: 19,
                top: 57.18,
                width: 205,
                height: 119,
                child: Image(
                  image: AssetImage(
                      '${PlatformIntroOptimizedAssets.root}title_art.png'),
                  fit: BoxFit.fill,
                ),
              ),
              _statusBar(),
              Positioned(
                left: 306,
                top: 42,
                width: 53,
                height: 38,
                child: GestureDetector(
                  key: const ValueKey('platform-optimized-skip'),
                  behavior: HitTestBehavior.opaque,
                  onTap: onSkip,
                  child: const Center(
                    child: Text('跳过',
                        textScaler: TextScaler.noScaling,
                        style: TextStyle(
                            inherit: false,
                            fontFamily: 'SourcePingFang',
                            fontSize: 14,
                            height: 20 / 14,
                            fontWeight: FontWeight.w500,
                            color: Color(0xFFC08B39))),
                  ),
                ),
              ),
              _capabilitySection(),
              _benefitSection(),
              Positioned(
                left: 16,
                top: 714,
                width: 343,
                height: 50,
                child: GestureDetector(
                  key: const ValueKey('platform-optimized-start'),
                  behavior: HitTestBehavior.opaque,
                  onTap: onStart,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                          colors: [
                            Color(0xFF111111),
                            Color(0xFF372D22),
                          ],
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight),
                      borderRadius: BorderRadius.circular(25),
                      border:
                          Border.all(color: const Color(0x66D6A44A), width: 1),
                      boxShadow: const [
                        BoxShadow(
                            color: Color(0x1AD6A44A),
                            blurRadius: 14,
                            offset: Offset(0, 8)),
                      ],
                    ),
                    child: const Center(
                      child: Text('开始入驻',
                          textScaler: TextScaler.noScaling,
                          style: TextStyle(
                              inherit: false,
                              fontFamily: 'SourcePingFang',
                              fontSize: 15,
                              height: 21 / 15,
                              fontWeight: FontWeight.w600,
                              color: _gold)),
                    ),
                  ),
                ),
              ),
              const Positioned(
                left: 121,
                top: 799,
                width: 134,
                height: 5,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: Colors.black,
                    borderRadius: BorderRadius.all(Radius.circular(99)),
                  ),
                ),
              ),
            ]),
          ),
        ),
      );

  Widget _statusBar() => Stack(children: [
        _text('9:41', 21, 14.33, 54, 18, 15, 18, Colors.black,
            align: TextAlign.center),
        const Positioned(
          left: 294,
          top: 17,
          width: 67,
          height: 12,
          child: CustomPaint(painter: _StatusPainter()),
        ),
      ]);

  Widget _capabilitySection() => Positioned(
        left: 15,
        top: 208,
        width: 343,
        height: 208,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment(0, -.7273469),
              colors: [Color(0xA3FFFFFF), Color(0xFFFEFDFB)],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFFFFAFA), width: 1),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x26DDAA5A),
                  blurRadius: 12,
                  offset: Offset(0, 6)),
            ],
          ),
          child: Stack(children: [
            const Positioned(
              left: 9,
              top: 10,
              width: 38.75,
              height: 38.75,
              child: Image(
                  image: AssetImage(
                      '${PlatformIntroOptimizedAssets.root}capability_badge.png')),
            ),
            _text('平台能力介绍', 46, 16, 96, 22, 16, 22, _ink,
                weight: FontWeight.w600),
            _capabilityCard(11, 55, 156.18, 65, 'capability_1.png', '内容创作',
                '支持图文、短视频类\n内容创作',
                titleTop: 8, descriptionTop: 26),
            _capabilityCard(
                175.82, 55, 156.18, 65, 'capability_2.png', '智能推荐', '快速积累关系人',
                iconLeft: 8, textLeft: 44, titleTop: 14, descriptionTop: 34),
            _capabilityCard(
                11, 130, 156.18, 65, 'capability_3.png', '任务互动', '拉近关系人距离',
                titleTop: 16, descriptionTop: 34),
            _capabilityCard(
                175.82, 130, 156.18, 65, 'capability_4.png', '关系维护', '助力关系持续发展',
                iconLeft: 8, textLeft: 44, titleTop: 16, descriptionTop: 34),
            const _MissingSourceAsset(
              left: 157,
              top: 12,
              width: 15,
              height: 13,
              semanticLabel: '平台标题引号素材未切',
            ),
            const _MissingSourceAsset(
              left: 276,
              top: 0,
              width: 60,
              height: 58,
              semanticLabel: '平台标题01装饰字体未提供',
              showLabel: true,
            ),
          ]),
        ),
      );

  Widget _capabilityCard(double x, double y, double w, double h, String icon,
          String title, String description,
          {double iconLeft = 10,
          double textLeft = 46,
          double titleTop = 8,
          double descriptionTop = 26}) =>
      Positioned(
        left: x,
        top: y,
        width: w,
        height: h,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0x4DFFF8EF),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFFFF3E2), width: 1),
          ),
          child: Stack(children: [
            Positioned(
              left: iconLeft,
              top: (h - 30) / 2,
              width: 30,
              height: 30,
              child: Image(
                  image:
                      AssetImage('${PlatformIntroOptimizedAssets.root}$icon')),
            ),
            _text(title, textLeft, titleTop, w - textLeft - 6, 17, 12, 17, _ink,
                weight: FontWeight.w600),
            _text(description, textLeft, descriptionTop, w - textLeft - 4,
                h - descriptionTop, 11, 16, const Color(0xFF858A96)),
          ]),
        ),
      );

  Widget _benefitSection() => Positioned(
        left: 16,
        top: 424,
        width: 343,
        height: 266,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment(-.039723, 1),
              colors: [Color(0xFF1C1C1A), Color(0xFFE8C17B)],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFFFFAFA), width: 1),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x26DDAA5A),
                  blurRadius: 12,
                  offset: Offset(0, 5)),
            ],
          ),
          child: Stack(children: [
            const Positioned(
              left: 7,
              top: 9,
              width: 38.75,
              height: 38.75,
              child: Image(
                  image: AssetImage(
                      '${PlatformIntroOptimizedAssets.root}reward_badge.png')),
            ),
            _text('创作者获得的收益', 46, 15, 128, 22, 16, 22, const Color(0xFFE2B75C),
                weight: FontWeight.w600),
            Positioned(
              left: 10,
              top: 47,
              width: 325,
              height: 210,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Color(0xFFFFFFFF), Color(0xFFFFFCF7)],
                  ),
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: const [
                    BoxShadow(
                        color: Color(0x1ADDAA5A),
                        blurRadius: 12,
                        offset: Offset(0, 5)),
                  ],
                ),
                child: Stack(children: [
                  _rewardRow(0, 'reward_1.png', '多平台分发', '一次创作，自动分发至多个平台'),
                  _rewardRow(72, 'reward_2.png', '多样任务', '满足不同能力需求'),
                  _rewardRow(140, 'reward_3.png', '任务奖励', '提升持续成长动力'),
                  const Positioned(
                    left: 4,
                    top: 69,
                    width: 316,
                    height: .5,
                    child: ColoredBox(color: Color(0xFFFFEBD0)),
                  ),
                  const Positioned(
                    left: 4,
                    top: 140,
                    width: 316,
                    height: .5,
                    child: ColoredBox(color: Color(0xFFFFEBD0)),
                  ),
                ]),
              ),
            ),
            const _MissingSourceAsset(
              left: 183,
              top: 11,
              width: 15,
              height: 13,
              semanticLabel: '收益标题引号素材未切',
            ),
            const _MissingSourceAsset(
              left: 265,
              top: 0,
              width: 78,
              height: 67,
              semanticLabel: '收益标题02与星光素材未切',
              showLabel: true,
            ),
          ]),
        ),
      );

  Widget _rewardRow(double y, String icon, String title, String description) =>
      Positioned(
        left: 0,
        top: y,
        width: 325,
        height: y == 0 ? 72 : 68,
        child: Stack(children: [
          Positioned(
            left: -1,
            top: 11,
            width: 63,
            height: 63,
            child: Image(
                image: AssetImage('${PlatformIntroOptimizedAssets.root}$icon')),
          ),
          _text(title, 60, 17, 150, 20, 14, 20, _ink, weight: FontWeight.w500),
          _text(description, 60, 37, 220, 18, 12, 17, _muted),
        ]),
      );

  static Widget _text(String value, double x, double y, double w, double h,
          double size, double line, Color color,
          {FontWeight weight = FontWeight.w400,
          TextAlign align = TextAlign.left}) =>
      Positioned(
        left: x,
        top: y,
        width: w,
        height: h,
        child: Text(value,
            textScaler: TextScaler.noScaling,
            textAlign: align,
            overflow: TextOverflow.visible,
            style: TextStyle(
                inherit: false,
                decoration: TextDecoration.none,
                fontFamily: 'SourcePingFang',
                fontSize: size,
                height: line / size,
                fontWeight: weight,
                color: color)),
      );
}

class _MissingSourceAsset extends StatelessWidget {
  const _MissingSourceAsset({
    required this.left,
    required this.top,
    required this.width,
    required this.height,
    required this.semanticLabel,
    this.showLabel = false,
  });

  final double left;
  final double top;
  final double width;
  final double height;
  final String semanticLabel;
  final bool showLabel;

  @override
  Widget build(BuildContext context) => Positioned(
        left: left,
        top: top,
        width: width,
        height: height,
        child: Semantics(
          label: semanticLabel,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0x1AFF4770),
              border: Border.all(color: const Color(0xFFFF4770), width: .75),
              borderRadius: BorderRadius.circular(2),
            ),
            child: showLabel
                ? const Center(
                    child: Text(
                      '缺',
                      textScaler: TextScaler.noScaling,
                      style: TextStyle(
                        inherit: false,
                        fontFamily: 'SourcePingFang',
                        fontSize: 9,
                        height: 1,
                        color: Color(0xFFFF4770),
                      ),
                    ),
                  )
                : null,
          ),
        ),
      );
}

class _StatusPainter extends CustomPainter {
  const _StatusPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.5, 9 - i * 2.2, 3.3, 3 + i * 2.2),
              const Radius.circular(1)),
          black);
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(29, 0, 16, 14), 3.75, 1.92, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(33, 4, 8, 8), 3.75, 1.92, false, wifi);
    canvas.drawCircle(const Offset(37, 11), 1.2, black);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(51, 1, 15, 10), const Radius.circular(2)),
        Paint()
          ..color = Colors.black
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.2);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(53, 3, 11, 6), const Radius.circular(1)),
        black);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
