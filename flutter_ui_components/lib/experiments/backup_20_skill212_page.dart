import 'package:flutter/material.dart';

import 'backup_20_page.dart';

class Backup20Skill212Assets {
  static const _root = 'assets/lanhu/backup_20/assets/';
  static const background =
      '${_root}81bbbe61cf9743c327055bd857c78a07d2ae00d03da0b3fe73cc1f818c8fbef8.png';
  static const filter =
      '${_root}25d03260ab42ac63ba1dedf84ee3fc864655ede23cf851ba0371123af174b251.png';
  static const charmLeft =
      '${_root}e399986613cfbc2318d7b20a5cb9af711042cb66a90f57b82df10ffac7435587.png';
  static const charmRight =
      '${_root}e739690c8d8f4044c1db66215a49a44fb5ee054ba0c8712ba9f93d1910de0204.png';
  static const moon =
      '${_root}e5420067e59f59b435239f526e0ef79929941ca6d7a18ab96cbf47d55a04cc44.png';
  static const lightning =
      '${_root}73ed648a53f3412cbca8213402ebedcde5e29d6895ccf2997127da4368a1b4fd.png';
  static const videoLeft =
      '${_root}b7a33d41942e2460afd5273bccb13aa04562f9b772463766de69ff29ddbf586a.png';
  static const videoRight =
      '${_root}fe3626a18bd7ac06a53d30b9b3d4c8a9ec5ab64af92e2f9f1b1479989cc8bf32.png';
  static const hi =
      '${_root}ab525432b63981b0a1a9fa25e691704390238a82cebd9d6affab99d2c97f67ff.png';
  static const discover =
      '${_root}72d1cd9a5ea8f37572eff1978f809e0f2a2a6e4d207037919b919c27b2bc6adf.png';
  static const online =
      '${_root}f8df60ed4a5bd5c53615b56081eb7b495f118ac02fd666af44878977d9b54562.png';
  static const busy =
      '${_root}6f871ca7a79d1e5a46613c08304c6f46db6fd6dbebd2dff21b9344b520b6407b.png';

  static const all = [
    background,
    filter,
    charmLeft,
    charmRight,
    moon,
    lightning,
    videoLeft,
    videoRight,
    hi,
    discover,
    online,
    busy,
  ];
}

/// Existing 2.12 component implementation with scoped 2.14 detail repairs.
/// Not an independently implemented or fully accepted Skill 2.14.1 trial.
///
/// Six portraits and the notification avatar have no exportable source asset.
/// Each unavailable bitmap is represented by a shape-preserving placeholder;
/// all business labels, controls and layout remain native Flutter widgets.
class Backup20Skill212Page extends StatelessWidget {
  const Backup20Skill212Page({
    super.key,
    this.notificationSubtitle = '你在干嘛呀？',
    this.notificationSubtitleLeft = 76,
    this.notificationSubtitleTop = 37,
    this.notificationSubtitleColor = const Color(0xFF91919B),
    this.onReply,
    this.onProfile,
    this.onNavigation,
  });

  static const designSize = Size(375, 812);

  final String notificationSubtitle;
  final double notificationSubtitleLeft;
  final double notificationSubtitleTop;
  final Color notificationSubtitleColor;
  final VoidCallback? onReply;
  final ValueChanged<int>? onProfile;
  final ValueChanged<int>? onNavigation;

