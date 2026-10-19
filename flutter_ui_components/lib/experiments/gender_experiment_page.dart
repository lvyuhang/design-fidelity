import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../components/social_components.dart';
import 'gender_direct.dart';
import 'gender_sol56_direct.dart';

class GenderExperimentPage extends StatefulWidget {
  const GenderExperimentPage(
      {super.key, this.galleryBuilder, this.evaluationData});
  final WidgetBuilder? galleryBuilder;
  final Map<String, dynamic>? evaluationData;
  @override
  State<GenderExperimentPage> createState() => _GenderExperimentPageState();
}

class _GenderExperimentPageState extends State<GenderExperimentPage> {
  static const assets = 'assets/experiments/gender-direct';
  static const variants = ['reference', 'sol56', 'direct', 'calibrated'];
  static const labels = ['蓝湖原稿', 'GPT-5.6 Sol · high', 'GPT-6 首版', '已有校准版'];
  String state = 'none', mode = 'compare', selectedRegion = 'shadow';
  double opacity = .5;
  final events = <int, String>{};
  bool get femaleSelected => state == 'female';
  late final Future<Map<String, dynamic>> evaluation =
      widget.evaluationData != null
          ? Future.value(widget.evaluationData!)
          : rootBundle
              .loadString('$assets/evaluation.json')
              .then((value) => jsonDecode(value) as Map<String, dynamic>);

