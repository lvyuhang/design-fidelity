import 'dart:math' as math;

import 'package:flutter/material.dart';

class Backup20Assets {
  static const String _sourceRoot = 'assets/lanhu/backup_20_source/';
  static const backgroundGlow =
      'assets/lanhu/backup_20/assets/81bbbe61cf9743c327055bd857c78a07d2ae00d03da0b3fe73cc1f818c8fbef8.png';
  static const statusBar = '${_sourceRoot}status_bar.png';
  static const notificationAvatar = '${_sourceRoot}notification_avatar.png';
  static const gridRow1 = '${_sourceRoot}grid_row_1.png';
  static const gridRow2 = '${_sourceRoot}grid_row_2.png';
  static const gridRow3Top = '${_sourceRoot}grid_row_3_top.png';
  static const bottomNav = '${_sourceRoot}bottom_nav.png';
  static const bottomRightSliver = '${_sourceRoot}bottom_right_sliver.png';
  static const reference = 'assets/reference/backup_20.png';

  static const all = [
    backgroundGlow,
    statusBar,
    notificationAvatar,
    gridRow1,
    gridRow2,
    gridRow3Top,
    bottomNav,
    bottomRightSliver,
  ];
}

/// Flutter implementation of Lanhu artboard `1备份 20`.
///
/// The six profile bitmaps have no source URL or exportable asset ID in the
/// pinned Lanhu snapshot. Their visible rows therefore use documented 4×
/// source-render crops. The notification card, backdrop, home indicator and
/// every interaction target remain Flutter widgets.
class Backup20Page extends StatelessWidget {
  const Backup20Page({
    super.key,
    this.onReply,
    this.onProfile,
    this.onNavigation,
  });

  final VoidCallback? onReply;
  final ValueChanged<int>? onProfile;
  final ValueChanged<int>? onNavigation;

  static const designSize = Size(375, 812);