  @override
  Widget build(BuildContext context) => SizedBox(
        width: designSize.width,
        height: designSize.height,
        child: ClipRect(
          child: ColoredBox(
            color: const Color(0xFFFCF5FA),
            child: Stack(children: [
              _asset(Backup20Skill212Assets.background, 0, 0, 375, 161),
              _statusBar(),
              _text('交友', 14, 51, 40, 28, 20, 28, const Color(0xFF18181B),
                  FontWeight.w600),
              _asset(Backup20Skill212Assets.filter, 318, 47, 44, 44),
              for (var index = 0; index < 6; index++) _profileCard(index),
              _notification(),
              _navigation(),
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
        _text('9:41', 21, 14, 54, 18, 15, 18, Colors.black, FontWeight.w400),
        const Positioned(
          left: 307,
          top: 15,
          width: 54,
          height: 17,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              _MiniMissing(width: 12, height: 10),
              SizedBox(width: 5),
              _MiniMissing(width: 12, height: 10),
              SizedBox(width: 5),
              _MiniMissing(width: 20, height: 10),
            ],
          ),
        ),
      ]);

  Widget _profileCard(int index) {
    final row = index ~/ 2;
    final right = index.isOdd;
    final left = right ? 192.0 : 15.0;
    final top = 98.0 + row * 233;
    final name = right ? '南城以南…' : '阿珍同学';
    final action = right && row == 1
        ? Backup20Skill212Assets.hi
        : right
            ? Backup20Skill212Assets.videoRight
            : Backup20Skill212Assets.videoLeft;
    return Positioned(
      left: left,
      top: top,
      width: 168.5,
      height: 224.67,
      child: GestureDetector(
        key: ValueKey('backup20-skill212-profile-$index'),
        behavior: HitTestBehavior.opaque,
        onTap: () => onProfile?.call(index),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: Stack(children: [
            const Positioned.fill(
              child: _MissingAsset(
                radius: 14,
                label: '设计素材\n未切图',
              ),
            ),
            if (row > 0)
              Positioned(
                left: 6,
                top: 6,
                width: right ? 74 : 76,
                height: 16,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xB84E4C55),
                    border:
                        Border.all(color: const Color(0x80FFB6DE), width: .6),
                    borderRadius: BorderRadius.circular(9),
                  ),
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Row(children: [
                      Image.asset(
                        right
                            ? Backup20Skill212Assets.charmRight
                            : Backup20Skill212Assets.charmLeft,
                        width: 18,
                        height: 18,
                        filterQuality: FilterQuality.high,
                      ),
                      const SizedBox(width: 1),
                      const Text('魅力指数:',
                          textScaler: TextScaler.noScaling,
                          style: TextStyle(
                              inherit: false,
                              fontFamily: 'SourcePingFang',
                              fontSize: 9,
                              height: 13 / 9,
                              color: Colors.white)),
                      Text(row == 2 && right ? '500' : '1000',
                          textScaler: TextScaler.noScaling,
                          style: const TextStyle(
                              inherit: false,
                              fontFamily: 'SourcePingFang',
                              fontSize: 9,
                              height: 13 / 9,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFFF94F2D))),
                    ]),
                  ),
                ),
              ),
            const Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              height: 78,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Color(0x0018181B), Color(0xD918181B)],
                  ),
                ),
              ),
            ),
            Positioned(
              left: 10,
              top: 178,
              child: Text(name,
                  textScaler: TextScaler.noScaling,
                  style: const TextStyle(
                      inherit: false,
                      fontFamily: 'SourcePingFang',
                      fontSize: 14,
                      height: 20 / 14,
                      fontWeight: FontWeight.w600,
                      color: Colors.white)),
            ),
            _presenceBadge(index, cardTop: top),
            Positioned(
              left: 11,
              top: 202,
              width: 54,
              height: 14,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0x804B3A69),
                  border: Border.all(color: const Color(0x807C64A9), width: .5),
                  borderRadius: BorderRadius.circular(7),
                ),
                child: Row(children: [
                  Image.asset(
                    right
                        ? Backup20Skill212Assets.lightning
                        : Backup20Skill212Assets.moon,
                    width: 12,
                    height: 12,
                  ),
                  Text(right ? '甜酷辣妹' : '温柔知性',
                      textScaler: TextScaler.noScaling,
                      style: const TextStyle(
                          inherit: false,
                          fontFamily: 'SourcePingFang',
                          fontSize: 9,
                          height: 13 / 9,
                          color: Color(0xFFDAC7FF))),
                ]),
              ),
            ),
            Positioned(
              left: 127,
              top: 183,
              width: 42,
              height: 48,
              child: Image.asset(action, fit: BoxFit.fill),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _presenceBadge(int index, {required double cardTop}) {
    final busy = index.isOdd;
    // Source groups have distinct row offsets; do not regularize their frames.
    const sourceTops = [280.0, 279.0, 512.0, 511.0, 739.0, 738.0];
    return Positioned(
      left: busy ? 84 : 70,
      top: sourceTops[index] - cardTop,
      width: 34,
      height: 14,
      child: DecoratedBox(
        key: ValueKey('backup20-presence-$index'),
        decoration: const BoxDecoration(
          color: Color(0x33000000),
          borderRadius: BorderRadius.all(Radius.circular(7.2)),
        ),
        child: Stack(children: [
          // 6×6 export frame includes the source dot's transparent margins.
          Positioned(
            left: 4,
            top: 4,
            width: 6,
            height: 6,
            child: Image.asset(
              busy
                  ? Backup20Skill212Assets.busy
                  : Backup20Skill212Assets.online,
              key: ValueKey('backup20-presence-dot-$index'),
              fit: BoxFit.fill,
              filterQuality: FilterQuality.high,
            ),
          ),
          Positioned(
            left: 12.238095238095,
            top: index == 1 ? 2.402777777778 : 1.402777777778,
            width: 16,
            height: 11,
            child: Text(
              busy ? '忙碌' : '在线',
              key: ValueKey('backup20-presence-text-$index'),
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                inherit: false,
                fontFamily: 'SourcePingFang',
                fontSize: 8,
                height: 11 / 8,
                fontWeight: FontWeight.w600,
                color: busy ? const Color(0xFFF87B62) : const Color(0xFF3BCE8A),
              ),
            ),
          ),
        ]),
      ),
    );
  }

  Widget _notification() => Positioned(
        left: 14,
        top: 50,
        width: 343,
        height: 68,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFFFDF4F8),
            border: Border.all(color: Colors.white, width: .5),
            borderRadius: BorderRadius.circular(14),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x10000000),
                  blurRadius: 12,
                  offset: Offset(0, 4)),
            ],
          ),
          child: Stack(children: [
            const Positioned(
              left: 13,
              top: 9,
              width: 50,
              height: 50,
              child: _MissingAsset(radius: 25, label: '头像\n未切图', compact: true),
            ),
            const Positioned(
              left: 49,
              top: 50,
              width: 8,
              height: 8,
              child: DecoratedBox(
                key: ValueKey('backup20-avatar-online'),
                decoration: BoxDecoration(
                  color: Color(0xFF0CBB25),
                  shape: BoxShape.circle,
                  border: Border.fromBorderSide(
                    BorderSide(
                      color: Colors.white,
                      width: 1,
                      strokeAlign: BorderSide.strokeAlignOutside,
                    ),
                  ),
                ),
              ),
            ),
            _text('温柔丸性', 76, 16, 60, 21, 15, 21, const Color(0xFF22242A),
                FontWeight.w600),
            _text(
                notificationSubtitle,
                notificationSubtitleLeft,
                notificationSubtitleTop,
                72,
                17,
                12,
                17,
                notificationSubtitleColor,
                FontWeight.w400),
            Positioned(
              left: 274,
              top: 24,
              width: 54,
              height: 21,
              child: GestureDetector(
                key: const ValueKey('backup20-skill212-reply'),
                behavior: HitTestBehavior.opaque,
                onTap: onReply,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFEAE8),
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: const Center(
                    child: Text('回复',
                        textScaler: TextScaler.noScaling,
                        style: TextStyle(
                            inherit: false,
                            fontFamily: 'SourcePingFang',
                            fontSize: 12,
                            height: 17 / 12,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFFF94F2E))),
                  ),
                ),
              ),
            ),
          ]),
        ),
      );

  Widget _navigation() => Positioned(
        left: 14,
        top: 735,
        width: 343,
        height: 56,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFFFDFBFC),
            borderRadius: BorderRadius.circular(28),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x1A9D8A95),
                  blurRadius: 14,
                  offset: Offset(0, 3)),
            ],
          ),
          child: Stack(children: [
            const Positioned(
              left: 101,
              top: 7,
              width: 60,
              height: 43,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Color(0xFFFFF4F8),
                  borderRadius: BorderRadius.all(Radius.circular(22)),
                ),
              ),
            ),
            for (var index = 0; index < 4; index++)
              Positioned(
                left: index * 85.75,
                top: 0,
                width: 85.75,
                height: 56,
                child: GestureDetector(
                  key: ValueKey('backup20-skill212-navigation-$index'),
                  behavior: HitTestBehavior.opaque,
                  onTap: () => onNavigation?.call(index),
                  child: Column(children: [
                    const SizedBox(height: 7),
                    if (index == 0)
                      Image.asset(Backup20Skill212Assets.discover,
                          width: 29, height: 29)
                    else
                      _MiniMissing(
                        width: 29,
                        height: 29,
                        selected: index == 1,
                      ),
                    Text(const ['发现', '交友', '消息', '我的'][index],
                        textScaler: TextScaler.noScaling,
                        style: TextStyle(
                            inherit: false,
                            fontFamily: 'SourcePingFang',
                            fontSize: 9,
                            height: 10 / 9,
                            color: index == 1
                                ? const Color(0xFF18181B)
                                : const Color(0xFF7B7980))),
                  ]),
                ),
              ),
          ]),
        ),
      );

  static Widget _asset(
    String path,
    double left,
    double top,
    double width,
    double height,
  ) =>
      Positioned(
        left: left,
        top: top,
        width: width,
        height: height,
        child: Image.asset(path,
            fit: BoxFit.fill, filterQuality: FilterQuality.high),
      );

  static Widget _text(
    String value,
    double left,
    double top,
    double width,
    double height,
    double fontSize,
    double lineHeight,
    Color color,
    FontWeight weight,
  ) =>
      Positioned(
        left: left,
        top: top,
        width: width,
        height: height,
        child: Text(value,
            maxLines: 1,
            softWrap: false,
            overflow: TextOverflow.visible,
            textScaler: TextScaler.noScaling,
            style: TextStyle(
                inherit: false,
                decoration: TextDecoration.none,
                fontFamily: 'SourcePingFang',
                fontSize: fontSize,
                height: lineHeight / fontSize,
                leadingDistribution: TextLeadingDistribution.even,
                fontWeight: weight,
                color: color)),
      );
}

