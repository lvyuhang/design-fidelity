import 'package:flutter/material.dart';

class FilterBackupAssets {
  static const _root = 'assets/lanhu/filter_backup/assets';
  static const video =
      '$_root/fc05fb6a52689670465a7af5e9a55b4d6279033448b3f70a4a8f024227d7b387.png';
  static const voice =
      '$_root/3c666d24c748913934f325c9ad39fca42ce9d6b7255dff932ac09040a3fb7517.png';
  static const message =
      '$_root/397fc5b0acee81c8bda59c4baebf6ef5d7ce9244d6687b6c80ac53a690e9974c.png';
  static const close =
      '$_root/0d9ac1307d34b7b89ecb1c24a36db21a1678f026aa8fd0fbc37ffb1a309313ad.png';
  static const check1 =
      '$_root/b79115be417ebc97b0f0ab56d90aca92484ca1ef3636b88f303cdbaad02555bc.png';
  static const check2 =
      '$_root/a2b42278ccdbfd16621fe4e9f9ba3372829136362d2520da3f00594ee40f91e1.png';
  static const check3 =
      '$_root/f9e593fe624f4c2b6491e35625a241dea6f4fbde931e830ef6a3dfee4688c4bf.png';
  static const all = [video, voice, message, close, check1, check2, check3];
}

class FilterBackupPage extends StatelessWidget {
  const FilterBackupPage({
    super.key,
    this.onClose,
    this.onConfigure,
    this.onTaskTap,
    this.onEnabledTaskTap,
  });

  final VoidCallback? onClose;
  final VoidCallback? onConfigure;
  final ValueChanged<int>? onTaskTap;
  final ValueChanged<int>? onEnabledTaskTap;

  static const size = Size(375, 812);
  static const _ink = Color(0xFF18181B);
  static const _gold = Color(0xFFE6B55E);
  static const _muted = Color(0xFFA6AAB5);

  @override
  Widget build(BuildContext context) => SizedBox(
        width: size.width,
        height: size.height,
        child: ClipRect(
          child: DefaultTextStyle(
            style: const TextStyle(fontFamily: 'SourcePingFang'),
            child: Stack(
              children: [
                const Positioned.fill(
                    child: ColoredBox(color: Color(0xFFFEFDFA))),
                _discoveryPage(),
                const Positioned.fill(
                    child: ColoredBox(color: Color(0x66000000))),
                _sheet(),
                _statusBar(),
                _homeIndicator(),
              ],
            ),
          ),
        ),
      );