  Widget _text(String text) => Text(text,
      style: const TextStyle(
          fontSize: 13, height: 1.65, color: Color(0xFF65717E)));
  Widget _title(String text) => Text(text,
      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600));
  Widget _inset(Widget child) => Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24), child: child);
  void _event(int index, String value) =>
      setState(() => events[index] = '已触发 onSelect($value)；预览保留当前源稿状态。');
  Widget _stage(int index) => switch (index) {
        0 => Image.asset('$assets/$state-reference.png',
            width: 375, height: 350, fit: BoxFit.fill),
        1 => Sol56GenderSelection(
            femaleSelected: femaleSelected, onSelect: (v) => _event(1, v)),
        2 => DirectGenderSelection(
            femaleSelected: femaleSelected, onSelect: (v) => _event(2, v)),
        _ => GenderSelection(
            femaleSelected: femaleSelected, onSelect: (v) => _event(3, v)),
      };
  Widget _panel(int index, Widget child, {String? note}) => SizedBox(
      width: 375,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 10),
            child: Row(children: [
              Expanded(
                  child: Text(labels[index],
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 14, fontWeight: FontWeight.w600))),
              const SizedBox(width: 8),
              Text(
                  index == 1
                      ? '独立冻结 · 0 次视觉修正'
                      : (index == 2
                          ? '首版冻结 · 0 次视觉修正'
                          : (index == 0 ? '同版本基准' : '此前的实现')),
                  style: TextStyle(
                      fontSize: 11,
                      color: index == 1 || index == 2
                          ? const Color(0xFF397165)
                          : const Color(0xFF65717E))),
            ])),
        child,
        if (note != null)
          Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: _text(note)),
      ]));
  Widget _panels(List<Widget> children) => LayoutBuilder(
      builder: (context, box) => SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
              width: math.max(375, box.maxWidth),
              child: Wrap(
                  alignment: WrapAlignment.center,
                  spacing: 24,
                  runSpacing: 24,
                  children: children))));

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
                            _inset(Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  TextButton.icon(
                                      onPressed: () {
                                        if (Navigator.canPop(context)) {
                                          Navigator.pop(context);
                                        } else if (widget.galleryBuilder !=
                                            null) {
                                          Navigator.pushReplacement(
                                              context,
                                              MaterialPageRoute(
                                                  builder:
                                                      widget.galleryBuilder!));
                                        }
                                      },
                                      icon: const Icon(Icons.arrow_back,
                                          size: 16),
                                      label: const Text('返回全部组件')),
                                  const SizedBox(height: 14),
                                  const Text('实验 02 / 同输入模型对比',
                                      style: TextStyle(
                                          fontSize: 12,
                                          letterSpacing: 1,
                                          color: Color(0xFF397165))),
                                  const SizedBox(height: 8),
                                  const Text('性别选择：5.6 Sol 与 GPT-6 首版对比',
                                      style: TextStyle(
                                          fontSize: 28,
                                          fontWeight: FontWeight.w600)),
                                  const SizedBox(height: 8),
                                  _text(
                                      '未选择 / 女生选中 · 每块预览固定 375 × 350 · 同一套苹方字体与原始图标'),
                                  const SizedBox(height: 16),
                                  Container(
                                      width: double.infinity,
                                      padding: const EdgeInsets.all(16),
                                      decoration: BoxDecoration(
                                          color: const Color(0xFFE8EFEC),
                                          borderRadius:
                                              BorderRadius.circular(12)),
                                      child: const Text(
                                          '本例结果：5.6 Sol 的选中图标与角标定位很准；未选半透明卡片受到 BoxShadow 内部染色，文字还出现宽度溢出标记。GPT-6 首版使用了既有绘制经验，整体误差更低。',
                                          style: TextStyle(
                                              fontSize: 14,
                                              height: 1.65,
                                              color: Color(0xFF304F45)))),
                                  const SizedBox(height: 12),
                                  _text(
                                      '5.6 Sol · high 在隔离任务中只读取同一份 MCP 原稿、节点和五份原始切图，未查看现有实现或指标；代码冻结后才首次渲染。GPT-6 首版来自已有上下文，掌握过阴影与文字还原经验，所以这是一项实用对比，不是严格的模型基准测试。'),
                                  const SizedBox(height: 18),
                                  Wrap(spacing: 8, runSpacing: 8, children: [
                                    for (final item in const [
                                      ('none', '未选择'),
                                      ('female', '女生选中')
                                    ])
                                      ChoiceChip(
                                          key: ValueKey('state-${item.$1}'),
                                          label: Text(item.$2),
                                          selected: state == item.$1,
                                          onSelected: (_) => setState(() {
                                                state = item.$1;
                                                events.clear();
                                                if (!femaleSelected &&
                                                    [
                                                      'check',
                                                      'warning',
                                                      'warning_text',
                                                      'shield_gap'
                                                    ].contains(
                                                        selectedRegion)) {
                                                  selectedRegion = 'shadow';
                                                }
                                              })),
                                    const SizedBox(width: 12),
                                    for (final item in const [
                                      ('compare', '四版对照'),
                                      ('overlay-sol56', '叠加：原稿 / 5.6 Sol'),
                                      ('overlay-direct', '叠加：原稿 / GPT-6')
                                    ])
                                      ChoiceChip(
                                          key: ValueKey('mode-${item.$1}'),
                                          label: Text(item.$2),
                                          selected: mode == item.$1,
                                          onSelected: (_) =>
                                              setState(() => mode = item.$1)),
                                  ]),
                                ])),
                            const SizedBox(height: 24),
                            if (mode == 'compare')
                              _panels([
                                _panel(0, _stage(0),
                                    note: femaleSelected
                                        ? '源稿：完善性别-已选择 · 6c06f0c3…'
                                        : '源稿：完善性别-未选择 · 9121ae6b…'),
                                _panel(1, _stage(1),
                                    note: events[1] ??
                                        '5.6 Sol · high 独立首版；冻结后未修改。'),
                                _panel(2, _stage(2),
                                    note: events[2] ??
                                        'GPT-6 首版；冻结后未修改，含此前积累的绘制经验。'),
                                _panel(3, _stage(3),
                                    note: events[3] ??
                                        (femaleSelected
                                            ? '此前校准版；淡色盾牌使用原稿裁切。'
                                            : '此前已核对、修正的实现。')),
                              ])
                            else
                              Column(children: [
                                _panels([
                                  SizedBox(
                                      width: 375,
                                      height: 350,
                                      child: Stack(children: [
                                        _stage(mode == 'overlay-sol56' ? 1 : 2),
                                        IgnorePointer(
                                            child: Opacity(
                                                opacity: opacity,
                                                child: _stage(0))),
                                      ]))
                                ]),
                                Center(
                                    child: SizedBox(
                                        width: 375,
                                        child: Slider(
                                            value: opacity,
                                            onChanged: (v) =>
                                                setState(() => opacity = v)))),
                                _inset(_text(
                                    '原稿 ${(opacity * 100).round()}% · 0% 仅${mode == 'overlay-sol56' ? '5.6 Sol' : 'GPT-6 首版'}，100% 仅原稿')),
                              ]),
                            const SizedBox(height: 28),
                            FutureBuilder<Map<String, dynamic>>(
                                future: evaluation,
                                builder: (context, snapshot) {
                                  if (snapshot.hasError) {
                                    return _inset(
                                        const Text('测量文件读取失败，请重新构建预览。'));
                                  }
                                  if (!snapshot.hasData) {
                                    return const Center(
                                        child: CircularProgressIndicator());
                                  }
                                  final report = snapshot.data!;
                                  final current =
                                      report['states'][state] as Map;
                                  final regions = Map<String, dynamic>.from(
                                      current['regions'] as Map);
                                  final region = regions[selectedRegion] as Map;
                                  final rect =
                                      (region['rect'] as List).cast<num>();
                                  final scale = math.min(4.0,
                                      math.min(343 / rect[2], 220 / rect[3]));
                                  final common = regions['common'] as Map;
                                  return Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        _inset(Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              _title('局部放大，查看偏差'),
                                              const SizedBox(height: 8),
                                              _text(
                                                  '共同可验证区域 MAE：5.6 Sol ${common['sol56']['mae']} / GPT-6 首版 ${common['direct']['mae']} / 校准版 ${common['calibrated']['mae']}。'),
                                              const SizedBox(height: 12),
                                              SizedBox(
                                                  width: 360,
                                                  child: DropdownButtonFormField<
                                                          String>(
                                                      key: ValueKey(
                                                          'region-selector-$state-$selectedRegion'),
                                                      initialValue:
                                                          selectedRegion,
                                                      isExpanded: true,
                                                      decoration:
                                                          const InputDecoration(
                                                              labelText: '放大区域',
                                                              border:
                                                                  OutlineInputBorder(),
                                                              isDense: true),
                                                      items: [
                                                        for (final entry
                                                            in regions.entries
                                                                .where((e) => ![
                                                                      'canvas',
                                                                      'common'
                                                                    ].contains(
                                                                        e.key)))
                                                          DropdownMenuItem(
                                                              value: entry.key,
                                                              child: Text(
                                                                  entry.value[
                                                                          'label']
                                                                      as String,
                                                                  style: const TextStyle(
                                                                      fontSize:
                                                                          13)))
                                                      ],
                                                      onChanged: (v) {
                                                        if (v != null) {
                                                          setState(() =>
                                                              selectedRegion =
                                                                  v);
                                                        }
                                                      })),
                                              const SizedBox(height: 10),
                                              _text(selectedRegion ==
                                                      'shield_gap'
                                                  ? '资源缺口：两个首版都只绘制可用外框和勾，内部布尔填充缺失；校准版该处为原稿裁切。低误差不能算独立还原成功。'
                                                  : '同一次 4× 测试截图，像素放大；本轮测量没有回写组件代码。'),
                                            ])),
                                        const SizedBox(height: 18),
                                        _panels([
                                          for (var i = 0; i < 4; i++)
                                            _panel(
                                                i,
                                                Container(
                                                    width: 375,
                                                    height: 244,
                                                    decoration: BoxDecoration(
                                                        color: Colors.white,
                                                        borderRadius:
                                                            BorderRadius
                                                                .circular(12)),
                                                    child: Center(
                                                        child: Image.asset(
                                                            '$assets/$state-$selectedRegion-${variants[i]}.png',
                                                            width:
                                                                rect[2] * scale,
                                                            height:
                                                                rect[3] * scale,
                                                            filterQuality:
                                                                FilterQuality
                                                                    .none))),
                                                note:
                                                    '${region['label']} · ${scale.toStringAsFixed(1)}×')
                                        ]),
                                        const SizedBox(height: 28),
                                        _inset(Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              _title('测量结果'),
                                              const SizedBox(height: 8),
                                              _text(
                                                  'RGB 平均绝对误差，范围 0–255，越低越接近。使用原生 4× 网格，未对齐优化或缩放；不是“还原度百分比”。大面积浅色背景会压低整体误差，应结合局部观察。'),
                                              const SizedBox(height: 12),
                                              SingleChildScrollView(
                                                  scrollDirection:
                                                      Axis.horizontal,
                                                  child: DataTable(
                                                      headingRowColor:
                                                          const WidgetStatePropertyAll(
                                                              Color(
                                                                  0xFFE8EBEF)),
                                                      columnSpacing: 28,
                                                      horizontalMargin: 14,
                                                      dataRowMinHeight: 36,
                                                      dataRowMaxHeight: 40,
                                                      headingRowHeight: 38,
                                                      columns: const [
                                                        DataColumn(
                                                            label: Text('区域')),
                                                        DataColumn(
                                                            label:
                                                                Text('5.6 Sol'),
                                                            numeric: true),
                                                        DataColumn(
                                                            label: Text(
                                                                'GPT-6 首版'),
                                                            numeric: true),
                                                        DataColumn(
                                                            label:
                                                                Text('已有校准版'),
                                                            numeric: true)
                                                      ],
                                                      rows: [
                                                        for (final entry
                                                            in regions.entries)
                                                          DataRow(cells: [
                                                            DataCell(Text(
                                                                entry.value[
                                                                    'label'],
                                                                style: const TextStyle(
                                                                    fontSize:
                                                                        12))),
                                                            for (final variant
                                                                in [
                                                              'sol56',
                                                              'direct',
                                                              'calibrated'
                                                            ])
                                                              DataCell(Text(
                                                                  (entry.value[variant]
                                                                              [
                                                                              'mae']
                                                                          as num)
                                                                      .toStringAsFixed(
                                                                          4),
                                                                  style: const TextStyle(
                                                                      fontSize:
                                                                          12))),
                                                          ])
                                                      ])),
                                              const SizedBox(height: 14),
                                              _text(
                                                  '共同可验证区与警示条指标：女生选中态对三种实现统一排除 (295, 299, 37, 34) 的盾牌区域；全画布与盾牌行保留完整差异。校准版的盾牌图片来自原稿裁切，不能用于证明绘制能力。'),
                                              const SizedBox(height: 10),
                                              _text(
                                                  '5.6 Sol 的未选卡片采用普通 BoxShadow，半透明填充让阴影染入内部；TextStyle 继承默认字距后，固定宽文本出现黄色溢出标记。其选中女生图标 MAE 0.0004、角标 0.0615，说明原始素材定位准确。GPT-6 首版预先使用外阴影裁除、显式字距和背景模糊映射经验。'),
                                              ExpansionTile(
                                                  tilePadding: EdgeInsets.zero,
                                                  title: const Text('实验记录与边界',
                                                      style: TextStyle(
                                                          fontSize: 13)),
                                                  children: [
                                                    Align(
                                                        alignment: Alignment
                                                            .centerLeft,
                                                        child: Column(
                                                            crossAxisAlignment:
                                                                CrossAxisAlignment
                                                                    .start,
                                                            children: [
                                                              _text(
                                                                  '当前源稿版本：${current['source_version']}'),
                                                              _text(
                                                                  'GPT-5.6 Sol 冻结代码 SHA-256：'),
                                                              SelectableText(
                                                                  report[
                                                                      'sol56_code_sha256'],
                                                                  style: const TextStyle(
                                                                      fontSize:
                                                                          11,
                                                                      height:
                                                                          1.6)),
                                                              const SizedBox(
                                                                  height: 8),
                                                              _text(
                                                                  '5.6 Sol · high：视觉修正 0 次、阻塞修复 0 次；隔离任务未读取现有实现、测试或指标。GPT-6 首版同样视觉修正 0 次，但来自已有上下文。两个首版均未复用校准绘制器、未补查底层 API、未用原稿裁切补图。'),
                                                              _text(
                                                                  'GPT-6 首版冻结 SHA-256：${report['code_sha256']}'),
                                                              _text(
                                                                  '测量从一开始为三种实现开启真实阴影模糊。测试引擎指标与浏览器展示分别验证；每个模型仅一次实现、两个源稿状态，不能外推为总体模型胜率。'),
                                                            ])),
                                                    const SizedBox(height: 12),
                                                  ]),
                                            ])),
                                      ]);
                                }),
                            const SizedBox(height: 40),
                          ]))))));
}
