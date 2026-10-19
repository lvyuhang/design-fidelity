import 'package:flutter/material.dart';

/// The 375 × 812 platform introduction artboard exported from Lanhu.
class Gpt6PlatformIntroPage extends StatelessWidget {
  const Gpt6PlatformIntroPage({
    super.key,
    this.onSkip,
    this.onStart,
  });

  final VoidCallback? onSkip;
  final VoidCallback? onStart;

  static const _assetRoot = 'assets/lanhu/full_page/';
  static const _ink = Color(0xFF22242A);
  static const _body = Color(0xFF686B77);
  static const _muted = Color(0xFFA6AAB5);
  static const _gold = Color(0xFFE6B55E);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: SizedBox(
          width: 375,
          height: 812,
          child: Stack(
            clipBehavior: Clip.hardEdge,
            children: [
              const Positioned.fill(child: ColoredBox(color: Colors.white)),
              _image('hero.png', 0, 0, 375, 229),
              _image('title_art.png', 19, 57.183, 205, 118.817),
              _capabilityCard(),
              _rewardCard(),
              _cta(),
              _statusBar(),
              Positioned(
                left: 315,
                top: 43,
                width: 46,
                height: 37,
                child: Semantics(
                  button: true,
                  label: '跳过',
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: onSkip,
                    child: const Center(
                      child: Text(
                        '跳过',
                        style: TextStyle(
                          fontFamily: 'SourcePingFang',
                          fontSize: 14,
                          height: 20 / 14,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFFB27A31),
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
                    color: Colors.black,
                    borderRadius: BorderRadius.circular(100),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _capabilityCard() {
    return Stack(
      children: [
        Positioned(
          left: 15,
          top: 208,
          width: 343,
          height: 208,
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0xA3FFFFFF), Color(0xFFFEFDFB)],
              ),
              border: Border.all(color: const Color(0xFFFFFAFA)),
              borderRadius: BorderRadius.circular(14),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x26DDAA5A),
                  offset: Offset(0, 6),
                  blurRadius: 12,
                ),
              ],
            ),
          ),
        ),
        _decorativeNumber('01', 287, 204, 65, 64, const Color(0x19D8B37C)),
        _quote(172, 214, const Color(0x2BEBC588)),
        _image('capability_badge.png', 26, 218, 34, 34),
        _text('平台能力介绍', 61, 224, 110, 22, 16, 22, _ink,
            weight: FontWeight.w600),
        _capabilityTile(26, 263),
        _capabilityTile(190.819, 263),
        _capabilityTile(26, 338),
        _capabilityTile(190.819, 338, last: true),
        _image('capability_1.png', 36, 281, 30, 30),
        _image('capability_2.png', 199, 281, 30, 30),
        _image('capability_3.png', 36, 355, 30, 30),
        _image('capability_4.png', 199, 355, 30, 30),
        _text('内容创作', 72, 271, 108, 17, 12, 17, _ink, weight: FontWeight.w600),
        _text('支持图文、短视频类内容创作', 72, 289, 102, 32, 11, 16, _body, maxLines: 2),
        _text('智能推荐', 235, 277, 108, 17, 12, 17, _ink, weight: FontWeight.w600),
        _text('快速积累关系人', 235, 297, 108, 16, 11, 16, _body),
        _text('任务互动', 72, 354, 108, 17, 12, 17, _ink, weight: FontWeight.w600),
        _text('拉近关系人距离', 72, 372, 108, 16, 11, 16, _body),
        _text('关系维护', 235, 354, 108, 17, 12, 17, _ink, weight: FontWeight.w600),
        _text('助力关系持续发展', 235, 372, 108, 16, 11, 16, _body),
      ],
    );
  }

  Widget _capabilityTile(double x, double y, {bool last = false}) {
    return Positioned(
      left: x,
      top: y,
      width: 156.181,
      height: 65,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: last ? const Color(0x33FFF8EF) : const Color(0x4DFFF8EF),
          border: Border.all(
            color: last ? const Color(0xFFFCF7F0) : const Color(0xFFFFF3E2),
          ),
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }

  Widget _rewardCard() {
    return Stack(
      children: [
        Positioned(
          left: 16,
          top: 424,
          width: 343,
          height: 266,
          child: DecoratedBox(
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
          ),
        ),
        _decorativeNumber('02', 279, 420, 70, 68, const Color(0x45D9B974)),
        _quote(199, 429, const Color(0x50E8C17B)),
        Positioned(
          left: 325,
          top: 435,
          child:
              Icon(Icons.auto_awesome, size: 23, color: _gold.withOpacity(.5)),
        ),
        _image('reward_badge.png', 26, 433, 34, 34),
        _text('创作者获得的收益', 62, 439, 160, 22, 16, 22, const Color(0xFFE8C77B),
            weight: FontWeight.w600),
        Positioned(
          left: 26,
          top: 471,
          width: 325,
          height: 210,
          child: DecoratedBox(
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
          ),
        ),
        _image('reward_1.png', 35, 486, 43, 43),
        _image('reward_2.png', 35, 558, 43, 43),
        _image('reward_3.png', 35, 625, 43, 43),
        _text('多平台分发', 86, 488, 170, 20, 14, 20, _ink, weight: FontWeight.w600),
        _text('一次创作，自动分发至多个平台', 86, 508, 230, 17, 12, 17, _muted),
        _divider(540),
        _text('多样任务', 86, 559, 170, 20, 14, 20, _ink, weight: FontWeight.w600),
        _text('满足不同能力需求', 86, 578, 230, 17, 12, 17, _muted),
        _divider(611),
        _text('任务奖励', 86, 627, 170, 20, 14, 20, _ink, weight: FontWeight.w600),
        _text('提升持续成长动力', 86, 646, 230, 17, 12, 17, _muted),
      ],
    );
  }

  Widget _divider(double y) => Positioned(
        left: 30,
        top: y,
        width: 316,
        height: 1,
        child: const ColoredBox(color: Color(0xFFFBEFE1)),
      );

  Widget _cta() {
    return Positioned(
      left: 16,
      top: 714,
      width: 343,
      height: 50,
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
        child: Semantics(
          button: true,
          label: '开始入驻',
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: onStart,
            child: const Center(
              child: Text(
                '开始入驻',
                style: TextStyle(
                  fontFamily: 'SourcePingFang',
                  fontSize: 15,
                  height: 21 / 15,
                  fontWeight: FontWeight.w600,
                  color: _gold,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _statusBar() {
    return Stack(
      children: [
        _text('9:41', 21, 14.333, 54, 18, 15, 18, Colors.black),
        const Positioned(
          left: 294,
          top: 17,
          width: 17,
          height: 12,
          child: Icon(Icons.signal_cellular_alt_rounded,
              size: 17, color: Colors.black),
        ),
        const Positioned(
          left: 315,
          top: 15.5,
          width: 18,
          height: 15,
          child: Icon(Icons.wifi_rounded, size: 18, color: Colors.black),
        ),
        Positioned(
          left: 336.333,
          top: 17.333,
          width: 22,
          height: 11.333,
          child: DecoratedBox(
            decoration: BoxDecoration(
              border: Border.all(color: const Color(0xFF777777), width: 1),
              borderRadius: BorderRadius.circular(2.5),
            ),
            child: Padding(
              padding: const EdgeInsets.all(1.3),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(1),
                ),
              ),
            ),
          ),
        ),
        Positioned(
          left: 359.333,
          top: 21,
          width: 1.4,
          height: 4,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xFF888888),
              borderRadius: BorderRadius.circular(1),
            ),
          ),
        ),
      ],
    );
  }

  Widget _decorativeNumber(String value, double x, double y, double width,
      double height, Color color) {
    return Positioned(
      left: x,
      top: y,
      width: width,
      height: height,
      child: IgnorePointer(
        child: Text(
          value,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: 'Georgia',
            fontStyle: FontStyle.italic,
            fontWeight: FontWeight.w700,
            fontSize: 58,
            height: 1,
            color: color,
          ),
        ),
      ),
    );
  }

  Widget _quote(double x, double y, Color color) => Positioned(
        left: x,
        top: y,
        width: 25,
        height: 24,
        child: IgnorePointer(
          child: Text(
            '”',
            style: TextStyle(
              fontFamily: 'Georgia',
              fontWeight: FontWeight.w700,
              fontSize: 36,
              height: .8,
              color: color,
            ),
          ),
        ),
      );

  Widget _image(String file, double x, double y, double width, double height) {
    return Positioned(
      left: x,
      top: y,
      width: width,
      height: height,
      child: Image.asset('$_assetRoot$file', fit: BoxFit.fill),
    );
  }

  Widget _text(
    String value,
    double x,
    double y,
    double width,
    double height,
    double size,
    double lineHeight,
    Color color, {
    FontWeight weight = FontWeight.w400,
    int maxLines = 1,
  }) {
    return Positioned(
      left: x,
      top: y,
      width: width,
      height: height,
      child: Text(
        value,
        maxLines: maxLines,
        overflow: TextOverflow.clip,
        style: TextStyle(
          fontFamily: 'SourcePingFang',
          fontSize: size,
          height: lineHeight / size,
          fontWeight: weight,
          color: color,
        ),
      ),
    );
  }
}
