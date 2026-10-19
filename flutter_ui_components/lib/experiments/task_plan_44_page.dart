import 'dart:math' as math;

import 'package:flutter/material.dart';

class TaskPlan44Screen extends StatelessWidget {
  const TaskPlan44Screen({
    super.key,
    this.onBack,
    this.onMessage,
    this.onComplete,
  });

  final VoidCallback? onBack;
  final VoidCallback? onMessage;
  final VoidCallback? onComplete;

  static const size = Size(375, 812);
  static const ink = Color(0xFF22242A);
  static const gold = Color(0xFFE6B55E);
  static const muted = Color(0xFFA6AAB5);

  @override
  Widget build(BuildContext context) => SizedBox(
        width: size.width,
        height: size.height,
        child: ClipRect(
          child: ColoredBox(
            color: const Color(0xFFFFFCF6),
            child: Stack(
              children: [
                _header(),
                const Positioned(
                  left: 0,
                  top: 375,
                  width: 375,
                  height: 12,
                  child: IgnorePointer(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Color(0x50D6A44A),
                            Color(0x47D6A44A),
                            Color(0x26D6A44A),
                            Color(0x18D6A44A),
                            Color(0x08D6A44A),
                            Color(0x00D6A44A),
                          ],
                          stops: [0, .15, .4, .62, .8, 1],
                        ),
                      ),
                    ),
                  ),
                ),
                _taskCard(
                  top: 387,
                  time: '07:00–08:00',
                  title: '叫醒铃声',
                  subtitle: '录制5–60s叫醒语音',
                  icon: 0,
                  action: '去完成',
                  onTap: onComplete,
                ),
                _taskCard(
                  top: 515,
                  time: '21:00–22:00',
                  title: '睡前陪伴',
                  subtitle: '语音陪伴不少于10分钟',
                  icon: 1,
                  action: '未开始',
                ),
                _taskCard(
                  top: 643,
                  time: '01:00–02:00',
                  title: '失眠哄睡',
                  subtitle: '语音陪伴不少于10分钟',
                  icon: 2,
                  expired: true,
                ),
                _taskCard(
                  top: 771,
                  time: '17:00–18:00',
                  title: '下午陪伴',
                  subtitle: '语音陪伴不少于10分钟',
                  icon: 1,
                  disabled: true,
                ),
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
              ],
            ),
          ),
        ),
      );

  Widget _header() => Positioned(
        left: 0,
        top: 0,
        width: 375,
        height: 375,
        child: DecoratedBox(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
          ),
          child: Stack(
            children: [
              const Positioned.fill(
                  child: CustomPaint(painter: _HeaderGlowPainter())),
              _text('9:41', 21, 14.33, 54, 18, 15, 18, Colors.black,
                  family: 'SourcePingFang', align: TextAlign.center),
              const Positioned(
                left: 294,
                top: 17,
                width: 67,
                height: 12,
                child: CustomPaint(painter: _DarkStatusPainter()),
              ),
              Positioned(
                left: 10,
                top: 55,
                width: 28,
                height: 28,
                child: Semantics(
                  button: true,
                  label: '返回',
                  child: GestureDetector(
                    key: const ValueKey('task-plan-back'),
                    behavior: HitTestBehavior.opaque,
                    onTap: onBack,
                    child: const CustomPaint(painter: _BackPainter()),
                  ),
                ),
              ),
              _text('任务计划', 156, 55, 64, 22, 16, 22, ink,
                  weight: FontWeight.w600),
              Positioned(
                left: 18,
                top: 103,
                width: 50,
                height: 50,
                child: const _MissingAssetBlock(
                  label: '头像\n未切图',
                  shape: BoxShape.circle,
                ),
              ),
              const Positioned(
                left: 52,
                top: 140,
                width: 12,
                height: 12,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: Color(0xFF1EBA3E),
                    shape: BoxShape.circle,
                    border: Border.fromBorderSide(
                      BorderSide(color: Colors.white, width: 1),
                    ),
                  ),
                ),
              ),
              _text('送礼大神', 80, 108, 56, 20, 14, 20, ink,
                  weight: FontWeight.w600),
              _text(
                  '（温度的司机）', 137, 109, 84, 17, 12, 17, const Color(0xFFB6A58E)),
              Positioned(
                left: 80,
                top: 130,
                width: 100,
                height: 22,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF8EA),
                    borderRadius: BorderRadius.circular(16),
                    border:
                        Border.all(color: const Color(0x33D6A44A), width: .5),
                  ),
                  child: Stack(
                    children: [
                      const Positioned(
                        left: 8,
                        top: 4,
                        width: 14,
                        height: 14,
                        child: _MissingAssetBlock(
                          label: '缺',
                          shape: BoxShape.circle,
                          compact: true,
                        ),
                      ),
                      const Positioned(
                        left: 24,
                        top: 3,
                        width: 57,
                        height: 16,
                        child: Text(
                          '和Ta的关系',
                          textScaler: TextScaler.noScaling,
                          style: TextStyle(
                            inherit: false,
                            decoration: TextDecoration.none,
                            fontFamily: 'SourcePingFang',
                            fontSize: 11,
                            height: 16 / 11,
                            color: Color(0xFFB27A31),
                          ),
                        ),
                      ),
                      const Positioned(
                        left: 88,
                        top: 8,
                        width: 3,
                        height: 6,
                        child: CustomPaint(painter: _SmallChevronPainter()),
                      ),
                    ],
                  ),
                ),
              ),
              Positioned(
                left: 252,
                top: 112,
                width: 106,
                height: 32,
                child: Semantics(
                  button: true,
                  label: '发私信',
                  child: GestureDetector(
                    key: const ValueKey('task-plan-message'),
                    behavior: HitTestBehavior.opaque,
                    onTap: onMessage,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF111113), Color(0xFF352719)],
                        ),
                        borderRadius: BorderRadius.circular(25),
                        border: Border.all(
                            color: const Color(0xFFB6883D), width: .55),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 16,
                            height: 16,
                            child: _MissingAssetBlock(
                              label: '缺',
                              shape: BoxShape.circle,
                              compact: true,
                            ),
                          ),
                          SizedBox(width: 6),
                          Text(
                            '发私信',
                            textScaler: TextScaler.noScaling,
                            style: TextStyle(
                              inherit: false,
                              decoration: TextDecoration.none,
                              fontFamily: 'SourcePingFang',
                              fontSize: 12,
                              height: 17 / 12,
                              fontWeight: FontWeight.w600,
                              color: gold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              Positioned(
                left: 17,
                top: 160,
                width: 340,
                height: 28,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xB3FFF8F2),
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              ),
              _text('备注：周末畅聊，喜欢语音聊天', 39, 165, 190, 17, 12, 17,
                  const Color(0xFFD58C43)),
              _planProgressCard(),
              for (final item in const [
                (17.0, '16', '未完成', Color(0xFFFFF2F2), Color(0xFFD9443A)),
                (67.0, '17', '', Color(0xFFEAFAE9), Color(0xFF22242A)),
                (117.0, '18', '今天', Color(0xFF22242A), Color(0xFFE6B55E)),
                (167.0, '19', '未开始', Color(0xFFF1F2F4), Color(0xFF22242A)),
                (217.0, '20', '未开始', Color(0xFFF1F2F4), Color(0xFF22242A)),
                (267.0, '21', '未开始', Color(0xFFF1F2F4), Color(0xFF22242A)),
                (317.0, '22', '到期', Color(0xFFF1F2F4), Color(0xFF22242A)),
              ])
                _datePill(item.$1, item.$2, item.$3, item.$4, item.$5),
            ],
          ),
        ),
      );

  Widget _planProgressCard() => Positioned(
        left: 16,
        top: 204,
        width: 343,
        height: 93,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0x66FFF3DE), Color(0x00FFF3DE)],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0x66FFF8E9), width: .6),
          ),
          child: Stack(
            children: [
              Positioned(
                left: 254,
                top: 27,
                width: 77,
                height: 6,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0x80FFDF9D),
                    borderRadius: BorderRadius.circular(99),
                  ),
                ),
              ),
              const Positioned(
                left: 17,
                top: 15,
                width: 20,
                height: 20,
                child: _MissingAssetBlock(label: '缺', compact: true),
              ),
              _text('初级任务包  7天', 43, 13, 150, 24, 17, 24, ink,
                  weight: FontWeight.w600),
              _text('到期', 254, 17, 25, 14, 10.2, 12, const Color(0xFFB6A58E)),
              _text('07月22日', 279, 16, 55, 17, 12, 17, const Color(0xFFB6A58E),
                  weight: FontWeight.w600),
              _text('任务进度（最低完成 5 个）', 19, 49, 150, 15, 10.8, 15,
                  const Color(0xFFB6A58E)),
              _text('4 / 7', 301, 50, 28, 14, 12, 14, Colors.black),
              Positioned(
                left: 19,
                top: 69,
                width: 306,
                height: 6,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFEFEF),
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
              Positioned(
                left: 19,
                top: 69,
                width: 158,
                height: 6,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8C77B),
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
              const Positioned(
                left: 169,
                top: 67,
                width: 10,
                height: 10,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                      color: Color(0xFF171512), shape: BoxShape.circle),
                ),
              ),
            ],
          ),
        ),
      );

  Widget _datePill(
      double left, String day, String state, Color background, Color dayColor) {
    final active = day == '18';
    final done = day == '17';
    return Positioned(
      left: left,
      top: 305,
      width: 40,
      height: 60,
      child: DecoratedBox(
        decoration: BoxDecoration(
            color: background, borderRadius: BorderRadius.circular(20)),
        child: Stack(
          children: [
            _text(day, day == '20' ? 12 : 13, 13, 18, 20, 14, 20, dayColor,
                weight: FontWeight.w600),
            if (done)
              const Positioned(
                left: 14,
                top: 36,
                width: 13.3333333333,
                height: 10,
                child: CustomPaint(painter: _CheckPainter()),
              )
            else if (state.isNotEmpty)
              _text(
                state,
                state.length == 2 ? 10 : 5,
                34,
                state.length == 2 ? 22 : 32,
                14,
                10,
                14,
                active
                    ? const Color(0xFFEAEBF0)
                    : (day == '16' ? const Color(0xFFD9443A) : muted),
              ),
          ],
        ),
      ),
    );
  }

  Widget _taskCard({
    required double top,
    required String time,
    required String title,
    required String subtitle,
    required int icon,
    String? action,
    bool expired = false,
    bool disabled = false,
    VoidCallback? onTap,
  }) =>
      Positioned(
        left: 16,
        top: top,
        width: 343,
        height: 120,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xF9FFFFFF),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.white, width: .7),
            boxShadow: const [
              BoxShadow(color: Color(0x1FE8C77B), blurRadius: 16),
            ],
          ),
          child: Opacity(
            opacity: disabled ? .64 : 1,
            child: Stack(
              children: [
                _text(
                    time,
                    18,
                    16,
                    120,
                    25,
                    18,
                    25,
                    expired
                        ? const Color(0xFFD9443A)
                        : (disabled
                            ? const Color(0xFF686B77)
                            : const Color(0xFF18181B)),
                    weight: FontWeight.w600),
                Positioned(
                  left: icon == 0 ? 17 : 19,
                  top: 53,
                  width: icon == 0 ? 39 : 38,
                  height: icon == 0 ? 39 : 38,
                  child: const _MissingAssetBlock(label: '未切图'),
                ),
                _text(title, 63, 60, 100, 21, 15, 21, const Color(0xFF18181B)),
                _text(subtitle, 63, 84, 150, 17, 12, 17, muted),
                if (action != null)
                  Positioned(
                    left: 247,
                    top: 60,
                    width: 78,
                    height: 28,
                    child: Semantics(
                      button: onTap != null,
                      label: action,
                      child: GestureDetector(
                        key: ValueKey(
                          action == '去完成'
                              ? 'task-plan-complete'
                              : 'task-plan-pending',
                        ),
                        behavior: HitTestBehavior.opaque,
                        onTap: onTap,
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: action == '去完成'
                                ? const Color(0x33E8C77B)
                                : const Color(0xFFEFE8DD),
                            borderRadius: BorderRadius.circular(14),
                            border: action == '去完成'
                                ? Border.all(
                                    color: const Color(0x33D6A44A), width: .5)
                                : null,
                          ),
                          child: action == '去完成'
                              ? const Stack(
                                  children: [
                                    Positioned(
                                      left: 19,
                                      top: 6,
                                      width: 36,
                                      height: 17,
                                      child: Text(
                                        '去完成',
                                        textScaler: TextScaler.noScaling,
                                        style: TextStyle(
                                          inherit: false,
                                          decoration: TextDecoration.none,
                                          fontFamily: 'SourcePingFang',
                                          fontSize: 12,
                                          height: 17 / 12,
                                          fontWeight: FontWeight.w600,
                                          color: Color(0xFFB27A31),
                                        ),
                                      ),
                                    ),
                                    Positioned(
                                      left: 59,
                                      top: 11,
                                      width: 3,
                                      height: 6,
                                      child: CustomPaint(
                                        painter: _SmallChevronPainter(
                                          color: Color(0xFFB27A31),
                                        ),
                                      ),
                                    ),
                                  ],
                                )
                              : Center(
                                  child: Text(
                                    action,
                                    textScaler: TextScaler.noScaling,
                                    style: const TextStyle(
                                      inherit: false,
                                      decoration: TextDecoration.none,
                                      fontFamily: 'SourcePingFang',
                                      fontSize: 12,
                                      height: 17 / 12,
                                      color: Color(0xFFB6A58E),
                                    ),
                                  ),
                                ),
                        ),
                      ),
                    ),
                  ),
                if (expired)
                  const Positioned(
                    left: 254,
                    top: 32,
                    width: 65,
                    height: 65,
                    child: _MissingAssetBlock(
                      label: '印章\n未切图',
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
          ),
        ),
      );

  static Widget _text(
    String value,
    double x,
    double y,
    double width,
    double height,
    double fontSize,
    double lineHeight,
    Color color, {
    FontWeight weight = FontWeight.w400,
    String family = 'SourcePingFang',
    TextAlign align = TextAlign.left,
  }) =>
      Positioned(
        left: x,
        top: y,
        width: width,
        height: height,
        child: Text(
          value,
          softWrap: false,
          overflow: TextOverflow.visible,
          textAlign: align,
          textScaler: TextScaler.noScaling,
          style: TextStyle(
            inherit: false,
            decoration: TextDecoration.none,
            fontFamily: family,
            fontSize: fontSize,
            height: lineHeight / fontSize,
            leadingDistribution: TextLeadingDistribution.even,
            fontWeight: weight,
            color: color,
          ),
        ),
      );
}