  Widget _discoveryPage() => Stack(
        children: [
          _text('发现', 22, 51, 52, 37, 26, 37, _ink, weight: FontWeight.w600),
          _text('★', 10, 51, 14, 18, 15, 18, const Color(0xFFE6B55E)),
          _text('我关注的', 89, 58, 64, 21, 15, 21, const Color(0xFF91919B)),
          _text('关注我的', 162, 58, 64, 21, 15, 21, const Color(0xFF91919B)),
          Positioned(
            left: 301,
            top: 56,
            width: 60,
            height: 26,
            child: DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(15),
                border: Border.all(color: const Color(0xFFD2CEC7)),
              ),
              child: Stack(children: [
                const Positioned(
                    left: 12,
                    top: 8,
                    width: 10,
                    height: 9.1666666667,
                    child: CustomPaint(painter: _FilterGlyphPainter())),
                _text('筛选', 27, 5, 22, 16, 11, 16, _ink),
              ]),
            ),
          ),
          _photoPlaceholder(8, '设计素材未切图：发现页照片 1'),
          _photoPlaceholder(190, '设计素材未切图：发现页照片 2'),
        ],
      );

  Widget _photoPlaceholder(double x, String label) => Positioned(
        left: x,
        top: 99,
        width: 177,
        height: 236,
        child: Semantics(
          image: true,
          label: label,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xFFFFE5EA),
              border: Border.all(color: const Color(0xFFFF4D6D)),
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Center(
              child: Text('未切图',
                  style: TextStyle(color: Color(0xFFC52245), fontSize: 12)),
            ),
          ),
        ),
      );

  Widget _sheet() => Stack(
        children: [
          Positioned(
            left: 0,
            top: 228,
            width: 375,
            height: 584,
            child: DecoratedBox(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment(-0.5219166577, -1),
                  end: Alignment(-0.5219166577, -0.3406127095),
                  colors: [Color(0xFFF8F1E1), Color(0xFFFFFFFF)],
                ),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                boxShadow: [
                  BoxShadow(
                      color: Color(0x4DE8C77B),
                      blurRadius: 26,
                      spreadRadius: -2,
                      offset: Offset(0, -12))
                ],
              ),
            ),
          ),
          const Positioned(
            left: 170,
            top: 241,
            width: 36,
            height: 1,
            child: DecoratedBox(
                decoration: BoxDecoration(
                    color: Color(0xFFD2D0D2),
                    borderRadius: BorderRadius.all(Radius.circular(3)))),
          ),
          _text('开通任务项，获取更多奖励', 25, 262, 216, 25, 18, 25, _ink,
              weight: FontWeight.w600),
          Positioned(
            left: 332,
            top: 258,
            width: 28,
            height: 28,
            child: Semantics(
              button: true,
              label: '关闭任务配置',
              child: GestureDetector(
                key: const ValueKey('filter-close'),
                behavior: HitTestBehavior.opaque,
                onTap: onClose,
                child: Center(
                    child: Image.asset(FilterBackupAssets.close,
                        width: 11, height: 11)),
              ),
            ),
          ),
          const Positioned(
              left: 25,
              top: 294,
              width: 16,
              height: 16,
              child: CustomPaint(painter: _BellPainter())),
          _text('已为你默认开启以下任务项，可前往设置奖励', 42, 294, 250, 17, 12, 17,
              const Color(0xFFBC914A)),
          Positioned(
            left: 23,
            top: 327,
            width: 329,
            height: 107,
            child: DecoratedBox(
              decoration: BoxDecoration(
                  color: const Color(0xC4FFFFFF),
                  borderRadius: BorderRadius.circular(18)),
            ),
          ),
          _text('已开启任务', 39, 338, 72, 17, 12, 17, const Color(0xFF22242A),
              weight: FontWeight.w600),
          _enabledItem(0, 67, FilterBackupAssets.video,
              FilterBackupAssets.check1, '视频通话'),
          _enabledItem(1, 172, FilterBackupAssets.voice,
              FilterBackupAssets.check2, '语音通话'),
          _enabledItem(2, 278, FilterBackupAssets.message,
              FilterBackupAssets.check3, '私信互动'),
          _text('待配置任务', 39, 448, 72, 17, 12, 17, const Color(0xFF22242A),
              weight: FontWeight.w600),
          Positioned(
            left: 23,
            top: 476,
            width: 329,
            height: 223,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xFFFFFCF6),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: Colors.white),
                boxShadow: const [
                  BoxShadow(
                      color: Color(0x4DE8C77B), blurRadius: 8, spreadRadius: -2)
                ],
              ),
            ),
          ),
          for (final top in [530.5, 586.5, 642.5])
            Positioned(
                left: 31.5,
                top: top,
                width: 314,
                height: 2,
                child: const ColoredBox(color: Color(0x1FE8C77B))),
          for (var i = 0; i < 4; i++) _taskRow(i),
          Positioned(
            left: 28,
            top: 727,
            width: 320,
            height: 50,
            child: Semantics(
              button: true,
              label: '去配置任务项',
              child: GestureDetector(
                key: const ValueKey('filter-configure'),
                behavior: HitTestBehavior.opaque,
                onTap: onConfigure,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                        colors: [Color(0xFF111111), Color(0xFF372D22)]),
                    borderRadius: BorderRadius.circular(25),
                    border: Border.all(color: const Color(0x66D6A44A)),
                    boxShadow: const [
                      BoxShadow(
                          color: Color(0x1AD6A44A),
                          blurRadius: 14,
                          offset: Offset(0, 8))
                    ],
                  ),
                  child: const Center(
                    child: Text('去配置任务项',
                        style: TextStyle(
                            fontFamily: 'SourcePingFang',
                            fontSize: 15,
                            height: 1.4,
                            fontWeight: FontWeight.w600,
                            color: _gold)),
                  ),
                ),
              ),
            ),
          ),
        ],
      );

  Widget _enabledItem(
          int index, double x, String icon, String check, String label) =>
      Positioned(
        left: x,
        top: 367,
        width: 40,
        height: 53,
        child: Semantics(
          button: true,
          label: '已开启任务：$label',
          child: GestureDetector(
            key: ValueKey('filter-enabled-$index'),
            behavior: HitTestBehavior.opaque,
            onTap: () => onEnabledTaskTap?.call(index),
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Image.asset(icon, width: 30, height: 30),
                Positioned(
                    left: index == 2 ? 22 : 21,
                    top: 18,
                    child: Image.asset(check, width: 12, height: 12)),
                Positioned(
                    left: index == 1 ? -8 : -9,
                    top: 34,
                    width: 48,
                    child: Text(label,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                            fontSize: 12, height: 17 / 12, color: _ink))),
              ],
            ),
          ),
        ),
      );

  Widget _taskRow(int index) {
    // These are source-node coordinates, not row container coordinates.  The
    // previous version added a second 7–9px inset to rows 2–4 and shifted the
    // entire visible row away from the Lanhu evidence.
    const tops = [488.0, 539.0, 597.0, 652.0];
    const iconTops = [0.0, 2.0, 1.0, 1.0];
    const subtitleTops = [20.0, 20.0, 21.67, 21.67];
    const statusTops = [9.0, 9.0, 10.0, 10.0];
    const fills = [
      Color(0xFFFFE29B),
      Color(0xFFE8C7FF),
      Color(0xFFFFC8D1),
      Color(0xFFDDBDFA)
    ];
    final top = tops[index];
    return Positioned(
      left: 31,
      top: top,
      width: 314,
      height: index < 2 ? 56 : 55,
      child: Semantics(
        button: true,
        label: '待配置叫醒服务 ${index + 1}',
        child: GestureDetector(
          key: ValueKey('filter-task-$index'),
          behavior: HitTestBehavior.opaque,
          onTap: () => onTaskTap?.call(index),
          child: Stack(
            children: [
              Positioned(
                left: 10,
                top: iconTops[index],
                child: Semantics(
                  image: true,
                  label: '设计素材未切图：叫醒服务图标 ${index + 1}',
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                        color: fills[index],
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0x66FF4D6D))),
                    child: const SizedBox(
                        width: 33,
                        height: 33,
                        child: Center(
                            child: Text('未切图',
                                style: TextStyle(
                                    fontSize: 6, color: Color(0xFFC52245))))),
                  ),
                ),
              ),
              Positioned(
                  left: index < 2 ? 48 : 51.1448275862,
                  top: 0,
                  child: const Text('叫醒服务',
                      style: TextStyle(
                          fontFamily: 'SourcePingFang',
                          fontSize: 13,
                          height: 18 / 13,
                          color: _ink))),
              Positioned(
                  left: index < 2 ? 48 : 51.1448275862,
                  top: subtitleTops[index],
                  child: const Text('录制至少 10 秒叫醒音频',
                      style: TextStyle(
                          fontFamily: 'SourcePingFang',
                          fontSize: 11,
                          height: 16 / 11,
                          color: _muted))),
              Positioned(
                  right: index < 2 ? 12 : 14,
                  top: statusTops[index],
                  child: const Text('未开通',
                      style: TextStyle(
                          fontFamily: 'SourcePingFang',
                          fontSize: 10,
                          height: 1.4,
                          color: Color(0xFFB27A31)))),
            ],
          ),
        ),
      ),
    );
  }

  static Widget _statusBar() => Stack(
        children: [
          Positioned(
              left: 34,
              top: 15.83,
              width: 41,
              height: 18,
              child: Text('9:41',
                  textAlign: TextAlign.left,
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                      inherit: false,
                      fontFamily: 'SourcePingFang',
                      fontSize: 15,
                      height: 18 / 15,
                      letterSpacing: -.3,
                      color: Colors.black))),
          const Positioned(
              left: 294,
              top: 17,
              width: 67,
              height: 14,
              child: CustomPaint(painter: _StatusPainter(dark: true))),
        ],
      );

  static Widget _homeIndicator() => const Positioned(
        left: 121,
        top: 799,
        width: 134,
        height: 5,
        child: DecoratedBox(
            decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.all(Radius.circular(3)))),
      );

  static Widget _text(String value, double x, double y, double width,
          double height, double fontSize, double lineHeight, Color color,
          {FontWeight weight = FontWeight.w400}) =>
      Positioned(
        left: x,
        top: y,
        width: width,
        height: height,
        child: Text(value,
            textScaler: TextScaler.noScaling,
            overflow: TextOverflow.visible,
            style: TextStyle(
                inherit: false,
                fontFamily: 'SourcePingFang',
                fontSize: fontSize,
                height: lineHeight / fontSize,
                leadingDistribution: TextLeadingDistribution.even,
                fontWeight: weight,
                color: color)),
      );
}