class _MissingAsset extends StatelessWidget {
  const _MissingAsset({
    required this.radius,
    required this.label,
    this.compact = false,
  });

  final double radius;
  final String label;
  final bool compact;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFFFFE5EA),
          border: Border.all(color: const Color(0xFFFF4D6D), width: .75),
          borderRadius: BorderRadius.circular(radius),
        ),
        child: Center(
          child: Text(label,
              textAlign: TextAlign.center,
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                  inherit: false,
                  decoration: TextDecoration.none,
                  fontFamily: 'SourcePingFang',
                  fontSize: compact ? 7 : 12,
                  height: 1.25,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFFC52245))),
        ),
      );
}

class _MiniMissing extends StatelessWidget {
  const _MiniMissing({
    required this.width,
    required this.height,
    this.selected = false,
  });

  final double width;
  final double height;
  final bool selected;

  @override
  Widget build(BuildContext context) => Semantics(
        label: '设计素材未切图',
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: selected ? const Color(0xFFFFC8D4) : const Color(0xFFFFE5EA),
            border: Border.all(color: const Color(0xFFFF4D6D), width: .75),
            borderRadius: BorderRadius.circular(height / 3),
          ),
          child: SizedBox(width: width, height: height),
        ),
      );
}

class Backup20Skill212PreviewPage extends StatefulWidget {
  const Backup20Skill212PreviewPage({super.key});