class TaskPlan44Page extends StatefulWidget {
  const TaskPlan44Page({super.key});

  @override
  State<TaskPlan44Page> createState() => _TaskPlan44PageState();
}

class _TaskPlan44PageState extends State<TaskPlan44Page> {
  String mode = 'compare';
  double opacity = .5;
  String? eventText;

  Widget _source() => Image.asset(
        'assets/reference/task_plan_44.png',
        width: 375,
        height: 812,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );

  Widget _implementation() => TaskPlan44Screen(
        onBack: () => setState(() => eventText = '已触发返回'),
        onMessage: () => setState(() => eventText = '已触发发私信'),
        onComplete: () => setState(() => eventText = '已触发去完成'),
      );

  Widget _panel(String label, String badge, Widget child) => SizedBox(
        width: 375,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                children: [
                  Expanded(
                      child: Text(label,
                          style: const TextStyle(fontWeight: FontWeight.w600))),
                  Text(badge,
                      style: const TextStyle(
                          fontSize: 11, color: Color(0xFF65717E))),
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
                      offset: Offset(0, 6))
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
    if (mode == 'compare') {
      return _row([
        _panel('蓝湖原稿', '固定版本 · 4×', _source()),
        _panel('Flutter 原生实现', '375 × 812', _implementation()),
      ]);
    }
    if (mode == 'source') return _row([_panel('蓝湖原稿', '固定版本 · 4×', _source())]);
    if (mode == 'flutter')
      return _row([_panel('Flutter 原生实现', '375 × 812', _implementation())]);
    return Column(
      children: [
        _row([
          _panel(
            '叠加：蓝湖 / Flutter',
            '原稿 ${(opacity * 100).round()}%',
            Stack(children: [
              _implementation(),
              IgnorePointer(child: Opacity(opacity: opacity, child: _source()))
            ]),
          ),
        ]),
        SizedBox(
          width: 375,
          child: Slider(
              value: opacity,
              onChanged: (value) => setState(() => opacity = value)),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('1备份 44 · Flutter 还原')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 36),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('蓝湖固定快照 / Flutter 原生页面',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              const Text(
                '画布固定 375×812。页头、任务进度、日期状态和任务卡由 Flutter 原生绘制；蓝湖未导出的头像和业务图标统一显示为“未切图”色块，并保持原素材的圆形或矩形外形。',
                style: TextStyle(color: Color(0xFF65717E), height: 1.55),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final item in const [
                    ('compare', '左右对比'),
                    ('source', '只看原稿'),
                    ('flutter', '只看 Flutter'),
                    ('overlay', '叠加对照'),
                  ])
                    ChoiceChip(
                      label: Text(item.$2),
                      selected: mode == item.$1,
                      onSelected: (_) => setState(() => mode = item.$1),
                    ),
                ],
              ),
              if (eventText != null) ...[
                const SizedBox(height: 10),
                Text(eventText!,
                    style: const TextStyle(color: Color(0xFF137A52))),
              ],
              const SizedBox(height: 18),
              _result(),
            ],
          ),
        ),
      );
}

