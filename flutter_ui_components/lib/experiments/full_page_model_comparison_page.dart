import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'full_page_gpt6.dart';
import 'full_page_gpt6_r1.dart';
import 'full_page_gpt6_r2.dart';
import 'full_page_sol56.dart';
import 'full_page_sol56_r1.dart';
import 'full_page_sol56_r2.dart';

class FullPageModelComparisonPage extends StatefulWidget {
  const FullPageModelComparisonPage({super.key, this.evaluationData});

  final Map<String, dynamic>? evaluationData;

  @override
  State<FullPageModelComparisonPage> createState() =>
      _FullPageModelComparisonPageState();
}

class _FullPageModelComparisonPageState
    extends State<FullPageModelComparisonPage> {
  String mode = 'compare';
  String revision = 'r2';
  double opacity = .5;
  String? eventText;

  late final Future<Map<String, dynamic>> evaluation =
      widget.evaluationData != null
          ? Future.value(widget.evaluationData!)
          : rootBundle
              .loadString('assets/lanhu/full_page/evaluation.json')
              .then((value) => jsonDecode(value) as Map<String, dynamic>);

  void _event(String value) => setState(() => eventText = value);

  Widget _source() => Image.asset(
        'assets/lanhu/full_page/reference.png',
        width: 375,
        height: 812,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );

  Widget _implementation(String variant) {
    if (variant == 'sol56' && revision == 'r2') {
      return Sol56PlatformIntroPageR2(
        onSkip: () => _event('GPT-5.6 Sol R2：onSkip'),
        onStart: () => _event('GPT-5.6 Sol R2：onStart'),
      );
    }
    if (variant == 'gpt6' && revision == 'r2') {
      return Gpt6PlatformIntroPageR2(
        onSkip: () => _event('GPT-6 R2：onSkip'),
        onStart: () => _event('GPT-6 R2：onStart'),
      );
    }
    if (variant == 'sol56' && revision == 'r1') {
      return Sol56PlatformIntroPageR1(
        onSkip: () => _event('GPT-5.6 Sol R1：onSkip'),
        onStart: () => _event('GPT-5.6 Sol R1：onStart'),
      );
    }
    if (variant == 'gpt6' && revision == 'r1') {
      return Gpt6PlatformIntroPageR1(
        onSkip: () => _event('GPT-6 R1：onSkip'),
        onStart: () => _event('GPT-6 R1：onStart'),
      );
    }
    return variant == 'sol56'
        ? Sol56PlatformIntroPage(
            onSkip: () => _event('GPT-5.6 Sol：onSkip'),
            onStart: () => _event('GPT-5.6 Sol：onStart'),
          )
        : Gpt6PlatformIntroPage(
            onSkip: () => _event('GPT-6：onSkip'),
            onStart: () => _event('GPT-6：onStart'),
          );
  }

  String get _roundBadge => switch (revision) {
        'r2' => '自动校准 R2 · 最终结果',
        'r1' => '视觉修正 R1 · 1 轮',
        _ => '独立首版 · 0 次视觉修正',
      };

  Widget _frame(Widget child) => SizedBox(
        width: 375,
        height: 812,
        child: ColoredBox(color: Colors.white, child: child),
      );

  Widget _panel(String label, String badge, Widget child) => SizedBox(
        width: 375,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      label,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  Text(
                    badge,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF65717E),
                    ),
                  ),
                ],
              ),
            ),
            DecoratedBox(
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFDDE1E6)),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x16000000),
                    blurRadius: 16,
                    offset: Offset(0, 6),
                  ),
                ],
              ),
              child: _frame(child),
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

  Widget _comparison() {
    if (mode == 'compare') {
      return _row([
        _panel('蓝湖原稿', '固定版本 · 4×', _source()),
        _panel(
          'GPT-5.6 Sol · high',
          _roundBadge,
          _implementation('sol56'),
        ),
        _panel(
          'GPT-6 · high',
          _roundBadge,
          _implementation('gpt6'),
        ),
      ]);
    }
    if (mode == 'source' || mode == 'sol56' || mode == 'gpt6') {
      return _row([
        if (mode == 'source') _panel('蓝湖原稿', '固定版本 · 4×', _source()),
        if (mode == 'sol56')
          _panel('GPT-5.6 Sol · high', _roundBadge, _implementation('sol56')),
        if (mode == 'gpt6')
          _panel('GPT-6 · high', _roundBadge, _implementation('gpt6')),
      ]);
    }
    final variant = mode == 'overlay-sol56' ? 'sol56' : 'gpt6';
    return Column(
      children: [
        _row([
          _panel(
            variant == 'sol56' ? '叠加：蓝湖 / GPT-5.6 Sol' : '叠加：蓝湖 / GPT-6',
            '原稿 ${(opacity * 100).round()}%',
            Stack(
              children: [
                _implementation(variant),
                IgnorePointer(
                  child: Opacity(opacity: opacity, child: _source()),
                ),
              ],
            ),
          ),
        ]),
        SizedBox(
          width: 375,
          child: Slider(
            key: const ValueKey('full-page-overlay-opacity'),
            value: opacity,
            onChanged: (value) => setState(() => opacity = value),
          ),
        ),
      ],
    );
  }

  Widget _metrics() => FutureBuilder<Map<String, dynamic>>(
        future: evaluation,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return const Text('像素测量文件读取失败。');
          }
          if (!snapshot.hasData) return const LinearProgressIndicator();
          final whole = (snapshot.data!['regions'] as Map)['whole'] as Map;
          final native = (snapshot.data!['regions'] as Map)['native'] as Map;
          String value(Map region, String model) =>
              ((region[model] as Map)['mean_abs_rgb_0_255'] as num)
                  .toStringAsFixed(2);
          final solKey = switch (revision) {
            'r2' => 'sol56_r2',
            'r1' => 'sol56_r1',
            _ => 'sol56',
          };
          final gpt6Key = switch (revision) {
            'r2' => 'gpt6_r2',
            'r1' => 'gpt6_r1',
            _ => 'gpt6',
          };
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFFE3E6EA)),
            ),
            child: Wrap(
              spacing: 28,
              runSpacing: 8,
              children: [
                Text('整页 MAE：5.6 ${value(whole, solKey)}'),
                Text('整页 MAE：GPT-6 ${value(whole, gpt6Key)}'),
                Text('原生结构 MAE：5.6 ${value(native, solKey)}'),
                Text('原生结构 MAE：GPT-6 ${value(native, gpt6Key)}'),
                const Text(
                  'MAE 范围 0–255，越低越接近；不是还原度百分比。',
                  style: TextStyle(color: Color(0xFF65717E)),
                ),
                if (revision == 'r1')
                  const Text(
                    'R1 的 4× 测试渲染缺少系统中文回退字体，因此 MAE 包含方框字形；Web 预览可正常使用浏览器字体，R0/R1 数值不宜直接判断 Web 视觉优劣。',
                    style: TextStyle(color: Color(0xFF9A5B18)),
                  ),
                if (revision == 'r2')
                  const Text(
                    'R2 使用蓝湖节点视觉契约校准可见像素边界，并补全嵌入字体字形。',
                    style: TextStyle(color: Color(0xFF137A52)),
                  ),
              ],
            ),
          );
        },
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('完整页面 · 模型还原对比')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 36),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '同一蓝湖快照 · 两种模型 · 自动校准结果',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              const Text(
                '三列均按 375×812 逻辑像素展示。默认显示自动校准后的 R2 最终结果，也可切回 R0 / R1 查看变化。',
                style: TextStyle(color: Color(0xFF65717E), height: 1.5),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final item in const [
                    ('r0', '首版 · 0 次修正'),
                    ('r1', 'R1 · 1 轮视觉修正'),
                    ('r2', 'R2 · 自动校准结果'),
                  ])
                    ChoiceChip(
                      key: ValueKey('full-page-revision-${item.$1}'),
                      label: Text(item.$2),
                      selected: revision == item.$1,
                      onSelected: (_) => setState(() => revision = item.$1),
                    ),
                ],
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final item in const [
                    ('compare', '三方对比'),
                    ('source', '只看原稿'),
                    ('sol56', '只看 5.6'),
                    ('gpt6', '只看 GPT-6'),
                    ('overlay-sol56', '叠加 5.6'),
                    ('overlay-gpt6', '叠加 GPT-6'),
                  ])
                    ChoiceChip(
                      key: ValueKey('full-page-mode-${item.$1}'),
                      label: Text(item.$2),
                      selected: mode == item.$1,
                      onSelected: (_) => setState(() => mode = item.$1),
                    ),
                ],
              ),
              if (eventText != null) ...[
                const SizedBox(height: 10),
                Text(eventText!, key: const ValueKey('full-page-event')),
              ],
              const SizedBox(height: 18),
              _metrics(),
              const SizedBox(height: 22),
              _comparison(),
            ],
          ),
        ),
      );
}