  @override
  State<Backup20Skill212PreviewPage> createState() =>
      _Backup20Skill212PreviewPageState();
}

class _Backup20Skill212PreviewPageState
    extends State<Backup20Skill212PreviewPage> {
  String mode = 'three';
  String event = '可点击人物卡、回复与底部导航。';

  Widget _panel(String title, String note, Widget child) => SizedBox(
        width: 375,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(
              child: Text(title,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
            ),
            Text(note,
                style: const TextStyle(fontSize: 11, color: Color(0xFF69727D))),
          ]),
          const SizedBox(height: 8),
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
        ]),
      );

  Widget _newPage() => Backup20Skill212Page(
        onReply: () => setState(() => event = '已触发回复'),
        onProfile: (index) => setState(() => event = '已打开人物卡 ${index + 1}'),
        onNavigation: (index) => setState(() => event = '已切换导航 ${index + 1}'),
      );

  @override
  Widget build(BuildContext context) {
    final panels = switch (mode) {
      'new' => [
          _panel('既有组件版', '局部修正 · 整页未验收', _newPage()),
        ],
      'versions' => [
          _panel('Skill 2.11', '整区域裁片', const Backup20Page()),
          _panel('既有组件版', '局部修正 · 整页未验收', _newPage()),
        ],
      _ => [
          _panel('蓝湖原稿', '4× 固定快照',
              Image.asset(Backup20Assets.reference, fit: BoxFit.fill)),
          _panel('Skill 2.11', '整区域裁片', const Backup20Page()),
          _panel('既有组件版', '局部修正 · 整页未验收', _newPage()),
        ],
    };
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('1备份 20 · 原稿 / 整区裁片 / 既有组件对比',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            const Text(
              '本组件来自 2.12 实现和后续局部修正，不是独立的 2.14.1 测试。整页未验收；已确认底栏合成效果、卡片异形底片仍有缺失。',
              style: TextStyle(color: Color(0xFF65717E)),
            ),
            const SizedBox(height: 14),
            Wrap(spacing: 8, children: [
              for (final item in const [
                ('three', '三方对比'),
                ('versions', '两版对比'),
                ('new', '只看组件版'),
              ])
                ChoiceChip(
                  label: Text(item.$2),
                  selected: mode == item.$1,
                  onSelected: (_) => setState(() => mode = item.$1),
                ),
            ]),
            const SizedBox(height: 8),
            Text(event,
                style: const TextStyle(fontSize: 12, color: Color(0xFF65717E))),
            const SizedBox(height: 18),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (var index = 0; index < panels.length; index++) ...[
                    panels[index],
                    if (index < panels.length - 1) const SizedBox(width: 22),
                  ],
                ],
              ),
            ),
          ]),
        ),
      ),
    );
  }
}
