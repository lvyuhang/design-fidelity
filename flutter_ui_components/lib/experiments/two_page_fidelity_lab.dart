import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'filter_backup_page.dart';
import 'home_page_optimized.dart';
import 'message_backup_34_page.dart';
import 'message_backup_36_page.dart';
import 'message_backup_45_page.dart';
import 'platform_intro_optimized_page.dart';
import 'voice_calling_backup_2_page.dart';

class PlatformIntroOptimizedPreviewPage extends StatelessWidget {
  const PlatformIntroOptimizedPreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '加入聚星阁 · 平台介绍页',
        revision: 'Skill 2.18.3 · 三轮回归验证',
        reference: 'assets/lanhu/full_page/reference.png',
        logLines: const [
          '范围：固定 da6dd92d 快照，100/100 节点、11 张蓝湖原始素材；本次为历史实现上的新版流程回归，不是冷启动模型实验。',
          'R0：真实 Flutter 4× 渲染；整页 MAE 3.46、P95 20，大区域通过但10项局部检查失败。',
          'R1：按素材导出画框修正三枚收益图标，并校准源字体权重；失败项 10→8。',
          'R2：按检测器重心做亚像素文字移动，失败项8→2，但整页MAE升至4.52；判定为负优化并撤回。',
          '最终选择R1：整页MAE 3.34、P95 19；CTA MAE 1.99、P95 1；旧区域阈值通过。',
          '未通过：仍有8项字体墨迹/组内中心线检查失败，未以调整阈值或亚像素偏移强行通过。',
          '缺图：引号、01/02 与星光缺少路径/字体/位图，继续按源矩形显示粉色占位。',
          '说明：没有降低阈值或扩大排除；旧v1契约仅作诊断，不能授予Skill 2.18.3正式PASS。',
        ],
        implementation: (event) => PlatformIntroOptimizedPage(
          onSkip: () => event('已触发跳过'),
          onStart: () => event('已触发开始入驻'),
        ),
      );
}

class HomePageOptimizedPreviewPage extends StatelessWidget {
  const HomePageOptimizedPreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '首页 · 发现双列信息流',
        revision: 'Skill 2.18.3 · 第二案例',
        reference: 'assets/reference/home-page.png',
        referenceBadge: '固定 58e8325b · 蓝湖原稿',
        logLines: const [
          'MCP：固定 58e8325b 快照，375×812、165 个节点、14/14 个蓝湖导出素材。',
          '实现：顶部原始导出；双列卡片、文字、状态与交互为 Flutter；底部导航复用源节点渲染。',
          '缺图：5 个内容照片区域与对应头像没有独立切图，仅在媒体画框内使用原稿裁片回退。',
          '门禁：4× Flutter 渲染；媒体回退区单独披露，结构与文字区域按固定阈值复查。',
        ],
        implementation: (event) => HomePageOptimized(
          onCard: (index) => event('已打开内容卡片 ${index + 1}'),
          onLike: (index) => event('已触发卡片 ${index + 1} 点赞'),
          onCompose: () => event('已触发发布入口'),
          onNavigation: (index) => event('已切换底部导航 $index'),
        ),
      );
}

class MessageBackup34PreviewPage extends StatelessWidget {
  const MessageBackup34PreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '1备份 34 · 消息列表',
        revision: 'Skill 2.5.0 · 优化回放 v1',
        reference: 'assets/reference/message_backup_34.png',
        referenceBadge: '固定快照 · 原生 2×',
        logLines: const [
          '缓存取证：固定 161 节点、13/13 原始资源；本轮 MCP 调用 0。',
          '预检：原生 2× 参考图、三种字体、素材解码与节点映射全部通过。',
          '缺图：5 张人物头像和官方通知图标按源外形标为“未切”，没有借用其他图标。',
          '修正：正式门禁 3项 → 1项 → 1项 → 0项，阈值与排除范围未降低。',
          '验收：PASS_WITH_EXCLUSIONS；139/141 节点覆盖，2 个节点明确排除，58/58 特征通过。',
          '指标：全页 MAE 3.29、P95 13；排除面积 3.67%。',
          '计时：固定证据回放 16.6 秒，其中渲染与门禁 1.8 秒、Web 构建 13.1 秒。',
        ],
        implementation: (event) => MessageBackup34Page(
          onNotification: () => event('已触发开启通知'),
          onFilter: () => event('已触发筛选'),
          onTab: (index) => event('已切换分类 $index'),
          onConversation: (index) => event('已打开消息 $index'),
          onNavigation: (index) => event('已切换底部导航 $index'),
        ),
      );
}

