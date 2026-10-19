import 'package:flutter/material.dart';
import 'components/login_components.dart';
import 'components/expanded_components.dart';
import 'components/social_components.dart';
import 'experiments/appeal_experiment_page.dart';
import 'experiments/backup_20_page.dart';
import 'experiments/backup_20_skill212_page.dart';
import 'experiments/backup_21_skill213_page.dart';
import 'experiments/caller_relationship_page.dart';
import 'experiments/complaint_record_empty_page.dart';
import 'experiments/components_model_comparison_page.dart';
import 'experiments/full_page_model_comparison_page.dart';
import 'experiments/gender_experiment_page.dart';
import 'experiments/settings_case_page.dart';
import 'experiments/detail_page_2_case.dart';
import 'experiments/task_plan_44_page.dart';
import 'experiments/two_page_fidelity_lab.dart';
import 'experiments/withdraw_2_page.dart';

void main() => runApp(const ComponentLab());

class ComponentLab extends StatelessWidget {
  const ComponentLab({this.caseName, this.pageOverride, super.key});
  final String? caseName;
  final Widget? pageOverride;
  @override
  Widget build(BuildContext context) => MaterialApp(
      debugShowCheckedModeBanner: false,
      title: '聚星阁 · 组件还原验证',
      theme: ThemeData(
          fontFamily: 'SourcePingFang',
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF314354)),
          scaffoldBackgroundColor: const Color(0xFFF2F3F5)),
      home: pageOverride ??
          switch (caseName ?? Uri.base.queryParameters['case']) {
            'appeal-direct' => AppealExperimentPage(
                galleryBuilder: (_) => const FidelityGallery()),
            'gender-direct' => GenderExperimentPage(
                galleryBuilder: (_) => const FidelityGallery()),
            'model-comparison' => ComponentsModelComparisonPage(
                galleryBuilder: (_) => const FidelityGallery()),
            'full-page-models' => const FullPageModelComparisonPage(),
            'caller-relationship' => const CallerRelationshipPage(),
            'task-plan-44' => const TaskPlan44Page(),
            'filter-backup' => const FilterBackupPreviewPage(),
            'voice-calling-backup-2' => const VoiceCallingBackup2PreviewPage(),
            'message-backup-34' => const MessageBackup34PreviewPage(),
            'message-backup-36' => const MessageBackup36PreviewPage(),
            'message-backup-45' => const MessageBackup45PreviewPage(),
            'platform-intro-optimized' =>
              const PlatformIntroOptimizedPreviewPage(),
            'home-page-optimized' => const HomePageOptimizedPreviewPage(),
            'complaint-record-empty' =>
              const _ComplaintRecordEmptyPreviewPage(),
            'settings-case-only' => const SettingsCasePreviewPage(),
            'detail-page-2-complex' => const DetailPage2CasePreviewPage(),
            'withdraw-2-skill2186' => const Withdraw2PreviewPage(),
            'backup-20' => const Backup20PreviewPage(),
            'backup-20-skill212' => const Backup20Skill212PreviewPage(),
            'backup-20-skill2141' => const Backup20Skill212PreviewPage(),
            'backup-21-skill213' => const Backup21Skill213PreviewPage(),
            _ => const FidelityGallery(),
          });
}

class _ComplaintRecordEmptyPreviewPage extends StatelessWidget {
  const _ComplaintRecordEmptyPreviewPage();

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFFF2F3F5),
        body: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Center(
            child: Column(children: [
              const Text('投诉记录备份 · 独立案例测试',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
              const SizedBox(height: 12),
              Container(
                width: 375,
                decoration: BoxDecoration(
                  border: Border.all(color: const Color(0xFFCBD1D9)),
                  boxShadow: const [
                    BoxShadow(color: Color(0x22000000), blurRadius: 16)
                  ],
                ),
                child: const ComplaintRecordEmptyPage(),
              ),
            ]),
          ),
        ),
      );
}

class FidelityGallery extends StatefulWidget {
  const FidelityGallery({super.key});
  @override
  State<FidelityGallery> createState() => _FidelityGalleryState();
}

