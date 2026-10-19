import 'dart:math' as math;

import 'package:flutter/material.dart';

class Sol56PlatformIntroPageR2 extends StatelessWidget {
  const Sol56PlatformIntroPageR2({
    super.key,
    this.onSkip,
    this.onStart,
  });

  final VoidCallback? onSkip;
  final VoidCallback? onStart;

  static const String _assetRoot = 'assets/lanhu/full_page';

  static const TextStyle _capabilityTitleStyle = TextStyle(
    color: Color(0xFF22242A),
    fontFamily: 'SourcePingFang',
    fontSize: 12,
    fontWeight: FontWeight.w600,
    height: 17 / 12,
  );

  static const TextStyle _capabilityBodyStyle = TextStyle(
    color: Color(0xFF686B77),
    fontFamily: 'SourcePingFang',
    fontSize: 11,
    fontWeight: FontWeight.w400,
    height: 16 / 11,
  );

  static const TextStyle _rewardTitleStyle = TextStyle(
    color: Color(0xFF22242A),
    fontFamily: 'SourcePingFang',
    fontSize: 14,
    fontWeight: FontWeight.w600,
    height: 20 / 14,
  );

  static const TextStyle _rewardBodyStyle = TextStyle(
    color: Color(0xFFA6AAB5),
    fontFamily: 'SourcePingFang',
    fontSize: 12,
    fontWeight: FontWeight.w400,
    height: 17 / 12,
  );

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      child: SizedBox(
        width: 375,
        height: 812,
        child: ClipRect(
          child: Stack(
            fit: StackFit.expand,
            children: [
              const ColoredBox(color: Colors.white),
              _asset(
                'hero.png',
                left: 0,
                top: 0,
                width: 375,
                height: 229,
              ),
              _asset(
                'title_art.png',
                left: 19,
                top: 57.183,
                width: 205,
                height: 118.817,
              ),
              const Positioned(
                left: 15,
                top: 208,
                width: 343,
                height: 208,
                child: _CapabilityPanel(),
              ),
              const Positioned(
                left: 26,
                top: 263,
                width: 156.181,
                height: 65,
                child: _CapabilityTile(),
              ),
              const Positioned(
                left: 190.819,
                top: 263,
                width: 156.181,
                height: 65,
                child: _CapabilityTile(),
              ),
              const Positioned(
                left: 26,
                top: 338,
                width: 156.181,
                height: 65,
                child: _CapabilityTile(),
              ),
              const Positioned(
                left: 190.819,
                top: 338,
                width: 156.181,
                height: 65,
                child: _CapabilityTile(subdued: true),
              ),
              _asset(
                'capability_badge.png',
                left: 23.625,
                top: 218.375,
                width: 38.75,
                height: 38.75,
              ),
              const Positioned(
                left: 59.8,
                top: 224,
                child: Text(
                  '平台能力介绍',
                  style: TextStyle(
                    color: Color(0xFF22242A),
                    fontFamily: 'SourcePingFang',
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    height: 22 / 16,
                  ),
                ),
              ),
              const Positioned(
                left: 171,
                top: 216,
                child: Text(
                  '”',
                  style: TextStyle(
                    color: Color(0xFFFAEFDF),
                    fontFamily: 'SourcePingFang',
                    fontSize: 27,
                    fontWeight: FontWeight.w600,
                    height: 1,
                  ),
                ),
              ),
              const Positioned(
                left: 288,
                top: 206,
                child: Text(
                  '01',
                  style: TextStyle(
                    color: Color(0xFFFBF6ED),
                    fontFamily: 'SourcePingFang',
                    fontSize: 58,
                    fontWeight: FontWeight.w600,
                    fontStyle: FontStyle.italic,
                    height: 1,
                  ),
                ),
              ),
              _asset(
                'capability_1.png',
                left: 36,
                top: 281,
                width: 30,
                height: 30,
              ),
              _asset(
                'capability_2.png',
                left: 199,
                top: 281,
                width: 30,
                height: 30,
              ),
              _asset(
                'capability_3.png',
                left: 36,
                top: 355,
                width: 30,
                height: 30,
              ),
              _asset(
                'capability_4.png',
                left: 199,
                top: 355,
                width: 30,
                height: 30,
              ),
              const Positioned(
                left: 70.9,
                top: 271,
                child: Text('内容创作', style: _capabilityTitleStyle),
              ),
              const Positioned(
                left: 70.9,
                top: 289,
                width: 102,
                child: Text(
                  '支持图文、短视频类\n内容创作',
                  style: _capabilityBodyStyle,
                ),
              ),
              const Positioned(
                left: 234.2,
                top: 277,
                child: Text('智能推荐', style: _capabilityTitleStyle),
              ),
              const Positioned(
                left: 234.2,
                top: 297,
                child: Text('快速积累关系人', style: _capabilityBodyStyle),
              ),
              const Positioned(
                left: 70.5,
                top: 354,
                child: Text('任务互动', style: _capabilityTitleStyle),
              ),
              const Positioned(
                left: 70.5,
                top: 372,
                child: Text('拉近关系人距离', style: _capabilityBodyStyle),
              ),
              const Positioned(
                left: 233.7,
                top: 354,
                child: Text('关系维护', style: _capabilityTitleStyle),
              ),
              const Positioned(
                left: 233.7,
                top: 372,
                child: Text('助力关系持续发展', style: _capabilityBodyStyle),
              ),
              const Positioned(
                left: 16,
                top: 424,
                width: 343,
                height: 266,
                child: _RewardPanel(),
              ),
              const Positioned(
                left: 26,
                top: 471,
                width: 325,
                height: 210,
                child: _RewardInnerCard(),
              ),
              const Positioned(
                left: 199,
                top: 431,
                child: Text(
                  '”',
                  style: TextStyle(
                    color: Color(0xFFE8C77B),
                    fontFamily: 'SourcePingFang',
                    fontSize: 27,
                    fontWeight: FontWeight.w600,
                    height: 1,
                  ),
                ),
              ),
              const Positioned(
                left: 278,
                top: 421,
                child: Text(
                  '02',
                  style: TextStyle(
                    color: Color(0x2EE8C77B),
                    fontFamily: 'SourcePingFang',
                    fontSize: 58,
                    fontWeight: FontWeight.w600,
                    fontStyle: FontStyle.italic,
                    height: 1,
                  ),
                ),
              ),
              _asset(
                'reward_badge.png',
                left: 23.625,
                top: 433.25,
                width: 38.75,
                height: 38.75,
              ),
              const Positioned(
                left: 61.3,
                top: 439,
                child: Text(
                  '创作者获得的收益',
                  style: TextStyle(
                    color: Color(0xFFE8C77B),
                    fontFamily: 'SourcePingFang',
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    height: 22 / 16,
                  ),
                ),
              ),
              _asset(
                'reward_1.png',
                left: 25,
                top: 482,
                width: 63,
                height: 63,
              ),
              _asset(
                'reward_2.png',
                left: 25,
                top: 554,
                width: 63,
                height: 63,
              ),
              _asset(
                'reward_3.png',
                left: 25,
                top: 621,
                width: 63,
                height: 63,
              ),
              const Positioned(
                left: 83.3,
                top: 488,
                child: Text('多平台分发', style: _rewardTitleStyle),
              ),
              const Positioned(
                left: 83.3,
                top: 508,
                child: Text(
                  '一次创作，自动分发至多个平台',
                  style: _rewardBodyStyle,
                ),
              ),
              const Positioned(
                left: 84.2,
                top: 559,
                child: Text('多样任务', style: _rewardTitleStyle),
              ),
              const Positioned(
                left: 84.2,
                top: 578,
                child: Text('满足不同能力需求', style: _rewardBodyStyle),
              ),
              const Positioned(
                left: 84.9,
                top: 627,
                child: Text('任务奖励', style: _rewardTitleStyle),
              ),
              const Positioned(
                left: 84.9,
                top: 646,
                child: Text('提升持续成长动力', style: _rewardBodyStyle),
              ),
              Positioned(
                left: 16,
                top: 714,
                width: 343,
                height: 50,
                child: _StartButton(onTap: onStart),
              ),
              Positioned(
                left: 315,
                top: 43,
                width: 44,
                height: 36,
                child: Semantics(
                  button: true,
                  label: '跳过',
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: onSkip,
                      borderRadius: BorderRadius.circular(18),
                      child: const Align(
                        alignment: Alignment.center,
                        child: Text(
                          '跳过',
                          style: TextStyle(
                            color: Color(0xFFB27A31),
                            fontFamily: 'SourcePingFang',
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            height: 20 / 14,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const Positioned(
                left: 0,
                top: 0,
                width: 375,
                height: 44,
                child: IgnorePointer(child: _StatusBar()),
              ),
              const Positioned(
                left: 121,
                top: 799,
                width: 134,
                height: 5,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: Colors.black,
                    borderRadius: BorderRadius.all(Radius.circular(100)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  static Widget _asset(
    String name, {
    required double left,
    required double top,
    required double width,
    required double height,
  }) {
    return Positioned(
      left: left,
      top: top,
      width: width,
      height: height,
      child: Image.asset(
        '$_assetRoot/$name',
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      ),
    );
  }
}

class _CapabilityPanel extends StatelessWidget {
  const _CapabilityPanel();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xA3FFFFFF), Color(0xFFFEFDFB)],
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFFFAFA)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x26DDAA5A),
            offset: Offset(0, 6),
            blurRadius: 12,
          ),
        ],
      ),
    );
  }
}

class _CapabilityTile extends StatelessWidget {
  const _CapabilityTile({this.subdued = false});

  final bool subdued;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: subdued ? const Color(0x33FFF8EF) : const Color(0x4DFFF8EF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: subdued ? const Color(0xFFFCF7F0) : const Color(0xFFFFF3E2),
        ),
      ),
    );
  }
}