  @override
  Widget build(BuildContext context) => SizedBox(
        width: designSize.width,
        height: designSize.height,
        child: ClipRect(
          child: ColoredBox(
            color: const Color(0xFFFCF5FA),
            child: Stack(children: [
              _asset(Backup20Assets.backgroundGlow, 0, 0, 375, 161),
              _asset(Backup20Assets.statusBar, 21, 14, 340, 19),
              _profileRow(0, Backup20Assets.gridRow1, 15, 118, 345.5, 205),
              _profileRow(2, Backup20Assets.gridRow2, 15, 331, 345.5, 225),
              _profileRow(4, Backup20Assets.gridRow3Top, 15, 564, 345.5, 171),
              _asset(Backup20Assets.bottomRightSliver, 357, 735, 4, 54),
              _notificationCard(),
              _bottomNavigation(),
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

  Widget _profileRow(
    int firstIndex,
    String asset,
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
        child: Stack(fit: StackFit.expand, children: [
          Image.asset(asset,
              fit: BoxFit.fill, filterQuality: FilterQuality.none),
          Row(children: [
            Expanded(
              child: GestureDetector(
                key: ValueKey('backup20-profile-$firstIndex'),
                behavior: HitTestBehavior.opaque,
                onTap: () => onProfile?.call(firstIndex),
              ),
            ),
            const SizedBox(width: 8.5),
            Expanded(
              child: GestureDetector(
                key: ValueKey('backup20-profile-${firstIndex + 1}'),
                behavior: HitTestBehavior.opaque,
                onTap: () => onProfile?.call(firstIndex + 1),
              ),
            ),
          ]),
        ]),
      );

  Widget _notificationCard() => Positioned(
        left: 14,
        top: 50,
        width: 343,
        height: 68,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFFFDF4F8),
            border: Border.all(color: Colors.white, width: .5),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Stack(children: [
            _asset(Backup20Assets.notificationAvatar, 13, 9, 50, 50),
            _text(
              '温柔丸性',
              76,
              16,
              60,
              21,
              15,
              21,
              const Color(0xFF22242A),
              weight: FontWeight.w600,
            ),
            _text(
              '你在干嘛呀？',
              76,
              37,
              72,
              17,
              12,
              17,
              const Color(0xFF91919B),
            ),
            Positioned(
              left: 274,
              top: 24,
              width: 54,
              height: 21,
              child: Semantics(
                button: true,
                label: '回复温柔丸性',
                child: GestureDetector(
                  key: const ValueKey('backup20-reply'),
                  behavior: HitTestBehavior.opaque,
                  onTap: onReply,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFEAE8),
                      borderRadius: BorderRadius.circular(11),
                    ),
                    child: const Center(
                      child: Text(
                        '回复',
                        textScaler: TextScaler.noScaling,
                        style: TextStyle(
                          inherit: false,
                          decoration: TextDecoration.none,
                          fontFamily: 'SourcePingFang',
                          fontSize: 12,
                          height: 17 / 12,
                          leadingDistribution: TextLeadingDistribution.even,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFFF94F2E),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ]),
        ),
      );

  Widget _bottomNavigation() => Positioned(
        left: 14,
        top: 735,
        width: 343,
        height: 56,
        child: Stack(fit: StackFit.expand, children: [
          Image.asset(
            Backup20Assets.bottomNav,
            fit: BoxFit.fill,
            filterQuality: FilterQuality.none,
          ),
          Row(
            children: List.generate(
              4,
              (index) => Expanded(
                child: GestureDetector(
                  key: ValueKey('backup20-navigation-$index'),
                  behavior: HitTestBehavior.opaque,
                  onTap: () => onNavigation?.call(index),
                ),
              ),
            ),
          ),
        ]),
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
        child: Image.asset(
          path,
          fit: BoxFit.fill,
          filterQuality: FilterQuality.none,
        ),
      );

  static Widget _text(
    String value,
    double left,
    double top,
    double width,
    double height,
    double fontSize,
    double lineHeight,
    Color color, {
    FontWeight weight = FontWeight.w400,
  }) =>
      Positioned(
        left: left,
        top: top,
        width: width,
        height: height,
        child: Text(
          value,
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
            color: color,
          ),
        ),
      );
}

class Backup20PreviewPage extends StatefulWidget {
  const Backup20PreviewPage({super.key});

  @override
  State<Backup20PreviewPage> createState() => _Backup20PreviewPageState();
}

class _Backup20PreviewPageState extends State<Backup20PreviewPage> {
  String mode = 'compare';
  double opacity = .5;
  String event = '可点击回复、人物卡和底部导航。';

  Widget _reference() => Image.asset(
        Backup20Assets.reference,
        width: 375,
        height: 812,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );

  Widget _implementation() => Backup20Page(
        onReply: () => setState(() => event = '已触发回复'),
        onProfile: (index) => setState(() => event = '已打开人物卡 ${index + 1}'),
        onNavigation: (index) => setState(() => event = '已切换底部导航 ${index + 1}'),
      );

  Widget _panel(String title, String badge, Widget child) => SizedBox(
        width: 375,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(children: [
              Expanded(
                child: Text(title,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ),
              Text(badge,
                  style:
                      const TextStyle(fontSize: 11, color: Color(0xFF65717E))),
            ]),
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
        ]),
      );

  Widget _panels(List<Widget> panels) => LayoutBuilder(
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

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFFF2F3F5),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 28, 24, 48),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('1备份 20 · 页面还原测试',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              const Text(
                'Lanhu MCP 固定快照 · Skill 2.11 · 375 × 812',
                style: TextStyle(color: Color(0xFF65717E)),
              ),
              const SizedBox(height: 14),
              Wrap(spacing: 8, children: [
                for (final choice in const [
                  ('compare', '左右对照'),
                  ('flutter', '只看 Flutter'),
                  ('overlay', '叠加检查'),
                ])
                  ChoiceChip(
                    label: Text(choice.$2),
                    selected: mode == choice.$1,
                    onSelected: (_) => setState(() => mode = choice.$1),
                  ),
              ]),
              if (mode == 'overlay')
                SizedBox(
                  width: 375,
                  child: Slider(
                    value: opacity,
                    onChanged: (value) => setState(() => opacity = value),
                  ),
                ),
              const SizedBox(height: 18),
              if (mode == 'compare')
                _panels([
                  _panel('蓝湖原稿', '固定版本 · 4×', _reference()),
                  _panel('Flutter 实现', '本轮结果', _implementation()),
                ])
              else if (mode == 'flutter')
                _panels([_panel('Flutter 实现', '375 × 812', _implementation())])
              else
                _panels([
                  _panel(
                    '叠加：蓝湖 / Flutter',
                    '原稿 ${(opacity * 100).round()}%',
                    Stack(children: [
                      _implementation(),
                      IgnorePointer(
                          child:
                              Opacity(opacity: opacity, child: _reference())),
                    ]),
                  ),
                ]),
              const SizedBox(height: 18),
              Text(event, style: const TextStyle(color: Color(0xFF4E5A67))),
              const SizedBox(height: 10),
              const Text(
                '素材说明：43/43 个可导出资源已校验；六张人物 bitmap 没有源 URL 或 asset ID，因此人物区使用固定 4× 原稿裁切，未生成替代人物图。',
                style: TextStyle(
                    fontSize: 12, color: Color(0xFF687482), height: 1.6),
              ),
            ]),
          ),
        ),
      );
}