class MessageBackup36PreviewPage extends StatelessWidget {
  const MessageBackup36PreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '1备份 36 · 新页面效率验证',
        revision: 'Skill 2.5.0 · 增量实现',
        reference: 'assets/reference/message_backup_36.png',
        referenceBadge: '固定快照 · 原生 2×',
        logLines: const [
          'MCP：固定 171 节点、14/14 原始资源；复用 12 个同 SHA 素材，只下载 2 个新增素材。',
          'R1 复查：发现 7 项偏差，集中在标题纵向、折叠图标描边溢出和箭头墨迹。',
          'R2 修正：按源矢量可见边界重绘 6 条线，校正标题和原始箭头画框；失败项降至 0。',
          '缺图：6 张人物头像均按 45×45 圆形原画框显示“未切”。',
          '验收：PASS_WITH_EXCLUSIONS；150/150 节点覆盖、67 项特征通过，排除面积 3.64%。',
          '指标：全页 MAE 3.27、P95 12；正式缓存回放 17.10 秒，渲染与门禁 1.78 秒。',
        ],
        implementation: (event) => MessageBackup36Page(
          onNotification: () => event('已触发开启通知'),
          onFilter: () => event('已触发筛选'),
          onTab: (index) => event('已切换分类 $index'),
          onConversation: (index) => event('已打开消息 $index'),
          onPinnedConversation: () => event('已触发折叠置顶会话'),
          onNavigation: (index) => event('已切换底部导航 $index'),
        ),
      );
}

class MessageBackup45PreviewPage extends StatelessWidget {
  const MessageBackup45PreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '1备份 45 · 新版 Skill 冷启动测试',
        revision: 'Skill 2.6.0 · 冷启动最终验收',
        reference: 'assets/reference/message_backup_45.png',
        logLines: const [
          'MCP：固定 4c1aaffb 快照，143/143 节点、16 个文字样式完整。',
          '素材：14/14 原始资源导出；9 个头像、礼物图和星币图未切图，按原画框占位。',
          '实现：消息气泡、语音/视频记录、礼物卡与底部工具栏均按源坐标落地。',
          'R1：门禁发现 7 个小图标轮廓/位置问题；校正返回、波形、视频和底部工具图标。',
          'R2 目检：自动门禁通过，但发现礼物名称缺字；补充可复现字体子集并进入截图测试。',
          '验收：PASS_WITH_EXCLUSIONS；106/118 节点覆盖，排除面积 3.77%，28 项特征无失败。',
          '指标：全页 MAE 1.68、消息区 MAE 0.47，P95 分别为 5 和 1。',
        ],
        implementation: (event) => MessageBackup45Page(
          onBack: () => event('已触发返回'),
          onRelationship: () => event('已打开关系入口'),
          onMore: () => event('已打开更多操作'),
          onInput: () => event('已触发消息输入'),
          onTool: (index) => event('已触发底部工具 ${index + 1}'),
        ),
      );
}

class FilterBackupPreviewPage extends StatelessWidget {
  const FilterBackupPreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '筛选备份',
        revision: '5.6 Sol · Skill 2.5.0 · r8',
        reference: 'assets/reference/filter_backup.png',
        logLines: const [
          'MCP：236 个节点，15/15 个原始资源获取成功。',
          '复查：修复字体、阴影、到期底纹、分隔线和漏斗闭合路径。',
          '缺图：两张背景照片、四个业务图标使用原画框占位。',
          '结果：官方门禁 PASS_WITH_EXCLUSIONS，失败检查 0。',
        ],
        implementation: (event) => FilterBackupPage(
          onClose: () => event('已触发关闭'),
          onConfigure: () => event('已触发去配置任务项'),
          onTaskTap: (index) => event('已触发待配置任务 ${index + 1}'),
          onEnabledTaskTap: (index) => event('已触发已开启任务 ${index + 1}'),
        ),
      );
}

class VoiceCallingBackup2PreviewPage extends StatelessWidget {
  const VoiceCallingBackup2PreviewPage({super.key});