class _RewardPanel extends StatelessWidget {
  const _RewardPanel();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF1C1C1A), Color(0xFFE8C17B)],
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFFFAFA)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x26DDAA5A),
            offset: Offset(0, 5),
            blurRadius: 12,
          ),
        ],
      ),
      child: const ClipRRect(
        borderRadius: BorderRadius.all(Radius.circular(13)),
        child: CustomPaint(painter: _RewardSparklePainter()),
      ),
    );
  }
}

class _RewardInnerCard extends StatelessWidget {
  const _RewardInnerCard();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.white, Color(0xFFFFFCF7)],
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1ADDAA5A),
            offset: Offset(0, 5),
            blurRadius: 12,
          ),
        ],
      ),
      child: Stack(
        children: const [
          Positioned(
            left: 4,
            top: 69,
            width: 316,
            height: 1,
            child: ColoredBox(color: Color(0xFFFBEFE1)),
          ),
          Positioned(
            left: 4,
            top: 140,
            width: 316,
            height: 1,
            child: ColoredBox(color: Color(0xFFFBEFE1)),
          ),
        ],
      ),
    );
  }
}

class _StartButton extends StatelessWidget {
  const _StartButton({required this.onTap});

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: '开始入驻',
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
            colors: [Color(0xFF111111), Color(0xFF372D22)],
          ),
          borderRadius: BorderRadius.circular(25),
          border: Border.all(color: const Color(0x66D6A44A)),
          boxShadow: const [
            BoxShadow(
              color: Color(0x1AD6A44A),
              offset: Offset(0, 8),
              blurRadius: 14,
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(25),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(25),
            child: const Center(
              child: Text(
                '开始入驻',
                style: TextStyle(
                  color: Color(0xFFE6B55E),
                  fontFamily: 'SourcePingFang',
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  height: 21 / 15,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _StatusBar extends StatelessWidget {
  const _StatusBar();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: const [
        Positioned(
          left: 21,
          top: 14.333,
          width: 54,
          height: 18,
          child: Text(
            '9:41',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.black,
              fontFamily: 'SourcePingFang',
              fontSize: 15,
              fontWeight: FontWeight.w600,
              letterSpacing: -0.3,
              height: 18 / 15,
            ),
          ),
        ),
        Positioned(
          left: 294,
          top: 17,
          width: 67,
          height: 12,
          child: CustomPaint(painter: _StatusIconsPainter()),
        ),
      ],
    );
  }
}

class _StatusIconsPainter extends CustomPainter {
  const _StatusIconsPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final fill = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.fill;

    const barWidth = 3.2;
    const gap = 1.6;
    for (var index = 0; index < 4; index++) {
      final height = 4.5 + index * 2.1;
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(
              index * (barWidth + gap), 12 - height, barWidth, height),
          const Radius.circular(0.8),
        ),
        fill,
      );
    }

    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2
      ..strokeCap = StrokeCap.round;
    const center = Offset(31.8, 9.9);
    for (final radius in [9.0, 6.0, 3.0]) {
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        math.pi * 1.18,
        math.pi * 0.64,
        false,
        wifi,
      );
    }
    canvas.drawCircle(const Offset(31.8, 10.3), 1.2, fill);

    final batteryStroke = Paint()
      ..color = const Color(0x59000000)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(42.3, 0.3, 22, 11.3),
        const Radius.circular(2),
      ),
      batteryStroke,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(44.3, 2.3, 18, 7.3),
        const Radius.circular(1),
      ),
      fill,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(65.2, 3.7, 1.3, 4),
        const Radius.circular(0.7),
      ),
      Paint()..color = const Color(0x59000000),
    );
  }

  @override
  bool shouldRepaint(covariant _StatusIconsPainter oldDelegate) => false;
}

class _RewardSparklePainter extends CustomPainter {
  const _RewardSparklePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final soft = Paint()..color = const Color(0x55F8D98E);
    final bright = Paint()..color = const Color(0xCCEEC66F);
    canvas.drawCircle(const Offset(318, 18), 14, soft);
    canvas.drawCircle(const Offset(318, 18), 4, bright);
    canvas.drawCircle(const Offset(296, 26), 1.4, bright);
    canvas.drawCircle(const Offset(329, 38), 1.1, bright);
    canvas.drawCircle(const Offset(286, 11), 0.8, bright);
    canvas.drawCircle(const Offset(307, 8), 0.7, bright);
    final rays = Paint()
      ..color = const Color(0x99FFE4A0)
      ..strokeWidth = 1;
    canvas.drawLine(const Offset(318, 0), const Offset(318, 36), rays);
    canvas.drawLine(const Offset(300, 18), const Offset(336, 18), rays);
  }

  @override
  bool shouldRepaint(covariant _RewardSparklePainter oldDelegate) => false;
}
