import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../components/expanded_components.dart';
import '../components/login_components.dart';
import '../components/social_components.dart';
import 'gender_experiment_page.dart';
import 'gender_sol56_direct.dart';
import 'login_sol56.dart';
import 'social_sol56.dart';
import 'utility_sol56.dart';

class ComponentsModelComparisonPage extends StatefulWidget {
  const ComponentsModelComparisonPage({
    super.key,
    this.galleryBuilder,
    this.evaluationData,
    this.genderEvaluationData,
  });

  final WidgetBuilder? galleryBuilder;
  final Map<String, dynamic>? evaluationData;
  final Map<String, dynamic>? genderEvaluationData;

  @override
  State<ComponentsModelComparisonPage> createState() =>
      _ComponentsModelComparisonPageState();
}

class _ComponentsModelComparisonPageState
    extends State<ComponentsModelComparisonPage> {
  static const _assetRoot = 'assets/experiments/components-sol56';
  static const _samples = <_Sample>[
    _Sample('feed', '图文动态卡片', 342, 'independent', '照片与头像为蓝湖预览裁切；独立指标排除媒体区。'),
    _Sample('comments', '评论与嵌套回复', 374, 'independent', '头像为蓝湖预览裁切；独立指标排除三个头像。'),
    _Sample('modal', '清除缓存弹窗', 280, 'whole', null),
    _Sample('nav', '五项底部导航', 98, 'whole', '消息图标缺少原始路径，两版均为近似绘制。'),
    _Sample('appeal', '处罚申诉业务卡片', 125, 'whole', null),
    _Sample('login', '登录按钮与协议', 395, 'whole', null),
    _Sample('gender', '性别选择', 350, 'common', '性别组件保留独立实验页，可查看未选择与女生选中两种状态。'),
  ];

  String sampleId = 'feed';
  String mode = 'compare';
  String genderState = 'none';
  double opacity = .5;
  String? eventText;

  late final Future<Map<String, dynamic>> evaluation =
      widget.evaluationData != null
          ? Future.value(widget.evaluationData!)
          : rootBundle
              .loadString('$_assetRoot/evaluation.json')
              .then((value) => jsonDecode(value) as Map<String, dynamic>);
  late final Future<Map<String, dynamic>> genderEvaluation =
      widget.genderEvaluationData != null
          ? Future.value(widget.genderEvaluationData!)
          : rootBundle
              .loadString('assets/experiments/gender-direct/evaluation.json')
              .then((value) => jsonDecode(value) as Map<String, dynamic>);

  _Sample get sample => _samples.firstWhere((item) => item.id == sampleId);

  void _event(String value) => setState(() => eventText = value);

  Widget _source() => Image.asset(
        sampleId == 'gender'
            ? 'assets/experiments/gender-direct/$genderState-reference.png'
            : '$_assetRoot/$sampleId-reference.png',
        width: 375,
        height: sample.height,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );

  Widget _implementation(String variant) {
    final sol56 = variant == 'sol56';
    return switch (sampleId) {
      'feed' => sol56
          ? Sol56FeedComponentStage(
              onOpen: () => _event('5.6：onOpen'),
              onLike: () => _event('5.6：onLike'),
              onProfile: () => _event('5.6：onProfile'),
            )
          : FeedComponentStage(
              onOpen: () => _event('GPT-6：onOpen'),
              onLike: () => _event('GPT-6：onLike'),
              onProfile: () => _event('GPT-6：onProfile'),
            ),
      'comments' => sol56
          ? Sol56CommentPanel(
              onClose: () => _event('5.6：onClose'),
              onDelete: () => _event('5.6：onDelete'),
              onExpand: () => _event('5.6：onExpand'),
              onReply: (id) => _event('5.6：onReply($id)'),
            )
          : CommentPanel(
              onClose: () => _event('GPT-6：onClose'),
              onDelete: () => _event('GPT-6：onDelete'),
              onExpand: () => _event('GPT-6：onExpand'),
              onReply: (id) => _event('GPT-6：onReply($id)'),
            ),
      'modal' => sol56
          ? Sol56ModalComponentStage(
              onCancel: () => _event('5.6：onCancel'),
              onConfirm: () => _event('5.6：onConfirm'),
            )
          : ModalComponentStage(
              onCancel: () => _event('GPT-6：onCancel'),
              onConfirm: () => _event('GPT-6：onConfirm'),
            ),
      'nav' => sol56
          ? Sol56NavigationComponentStage(
              onSelect: (index) => _event('5.6：onSelect($index)'),
            )
          : NavigationComponentStage(
              onSelect: (index) => _event('GPT-6：onSelect($index)'),
            ),
      'appeal' => sol56
          ? Sol56AppealComponentStage(
              onAppeal: () => _event('5.6：onAppeal'),
            )
          : AppealComponentStage(
              onAppeal: () => _event('GPT-6：onAppeal'),
            ),
      'login' => sol56
          ? Sol56LoginComponentStage(
              onProviderTap: (id) => _event('5.6：$id'),
            )
          : LoginComponentStage(
              onProviderTap: (id) => _event('GPT-6：$id'),
            ),
      _ => sol56
          ? Sol56GenderSelection(
              femaleSelected: genderState == 'female',
              onSelect: (value) => _event('5.6：onSelect($value)'),
            )
          : GenderSelection(
              femaleSelected: genderState == 'female',
              onSelect: (value) => _event('GPT-6：onSelect($value)'),
            ),
    };
  }

  Widget _canvas(Widget child) => SizedBox(
        width: 375,
        height: sample.height,
        child: ColoredBox(color: Colors.white, child: child),
      );

  Widget _panel(String label, String badge, Widget child) => SizedBox(
        width: 375,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
            child: Row(children: [
              Expanded(
                child: Text(label,
                    style: const TextStyle(
                        fontSize: 14, fontWeight: FontWeight.w600)),
              ),
              Text(badge,
                  style:
                      const TextStyle(fontSize: 11, color: Color(0xFF65717E))),
            ]),
          ),
          _canvas(child),
        ]),
      );

  Widget _panelRow(List<Widget> panels) => LayoutBuilder(
        builder: (context, constraints) => SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: math.max(375, constraints.maxWidth),
            child: Wrap(
              alignment: WrapAlignment.center,
              spacing: 24,
              runSpacing: 24,
              children: panels,
            ),
          ),
        ),
      );

  Widget _comparison() {
    if (mode == 'compare') {
      return _panelRow([
        _panel('蓝湖原稿', '同版本基准', _source()),
        _panel(
            'GPT-5.6 Sol · high', '首版冻结 · 0 次视觉修正', _implementation('sol56')),
        _panel('此前 GPT-6', '已核对实现', _implementation('gpt6')),
      ]);
    }
    if (mode == 'sol56' || mode == 'gpt6') {
      final isSol = mode == 'sol56';
      return _panelRow([
        _panel(
          isSol ? 'GPT-5.6 Sol · high' : '此前 GPT-6',
          isSol ? '首版冻结' : '已核对实现',
          _implementation(mode),
        ),
      ]);
    }
    final variant = mode == 'overlay-sol56' ? 'sol56' : 'gpt6';
    return Column(children: [
      _panelRow([
        _panel(
          variant == 'sol56' ? '叠加：原稿 / 5.6 Sol' : '叠加：原稿 / GPT-6',
          '原稿 ${(opacity * 100).round()}%',
          Stack(children: [
            _implementation(variant),
            IgnorePointer(child: Opacity(opacity: opacity, child: _source())),
          ]),
        ),
      ]),
      SizedBox(
        width: 375,
        child: Slider(
          key: const ValueKey('overlay-opacity'),
          value: opacity,
          onChanged: (value) => setState(() => opacity = value),
        ),
      ),
    ]);
  }

  Widget _metrics() => FutureBuilder<List<Map<String, dynamic>>>(
        future: Future.wait([evaluation, genderEvaluation]),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return const Text('像素测量文件读取失败。');
          }
          if (!snapshot.hasData) {
            return const LinearProgressIndicator();
          }
          final Map region;
          final String note;
          if (sampleId == 'gender') {
            final states = snapshot.data![1]['states'] as Map;
            region = ((states[genderState] as Map)['regions'] as Map)['common']
                as Map;
            note = '性别 common 区域；详细局部指标见独立实验页。';
          } else {
            final samples = snapshot.data![0]['samples'] as Map;
            final item = samples[sampleId] as Map;
            region = (item['regions'] as Map)[sample.metricRegion] as Map;
            note = sample.note ?? '完整 375px 舞台。';
          }
          final metricKey = sampleId == 'gender' ? 'mae' : 'mean_abs_rgb_0_255';
          final sol = (region['sol56'] as Map)[metricKey];
          final gpt6Key = sampleId == 'gender' ? 'calibrated' : 'gpt6';
          final gpt6 = (region[gpt6Key] as Map)[metricKey];
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFE8EFEC),
              borderRadius: BorderRadius.circular(12),
            ),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('同网格平均 RGB 绝对误差（0–255）',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Wrap(spacing: 24, runSpacing: 8, children: [
                Text('GPT-5.6 Sol：$sol'),
                Text('此前 GPT-6：$gpt6'),
              ]),
              const SizedBox(height: 7),
              Text(note,
                  style: const TextStyle(
                      fontSize: 12, height: 1.5, color: Color(0xFF4D625C))),
            ]),
          );
        },
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1221),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              TextButton.icon(
                                onPressed: () {
                                  if (Navigator.canPop(context)) {
                                    Navigator.pop(context);
                                  } else if (widget.galleryBuilder != null) {
                                    Navigator.pushReplacement(
                                      context,
                                      MaterialPageRoute(
                                          builder: widget.galleryBuilder!),
                                    );
                                  }
                                },
                                icon: const Icon(Icons.arrow_back, size: 16),
                                label: const Text('返回全部组件'),
                              ),
                              const SizedBox(height: 12),
                              const Text('实验 03 / 多组件模型对比',
                                  style: TextStyle(
                                      fontSize: 12,
                                      letterSpacing: 1,
                                      color: Color(0xFF397165))),
                              const SizedBox(height: 8),
                              const Text('同一份蓝湖输入：5.6 首版与此前 GPT-6',
                                  style: TextStyle(
                                      fontSize: 28,
                                      fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              const Text(
                                '每块预览固定 375px。5.6 Sol · high 在隔离任务中读取蓝湖证据，冻结后才首次渲染，未做视觉修正。此前 GPT-6 列是已核对、修正过的当前实现，因此这是一项工作流对比，不是严格的模型排行榜。像素指标来自 Flutter debug 测试引擎，会把 5.6 固定文本框触发的溢出诊断条计入误差；当前 Web release 预览不会显示诊断条。',
                                style: TextStyle(
                                    fontSize: 13,
                                    height: 1.65,
                                    color: Color(0xFF65717E)),
                              ),
                              const SizedBox(height: 18),
                              Wrap(spacing: 8, runSpacing: 8, children: [
                                for (final item in _samples)
                                  ChoiceChip(
                                    key: ValueKey('sample-${item.id}'),
                                    label: Text(item.label),
                                    selected: sampleId == item.id,
                                    onSelected: (_) => setState(() {
                                      sampleId = item.id;
                                      eventText = null;
                                    }),
                                  ),
                              ]),
                              const SizedBox(height: 12),
                              Wrap(spacing: 8, runSpacing: 8, children: [
                                for (final item in const [
                                  ('compare', '三版对照'),
                                  ('sol56', '仅 5.6 Sol'),
                                  ('gpt6', '仅此前 GPT-6'),
                                  ('overlay-sol56', '叠加 原稿/5.6'),
                                  ('overlay-gpt6', '叠加 原稿/GPT-6'),
                                ])
                                  ChoiceChip(
                                    key: ValueKey('mode-${item.$1}'),
                                    label: Text(item.$2),
                                    selected: mode == item.$1,
                                    onSelected: (_) =>
                                        setState(() => mode = item.$1),
                                  ),
                              ]),
                              if (sampleId == 'gender') ...[
                                const SizedBox(height: 12),
                                Wrap(spacing: 8, children: [
                                  for (final item in const [
                                    ('none', '未选择'),
                                    ('female', '女生选中'),
                                  ])
                                    ChoiceChip(
                                      key: ValueKey('gender-${item.$1}'),
                                      label: Text(item.$2),
                                      selected: genderState == item.$1,
                                      onSelected: (_) =>
                                          setState(() => genderState = item.$1),
                                    ),
                                  TextButton(
                                    onPressed: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                          builder: (_) =>
                                              const GenderExperimentPage()),
                                    ),
                                    child: const Text('查看性别详细实验'),
                                  ),
                                ]),
                              ],
                            ]),
                      ),
                      const SizedBox(height: 24),
                      _comparison(),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(24, 18, 24, 0),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (eventText != null)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 12),
                                  child: Text('交互事件：$eventText',
                                      style: const TextStyle(
                                          fontSize: 13,
                                          color: Color(0xFF397165))),
                                ),
                              _metrics(),
                              if (sample.note != null) ...[
                                const SizedBox(height: 12),
                                Text('资源说明：${sample.note}',
                                    style: const TextStyle(
                                        fontSize: 12,
                                        height: 1.6,
                                        color: Color(0xFF65717E))),
                              ],
                            ]),
                      ),
                    ]),
              ),
            ),
          ),
        ),
      );
}

class _Sample {
  const _Sample(this.id, this.label, this.height, this.metricRegion, this.note);

  final String id;
  final String label;
  final double height;
  final String metricRegion;
  final String? note;
}