  @override
  Widget build(BuildContext context) => _FidelityPreviewPage(
        title: '语音中－拨打方备份 2',
        revision: '5.6 Sol · Skill 2.5.0 · r12',
        reference: 'assets/reference/voice_calling_backup_2.png',
        logLines: const [
          'MCP：89 个节点，4/4 个原始资源获取成功。',
          '复查：修复波形偏移、头像环亮度、玻璃描边和近似图标。',
          '缺图：头像照片使用 80×80 圆形占位，原始金色头像环保留。',
          '结果：官方门禁 PASS_WITH_EXCLUSIONS，失败检查 0。',
        ],
        implementation: (event) => VoiceCallingBackup2Page(
          onMinimize: () => event('已触发最小化'),
          onMore: () => event('已触发更多操作'),
          onClose: () => event('已触发结束通话'),
          onRelationship: () => event('已触发关系入口'),
          onMessage: () => event('已触发文字输入'),
          onPhoto: () => event('已触发发送图片'),
          onGift: () => event('已触发送礼物'),
        ),
      );
}

class _FidelityPreviewPage extends StatefulWidget {
  const _FidelityPreviewPage({
    required this.title,
    required this.revision,
    required this.reference,
    this.referenceBadge = '固定快照 · 4×',
    required this.logLines,
    required this.implementation,
  });

  final String title;
  final String revision;
  final String reference;
  final String referenceBadge;
  final List<String> logLines;
  final Widget Function(ValueChanged<String> event) implementation;

  @override
  State<_FidelityPreviewPage> createState() => _FidelityPreviewPageState();
}

class _FidelityPreviewPageState extends State<_FidelityPreviewPage> {
  String mode = 'compare';
  double opacity = .5;
  String eventText = '尚未触发交互';

  Widget _source() => Image.asset(
        widget.reference,
        width: 375,
        height: 812,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );

  Widget _implementation() => widget.implementation(
        (value) => setState(() => eventText = value),
      );

  Widget _panel(String label, String badge, Widget child) => SizedBox(
        width: 375,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(children: [
                Expanded(
                    child: Text(label,
                        style: const TextStyle(fontWeight: FontWeight.w600))),
                Text(badge,
                    style: const TextStyle(
                        fontSize: 11, color: Color(0xFF65717E))),
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
    if (mode == 'source') {
      return _row([_panel('蓝湖原稿', widget.referenceBadge, _source())]);
    }
    if (mode == 'flutter') {
      return _row([_panel('Flutter 原生实现', '375 × 812', _implementation())]);
    }
    if (mode == 'overlay') {
      return _row([
        _panel(
          '叠加：蓝湖 / Flutter',
          '原稿 ${(opacity * 100).round()}%',
          Stack(children: [
            _implementation(),
            Opacity(opacity: opacity, child: _source()),
          ]),
        ),
      ]);
    }
    return _row([
      _panel('蓝湖原稿', widget.referenceBadge, _source()),
      _panel('Flutter 原生实现', '375 × 812', _implementation()),
    ]);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 28),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1040),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(widget.title,
                              style: const TextStyle(
                                  fontSize: 26, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 6),
                          Text('${widget.revision} · 固定 375px 移动画布',
                              style: const TextStyle(color: Color(0xFF65717E))),
                          const SizedBox(height: 16),
                          Wrap(spacing: 8, runSpacing: 8, children: [
                            for (final item in const [
                              ('compare', '左右对照'),
                              ('source', '蓝湖原稿'),
                              ('flutter', 'Flutter'),
                              ('overlay', '叠加检查'),
                            ])
                              ChoiceChip(
                                label: Text(item.$2),
                                selected: mode == item.$1,
                                onSelected: (_) =>
                                    setState(() => mode = item.$1),
                              ),
                          ]),
                          if (mode == 'overlay')
                            Slider(
                              value: opacity,
                              onChanged: (value) =>
                                  setState(() => opacity = value),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    _result(),
                    const SizedBox(height: 22),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFDDE1E6)),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(18),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('运行日志',
                                  style: TextStyle(
                                      fontSize: 17,
                                      fontWeight: FontWeight.w600)),
                              const SizedBox(height: 10),
                              for (final line in widget.logLines)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 6),
                                  child: Text(line),
                                ),
                              const Divider(height: 22),
                              Text('交互：$eventText',
                                  style: const TextStyle(
                                      color: Color(0xFF65717E))),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
}