class _FilterGlyphPainter extends CustomPainter {
  const _FilterGlyphPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(0, 0)
      ..lineTo(size.width * .4, size.height * .5096303225)
      ..lineTo(size.width * .4, size.height * .8922545314)
      ..lineTo(size.width * .6, size.height)
      ..lineTo(size.width * .6, size.height * .5096303225)
      ..lineTo(size.width, 0)
      ..close();
    canvas.drawPath(
        path,
        Paint()
          ..color = const Color(0xFF333333)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _BellPainter extends CustomPainter {
  const _BellPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = const Color(0xFFBC914A);
    final path = Path()
      ..moveTo(3, 11)
      ..quadraticBezierTo(3, 4, 8, 3)
      ..quadraticBezierTo(13, 4, 13, 11)
      ..lineTo(15, 14)
      ..lineTo(1, 14)
      ..close();
    canvas.drawPath(path, paint);
    canvas.drawCircle(const Offset(8, 2), 1.2, paint);
    canvas.drawCircle(const Offset(8, 15), 1.2, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _StatusPainter extends CustomPainter {
  const _StatusPainter({required this.dark});
  final bool dark;
  @override
  void paint(Canvas canvas, Size size) {
    final c = dark ? Colors.black : Colors.white;
    final p = Paint()..color = c;
    for (var i = 0; i < 4; i++)
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.0, 10 - i * 2.4, 3, 4 + i * 2.4),
              const Radius.circular(1)),
          p);
    final wifi = Path()
      ..moveTo(23, 5)
      ..quadraticBezierTo(30.5, -1, 38, 5)
      ..moveTo(26, 8)
      ..quadraticBezierTo(30.5, 4, 35, 8)
      ..moveTo(29, 11)
      ..quadraticBezierTo(30.5, 9.5, 32, 11);
    canvas.drawPath(
        wifi,
        Paint()
          ..color = c
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..strokeCap = StrokeCap.round);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(44, 1, 22, 11), const Radius.circular(3)),
        Paint()
          ..color = c.withValues(alpha: .35)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(46, 3, 18, 7), const Radius.circular(1.5)),
        p);
  }

  @override
  bool shouldRepaint(covariant _StatusPainter oldDelegate) =>
      oldDelegate.dark != dark;
}