class _FidelityGalleryState extends State<FidelityGallery> {
  String mode = 'compare';
  double opacity = .5;
  final events = <String, String>{};
  void event(String sample, String value) =>
      setState(() => events[sample] = value);
  @override
  Widget build(BuildContext context) => Scaffold(
      body: SafeArea(
          child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(vertical: 32),
              child: Center(
                  child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 950),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Padding(
                                padding: EdgeInsets.symmetric(horizontal: 24),
                                child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text('聚星阁 / COMPONENT LAB',
                                          style: TextStyle(
                                              fontSize: 12,
                                              color: Color(0xFF687482),
                                              letterSpacing: 1)),
                                      SizedBox(height: 10),
                                      Text('七类组件，同一把还原标尺',
                                          style: TextStyle(
                                              fontSize: 28,
                                              fontWeight: FontWeight.w600)),
                                      SizedBox(height: 10),
                                      Text(
                                          '动态卡片 · 性别选择 · 评论 · 弹窗 · 导航 · 申诉 · 登录',
                                          style: TextStyle(fontSize: 16)),
                                      SizedBox(height: 6),
                                      Text(
                                          '每块预览固定 375px。左侧为蓝湖源稿，右侧为可交互的 Flutter 组件。',
                                          style: TextStyle(
                                              color: Color(0xFF65717E),
                                              height: 1.6)),
                                    ])),
                            const SizedBox(height: 20),
                            Padding(
                                padding:
                                    const EdgeInsets.symmetric(horizontal: 24),
                                child:
                                    Wrap(spacing: 8, runSpacing: 8, children: [
                                  for (final item in const [
                                    ('compare', '左右对照'),
                                    ('flutter', 'Flutter 组件'),
                                    ('overlay', '叠加对照')
                                  ])
                                    ChoiceChip(
                                        label: Text(item.$2),
                                        selected: mode == item.$1,
                                        onSelected: (_) =>
                                            setState(() => mode = item.$1)),
                                ])),
                            if (mode == 'overlay')
                              Padding(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 24),
                                  child: Column(children: [
                                    Slider(
                                        value: opacity,
                                        onChanged: (v) =>
                                            setState(() => opacity = v)),
                                    Text(
                                        '原稿透明度 ${(opacity * 100).round()}% · 0% 只看 Flutter / 100% 只看原稿',
                                        style: const TextStyle(fontSize: 12)),
                                  ])),
                            Padding(
                                padding:
                                    const EdgeInsets.fromLTRB(24, 18, 24, 0),
                                child: OutlinedButton.icon(
                                    icon: const Icon(Icons.science_outlined,
                                        size: 18),
                                    label: const Text('实验：直接读取 MCP 实现申诉卡片'),
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const AppealExperimentPage())))),
                            Padding(
                                padding:
                                    const EdgeInsets.fromLTRB(24, 8, 24, 0),
                                child: OutlinedButton.icon(
                                    icon: const Icon(Icons.science_outlined,
                                        size: 18),
                                    label: const Text(
                                        '模型对比：GPT-5.6 Sol / GPT-6 性别选择'),
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const GenderExperimentPage())))),
                            Padding(
                                padding:
                                    const EdgeInsets.fromLTRB(24, 8, 24, 0),
                                child: FilledButton.icon(
                                    icon: const Icon(Icons.compare_arrows,
                                        size: 18),
                                    label: const Text(
                                        '模型对比：全部组件 5.6 Sol / 此前 GPT-6'),
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const ComponentsModelComparisonPage())))),
                            Padding(
                                padding:
                                    const EdgeInsets.fromLTRB(24, 8, 24, 0),
                                child: FilledButton.icon(
                                    icon: const Icon(Icons.phone_iphone,
                                        size: 18),
                                    label: const Text(
                                        '完整页面对比：蓝湖 / 5.6 Sol / GPT-6'),
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const FullPageModelComparisonPage())))),
                            Padding(
                                padding:
                                    const EdgeInsets.fromLTRB(24, 8, 24, 0),
                                child: FilledButton.icon(
                                    icon: const Icon(Icons.call_outlined,
                                        size: 18),
                                    label: const Text('完整页面：拨打方-1备份 2 / 蓝湖对照'),
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const CallerRelationshipPage())))),
                            Padding(
                                padding:
                                    const EdgeInsets.fromLTRB(24, 8, 24, 0),
                                child: FilledButton.icon(
                                    icon: const Icon(Icons.task_alt, size: 18),
                                    label: const Text('完整页面：1备份 44 / 任务计划'),
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const TaskPlan44Page())))),
                            _sample(
                                'feed',
                                '新增 / 图文动态卡片',
                                342,
                                'assets/reference/feed-stage.png',
                                FeedComponentStage(
                                    onOpen: () => event('feed', '已触发 onOpen。'),
                                    onLike: () =>
                                        event('feed', '已触发 onLike；源稿仅提供未点赞态。'),
                                    onProfile: () =>
                                        event('feed', '已触发 onProfile。')),
                                '首页 · 固定版本 7f08adcf…\n单卡 181.5 × 318，在 375px 舞台居中；保持原稿双列卡片的实际尺寸。',
                                '照片与头像暂取自 4× 预览裁切；照片内的“6”角标已烘焙，尚未独立验证。标题、作者、在线标签、心形均为原生组件；媒体区域不计入独立还原评分。'),
                            _sample(
                                'gender_none',
                                '新增 / 性别选择 · 未选择',
                                350,
                                'assets/reference/gender_none.png',
                                GenderSelection(
                                    onSelect: (value) => event('gender_none',
                                        '已触发 onSelect($value)。下方保留女生选中态供对照。')),
                                '完善性别-未选择 · 固定版本 9121ae6b…\n选项 134 × 164；圆角 22；图标圆盘 64 × 64；标题 30 / 42。',
                                '原始图标资源 + 原生文字、渐变背景、边框和阴影。左右选项均输出回调，预览保持固定状态以便对照。'),
                            _sample(
                                'gender_female',
                                '新增 / 性别选择 · 女生选中',
                                350,
                                'assets/reference/gender_female.png',
                                GenderSelection(
                                    femaleSelected: true,
                                    onSelect: (value) => event('gender_female',
                                        '已触发 onSelect($value)。')),
                                '完善性别-已选择 · 固定版本 6c06f0c3…\n选中填充 #FFF9EC / 边框 #DDAA5A；警示条 307 × 36。',
                                '勾选与警示图标使用原始导出。警示条右侧淡红盾牌的布尔路径缺失，暂用小图裁切并从评分中排除；当前只验证这两个有原稿的状态。'),
                            _sample(
                                'comments',
                                '新增 / 评论与嵌套回复',
                                374,
                                'assets/reference/comments.png',
                                CommentPanel(
                                    onClose: () =>
                                        event('comments', '已触发 onClose。'),
                                    onReply: (id) =>
                                        event('comments', '已触发 onReply($id)。'),
                                    onDelete: () => event(
                                        'comments', '已触发 onDelete；演示数据保留。'),
                                    onExpand: () => event('comments',
                                        '已触发 onExpand；源稿未提供展开后的三条内容。')),
                                '详情页-视频评论 · 固定版本 ae9eabab…\n一级头像 30，二级头像 24；正文 14 / 20；@momo 单独保留 #BC914A。',
                                '评论、作者标签、时间地区、回复层级均为原生渲染；关闭、回复、删除和展开可点击。头像暂用 4× 预览裁切，不计入独立还原评分。'),
                            _sample(
                                'modal',
                                '01 / 清除缓存弹窗',
                                280,
                                'assets/reference/modal.png',
                                ModalComponentStage(
                                    onCancel: () =>
                                        event('modal', '已触发 onCancel。'),
                                    onConfirm: () => event(
                                        'modal', '已触发 onConfirm；此处为组件演示。')),
                                '清除缓存 · 固定版本 f11338b7…\n面板 330 × 228 / 圆角 24；双按钮 140 × 46；遮罩 40%。',
                                '保留源稿主按钮文案“清除记录”。外围设置列表也是 Flutter 绘制；操作后保留样本，便于继续对照。'),
                            _sample(
                                'nav',
                                '02 / 五项底部导航',
                                98,
                                'assets/reference/nav.png',
                                NavigationComponentStage(
                                    onSelect: (i) => event('nav',
                                        '已触发 onSelect($i)：${JuxingBottomNavigation.labels[i]}。')),
                                '首页备份 2 · 固定版本 32aa246d…\n导航 347 × 56；左侧 14；圆角 28；原始首页图标 + 原稿矢量路径。',
                                '待验证：消息图标外轮廓缺少原始路径，当前为近似描绘；毛玻璃仅验证了这张浅色背景。当前仅核对首页选中态，点击返回导航事件。'),
                            _sample(
                                'appeal',
                                '03 / 处罚申诉业务卡片',
                                125,
                                'assets/reference/appeal.png',
                                AppealComponentStage(
                                    onAppeal: () =>
                                        event('appeal', '已触发 onAppeal。')),
                                '登录受限-1 · 固定版本 84ebb977…\n卡片 343 × 116；左侧 16；圆角 18；原始盾牌资源保留 5% 图层透明度。',
                                '标题、状态、字段、分隔线、渐变按钮均为 Flutter 原生绘制。图片型业务卡片见新增的动态卡片样本。'),
                            _sample(
                                'login',
                                '04 / 登录按钮与协议',
                                395,
                                'assets/reference/reference-region.png',
                                LoginComponentStage(
                                    onProviderTap: (id) =>
                                        event('login', '已触发 $id 登录按钮。')),
                                '登录-普通登录 · 固定版本 18f1a6ed…\n4 个 299 × 50 按钮；5 份原始图标；苹方 14 / 20。',
                                '保留已核对的默认态与协议未勾选态。'),
                            const Padding(
                                padding: EdgeInsets.fromLTRB(24, 8, 24, 20),
                                child: Text(
                                    '验证范围：固定版本、默认状态、375px 基线。截图相似不代表整套组件和全部状态已通过；本页明确保留数据缺口。',
                                    style: TextStyle(
                                        fontSize: 12,
                                        color: Color(0xFF65717E),
                                        height: 1.6))),
                          ]))))));

  Widget _sample(String id, String title, double height, String asset,
      Widget implementation, String facts, String notes) {
    final reference = Image.asset(asset,
        width: 375,
        height: height,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high);
    Widget panel(String label, Widget child) => SizedBox(
        width: 375,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Text(label,
                  style:
                      const TextStyle(fontSize: 12, color: Color(0xFF65717E)))),
          child,
        ]));
    return Padding(
        padding: const EdgeInsets.only(top: 32),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(title,
                  style: const TextStyle(
                      fontSize: 20, fontWeight: FontWeight.w600))),
          const SizedBox(height: 16),
          LayoutBuilder(
              builder: (context, box) => SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: SizedBox(
                      width: box.maxWidth < 375 ? 375 : box.maxWidth,
                      child: Wrap(
                          alignment: WrapAlignment.center,
                          spacing: 24,
                          runSpacing: 16,
                          children: [
                            if (mode == 'compare')
                              panel(
                                  '蓝湖原稿 · 375 × ${height.toInt()}', reference),
                            if (mode != 'overlay')
                              panel('Flutter 实现 · 375 × ${height.toInt()}',
                                  implementation),
                            if (mode == 'overlay')
                              panel(
                                  '叠加对照 · 375px',
                                  SizedBox(
                                      width: 375,
                                      height: height,
                                      child: Stack(children: [
                                        implementation,
                                        IgnorePointer(
                                            child: Opacity(
                                                opacity: opacity,
                                                child: reference)),
                                      ]))),
                          ])))),
          Container(
              margin: const EdgeInsets.fromLTRB(24, 16, 24, 0),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                  color: Colors.white, borderRadius: BorderRadius.circular(12)),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(facts,
                        style: const TextStyle(fontSize: 12, height: 1.7)),
                    const SizedBox(height: 6),
                    Text(notes,
                        style: const TextStyle(
                            fontSize: 12,
                            height: 1.7,
                            color: Color(0xFF65717E))),
                    const SizedBox(height: 8),
                    Text(events[id] ?? '可点击右侧组件，查看回调。',
                        key: ValueKey('event-$id'),
                        style: const TextStyle(
                            fontSize: 12, color: Color(0xFF314354))),
                  ])),
        ]));
  }
}
