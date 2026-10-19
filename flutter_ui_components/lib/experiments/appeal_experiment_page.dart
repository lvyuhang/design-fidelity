import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../components/expanded_components.dart';
import 'appeal_direct.dart';

class AppealExperimentPage extends StatefulWidget {
  const AppealExperimentPage(
      {this.galleryBuilder, this.evaluationData, super.key});
  final WidgetBuilder? galleryBuilder;
  final Map<String, dynamic>? evaluationData;
  @override
  State<AppealExperimentPage> createState() => _AppealExperimentPageState();
}

class _AppealExperimentPageState extends State<AppealExperimentPage> {
  static const assets = 'assets/experiments/appeal-direct';
  static const labels = ['蓝湖原稿', 'MCP 直接实现', '已有校准版'];
  String selectedRegion = 'button';
  String mode = 'compare';
  double opacity = .5;
  String directEvent = '点击申诉，查看回调';
  String calibratedEvent = '点击申诉，查看回调';
  late final Future<Map<String, dynamic>> evaluation =
      widget.evaluationData != null
          ? Future.value(widget.evaluationData!)
          : rootBundle
              .loadString('$assets/evaluation.json')
              .then((text) => jsonDecode(text) as Map<String, dynamic>);

  Widget _bodyText(String text) => Text(text,
      style:
          const TextStyle(fontSize: 13, height: 1.7, color: Color(0xFF65717E)));
  Widget _title(String text) => Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Text(text,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600)));
  Widget _stage(int index) => switch (index) {
        0 => Image.asset('$assets/reference.png',
            width: 375, height: 125, fit: BoxFit.fill),
        1 => DirectAppealStage(
            onAppeal: () => setState(() => directEvent = '已触发直接实现版 onAppeal')),
        _ => AppealComponentStage(
            onAppeal: () =>
                setState(() => calibratedEvent = '已触发校准版 onAppeal')),
      };

  Widget _panel(int index, Widget child, {String? footnote}) => SizedBox(
      width: 375,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 10),
            child: Row(children: [
              Text(labels[index],
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600)),
              const Spacer(),
              Text(
                  index == 1
                      ? '首版冻结 · 0 次视觉修正'
                      : (index == 0 ? '固定版本基准' : '此前的实现'),
                  style: TextStyle(
                      fontSize: 11,
                      color: index == 1
                          ? const Color(0xFF397165)
                          : const Color(0xFF65717E))),
            ])),
        child,
        if (footnote != null)
          Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: _bodyText(footnote)),
      ]));

  Widget _panels(List<Widget> children) => LayoutBuilder(
      builder: (context, box) => SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
              width: math.max(375, box.maxWidth),
              child: Wrap(
                  alignment: WrapAlignment.center,
                  spacing: 24,
                  runSpacing: 28,
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
                                              builder: widget.galleryBuilder!));
                                    }
                                  },
                                  icon: const Icon(Icons.arrow_back, size: 16),
                                  label: const Text('返回全部组件')),
                              const SizedBox(height: 16),
                              const Text('实验 01 / MCP 直接实现',
                                  style: TextStyle(
                                      fontSize: 12,
                                      letterSpacing: 1,
                                      color: Color(0xFF397165))),
                              const SizedBox(height: 10),
                              const Text('不做视觉校正，会还原成什么样？',
                                  style: TextStyle(
                                      fontSize: 28,
                                      fontWeight: FontWeight.w600)),
                              const SizedBox(height: 10),
                              _bodyText('处罚申诉业务卡片 · 同一蓝湖版本 · 同一字体 · 375px 预览'),
                              const SizedBox(height: 18),
                              Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                      color: const Color(0xFFE8EFEC),
                                      borderRadius: BorderRadius.circular(12)),
                                  child: const Text(
                                      '本例结果：直接实现已很接近。主要额外偏差出现在分隔线，文字与背景填充的测量结果与校准版相同。',
                                      style: TextStyle(
                                          fontSize: 14,
                                          height: 1.7,
                                          color: Color(0xFF304F45)))),
                              const SizedBox(height: 14),
                              _bodyText(
                                  '先独立编写并冻结代码，再截图测量；测量后未修改组件。初始输入含 MCP 返回的原稿预览、节点与图标。当前会话已有上次实现知识，本案例不是严格盲测。'),
                              const SizedBox(height: 24),
                              Wrap(spacing: 8, runSpacing: 8, children: [
                                for (final item in [
                                  ('compare', '三版对照'),
                                  ('overlay', '叠加：原稿 / 直接版')
                                ])
                                  ChoiceChip(
                                      label: Text(item.$2),
                                      selected: mode == item.$1,
                                      onSelected: (_) =>
                                          setState(() => mode = item.$1)),
                              ]),
                            ])),
                    const SizedBox(height: 24),
                    if (mode == 'compare')
                      _panels([
                        _panel(0, _stage(0), footnote: '卡片 343 × 116，左右边距 16'),
                        _panel(1, _stage(1), footnote: directEvent),
                        _panel(2, _stage(2), footnote: calibratedEvent),
                      ])
                    else
                      Column(children: [
                        Center(
                            child: SizedBox(
                                width: 375,
                                height: 125,
                                child: Stack(children: [
                                  _stage(1),
                                  IgnorePointer(
                                      child: Opacity(
                                          opacity: opacity, child: _stage(0))),
                                ]))),
                        Center(
                            child: SizedBox(
                                width: 375,
                                child: Slider(
                                    value: opacity,
                                    onChanged: (v) =>
                                        setState(() => opacity = v)))),
                        _bodyText(
                            '原稿 ${(opacity * 100).round()}% · 0% 仅直接实现，100% 仅原稿'),
                      ]),
                    const SizedBox(height: 30),
                    FutureBuilder<Map<String, dynamic>>(
                        future: evaluation,
                        builder: (context, snapshot) {
                          if (snapshot.hasError)
                            return const Padding(
                                padding: EdgeInsets.all(24),
                                child: Text('测量文件读取失败，请重新构建预览。'));
                          if (!snapshot.hasData)
                            return const Center(
                                child: CircularProgressIndicator());
                          final report = snapshot.data!;
                          final regions = Map<String, dynamic>.from(
                              report['regions'] as Map);
                          final region = regions[selectedRegion] as Map;
                          final rect = (region['rect'] as List).cast<num>();
                          final scale = math.min(4.0, 343 / rect[2]);
                          return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Padding(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 24),
                                    child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          _title('局部放大，查看偏差'),
                                          _bodyText(
                                              '以下来自同一次 4× 测试截图；切换区域不会修改冻结组件。'),
                                          const SizedBox(height: 12),
                                          Wrap(
                                              spacing: 8,
                                              runSpacing: 8,
                                              children: [
                                                for (final entry
                                                    in regions.entries.where(
                                                        (e) => e.key != 'card'))
                                                  ChoiceChip(
                                                      key: ValueKey(
                                                          'region-${entry.key}'),
                                                      label: Text(
                                                          entry.value['label']),
                                                      selected:
                                                          selectedRegion ==
                                                              entry.key,
                                                      onSelected: (_) =>
                                                          setState(() =>
                                                              selectedRegion =
                                                                  entry.key)),
                                              ]),
                                          const SizedBox(height: 16),
                                        ])),
                                _panels([
                                  for (var i = 0; i < 3; i++)
                                    _panel(
                                        i,
                                        Container(
                                            width: 375,
                                            height: 148,
                                            decoration: BoxDecoration(
                                                color: Colors.white,
                                                borderRadius:
                                                    BorderRadius.circular(12)),
                                            child: Center(
                                                child: Image.asset(
                                                    '$assets/$selectedRegion-${[
                                                      'reference',
                                                      'direct',
                                                      'calibrated'
                                                    ][i]}.png',
                                                    width: rect[2] * scale,
                                                    height: rect[3] * scale,
                                                    filterQuality:
                                                        FilterQuality.none))),
                                        footnote:
                                            '${region['label']} · ${scale.toStringAsFixed(1)}×'),
                                ]),
                                Padding(
                                    padding: const EdgeInsets.fromLTRB(
                                        24, 28, 24, 0),
                                    child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          _title('测量结果'),
                                          _bodyText(
                                              'RGB 平均绝对误差（0–255），越低越接近原稿。未经坐标拟合或缩放；这些数值不是“还原度百分比”。'),
                                          const SizedBox(height: 14),
                                          SingleChildScrollView(
                                              scrollDirection: Axis.horizontal,
                                              child: DataTable(
                                                  headingRowColor:
                                                      const WidgetStatePropertyAll(
                                                          Color(0xFFE8EBEF)),
                                                  columnSpacing: 30,
                                                  horizontalMargin: 14,
                                                  dataRowMinHeight: 36,
                                                  dataRowMaxHeight: 40,
                                                  headingRowHeight: 38,
                                                  columns: const [
                                                    DataColumn(
                                                        label: Text('区域')),
                                                    DataColumn(
                                                        label: Text('直接实现'),
                                                        numeric: true),
                                                    DataColumn(
                                                        label: Text('已有校准版'),
                                                        numeric: true)
                                                  ],
                                                  rows: [
                                                    for (final entry
                                                        in regions.entries)
                                                      DataRow(cells: [
                                                        DataCell(Text(
                                                            entry
                                                                .value['label'],
                                                            style:
                                                                const TextStyle(
                                                                    fontSize:
                                                                        12))),
                                                        DataCell(Text(
                                                            (entry.value['direct']
                                                                        ['mae']
                                                                    as num)
                                                                .toStringAsFixed(
                                                                    4),
                                                            style:
                                                                const TextStyle(
                                                                    fontSize:
                                                                        12))),
                                                        DataCell(Text(
                                                            (entry.value['calibrated']
                                                                        ['mae']
                                                                    as num)
                                                                .toStringAsFixed(
                                                                    4),
                                                            style:
                                                                const TextStyle(
                                                                    fontSize:
                                                                        12))),
                                                      ])
                                                  ])),
                                          const SizedBox(height: 18),
                                          _bodyText(
                                              '分隔线：MCP 的原始路径有约 0.54px 的纵向变化，首版使用了水平 Divider，差异保留。文字区域：两版结果相同，仍有字体栅格化差异。盾牌：两版使用同一份原始 PNG，不能据此评价矢量重建能力。'),
                                          const SizedBox(height: 12),
                                          _bodyText(
                                              '边界：仅一次实现、一个组件、默认状态。未额外调用底层 API 补查，也未复用已有校准绘制器；已有会话知识和字体准备仍影响结果。后续测量只用来展示差异，没有回写组件。'),
                                          const SizedBox(height: 12),
                                          ExpansionTile(
                                              tilePadding: EdgeInsets.zero,
                                              title: const Text('实验记录与测量条件',
                                                  style:
                                                      TextStyle(fontSize: 13)),
                                              children: [
                                                Align(
                                                    alignment:
                                                        Alignment.centerLeft,
                                                    child: Column(
                                                        crossAxisAlignment:
                                                            CrossAxisAlignment
                                                                .start,
                                                        children: [
                                                          _bodyText(
                                                              '蓝湖版本：${report['source_version']}'),
                                                          _bodyText(
                                                              '冻结代码 SHA-256：'),
                                                          SelectableText(
                                                              report[
                                                                  'code_sha256'],
                                                              style:
                                                                  const TextStyle(
                                                                      fontSize:
                                                                          11,
                                                                      height:
                                                                          1.6)),
                                                          const SizedBox(
                                                              height: 8),
                                                          _bodyText(
                                                              '组件视觉修正 0 次；编译 / 运行修复 0 次。测量前统一开启两版的真实阴影模糊，修正了测试工具默认关闭 BoxShadow 模糊的问题。测试引擎指标与浏览器检查分别记录。'),
                                                          const SizedBox(
                                                              height: 12),
                                                        ])),
                                              ]),
                                        ])),
                              ]);
                        }),
                    const SizedBox(height: 40),
                  ])),
        ),
      )));
}