class _HeaderGlowPainter extends CustomPainter {
  const _HeaderGlowPainter();

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(
      Offset.zero & size,
      Paint()
        ..shader = const RadialGradient(
          center: Alignment(-.68, -.8),
          radius: .7,
          colors: [Color(0x33FCD4FF), Color(0x00FFFFFF)],
        ).createShader(Offset.zero & size),
    );
    canvas.drawRect(
      Offset.zero & size,
      Paint()
        ..shader = const RadialGradient(
          center: Alignment(.78, -.93),
          radius: .72,
          colors: [Color(0x73FFE39E), Color(0x00FFFFFF)],
        ).createShader(Offset.zero & size),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _DarkStatusPainter extends CustomPainter {
  const _DarkStatusPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
            Rect.fromLTWH(i * 4.7, 8 - i * 2.1, 3.2, 4 + i * 2.1),
            const Radius.circular(1)),
        black,
      );
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(23, 0, 16, 12), math.pi * 1.18,
        math.pi * .64, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(26, 4, 10, 7), math.pi * 1.18,
        math.pi * .64, false, wifi);
    canvas.drawCircle(const Offset(31, 10.5), 1.2, black);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(42.3, .3, 22, 11.3), const Radius.circular(2.6)),
      Paint()
        ..color = const Color(0x66000000)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(44.3, 2.3, 18, 7.3), const Radius.circular(1.2)),
      black,
    );
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(65.3, 4, 1.3, 4), const Radius.circular(.6)),
        black);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _BackPainter extends CustomPainter {
  const _BackPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = const Color(0xFF22242A)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(
        Path()
          ..moveTo(16, 6)
          ..lineTo(10, 14)
          ..lineTo(16, 22),
        p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _CheckPainter extends CustomPainter {
  const _CheckPainter();
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawPath(
      Path()
        ..moveTo(0, size.height * .5)
        ..lineTo(size.width * .3312693536, size.height)
        ..lineTo(size.width, 0),
      Paint()
        ..color = const Color(0xFF83C685)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MissingAssetBlock extends StatelessWidget {
  const _MissingAssetBlock({
    required this.label,
    this.shape = BoxShape.rectangle,
    this.compact = false,
  });

  final String label;
  final BoxShape shape;
  final bool compact;

  @override
  Widget build(BuildContext context) => Semantics(
        label: '设计素材未切图：$label',
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFFFFE5EA),
            shape: shape,
            borderRadius:
                shape == BoxShape.rectangle ? BorderRadius.circular(8) : null,
            border: Border.all(color: const Color(0xFFFF4D6D), width: 1),
          ),
          child: Center(
            child: Text(
              label,
              textAlign: TextAlign.center,
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                inherit: false,
                decoration: TextDecoration.none,
                fontFamily: 'SourcePingFang',
                fontSize: compact ? 7 : 8,
                height: 1.15,
                fontWeight: FontWeight.w600,
                color: Color(0xFFC52245),
              ),
            ),
          ),
        ),
      );
}

class _SmallChevronPainter extends CustomPainter {
  const _SmallChevronPainter({this.color = const Color(0xFFA97A31)});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawPath(
      Path()
        ..moveTo(0, 0)
        ..lineTo(size.width, size.height * .5)
        ..lineTo(0, size.height),
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(covariant _SmallChevronPainter oldDelegate) =>
      oldDelegate.color != color;
}

