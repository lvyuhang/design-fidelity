import 'package:flutter/material.dart';

import 'backup_20_skill212_page.dart';

/// Controlled Skill 2.13 reuse case for Lanhu artboard `1备份 21`.
///
/// Pinned evidence proves all 19 unique exported assets and all pixels outside
/// the notification subtitle are identical to `1备份 20`.
class Backup21Skill213Page extends StatelessWidget {
  const Backup21Skill213Page({
    super.key,
    this.onReply,
    this.onProfile,
    this.onNavigation,
  });

  static const designSize = Backup20Skill212Page.designSize;

  final VoidCallback? onReply;
  final ValueChanged<int>? onProfile;
  final ValueChanged<int>? onNavigation;

  @override
  Widget build(BuildContext context) => Backup20Skill212Page(
        notificationSubtitle: '[语音] 7”',
        notificationSubtitleLeft: 77,
        notificationSubtitleTop: 39,
        // The source is opaque #91919B. Flutter/Skia rasterizes this bundled
        // PingFang face about 5% denser than the pinned Lanhu PNG; 95% alpha
        // preserves the measured glyph geometry while matching its edge ink.
        notificationSubtitleColor: const Color(0xF291919B),
        onReply: onReply,
        onProfile: onProfile,
        onNavigation: onNavigation,
      );
}

class Backup21Skill213PreviewPage extends StatefulWidget {
  const Backup21Skill213PreviewPage({super.key});

  @override
  State<Backup21Skill213PreviewPage> createState() =>
      _Backup21Skill213PreviewPageState();
}

class _Backup21Skill213PreviewPageState
    extends State<Backup21Skill213PreviewPage> {
  bool sourceOnly = false;
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

  Widget _implementation() => Backup21Skill213Page(
        onReply: () => setState(() => event = '已触发回复'),
        onProfile: (index) => setState(() => event = '已打开人物卡 ${index + 1}'),
        onNavigation: (index) => setState(() => event = '已切换导航 ${index + 1}'),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('1备份 21 · Skill 2.13 复用测试',
                    style:
                        TextStyle(fontSize: 26, fontWeight: FontWeight.w600)),
                const SizedBox(height: 6),
                const Text(
                  '诊断预览，尚未完成整页验收。历史差分检查不能证明复用组件合格；共享状态底板和圆点已修复并加入源数据回归检查。缺图继续保形占位。',
                  style: TextStyle(color: Color(0xFF65717E)),
                ),
                const SizedBox(height: 12),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('只看蓝湖原稿'),
                  value: sourceOnly,
                  onChanged: (value) => setState(() => sourceOnly = value),
                ),
                Text(event,
                    style: const TextStyle(
                        fontSize: 12, color: Color(0xFF65717E))),
                const SizedBox(height: 16),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _panel(
                        '蓝湖原稿',
                        '4× 固定快照',
                        Image.asset('assets/reference/backup_21.png',
                            fit: BoxFit.fill),
                      ),
                      if (!sourceOnly) ...[
                        const SizedBox(width: 22),
                        _panel('Skill 2.13 Flutter', '复用组件 + 证据差分',
                            _implementation()),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      );
}
