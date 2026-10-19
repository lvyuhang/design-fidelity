import 'package:flutter/material.dart';

const _fontFamily = 'SourcePingFang';
const _ink = Color(0xFF22242A);
const _muted = Color(0xFF686B77);
const _gold = Color(0xFFE6B55E);
const _deepGold = Color(0xFFBC914A);
const _navInk = Color(0xFF18181B);

/// Frozen 375 x 280 reconstruction of the default clear-cache modal state.
class Sol56ModalComponentStage extends StatelessWidget {
  const Sol56ModalComponentStage({
    super.key,
    this.onCancel,
    this.onConfirm,
  });

  final VoidCallback? onCancel;
  final VoidCallback? onConfirm;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 375,
      height: 280,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          const Positioned.fill(child: ColoredBox(color: Colors.white)),
          const Positioned(
            left: 37,
            top: 7,
            width: 302,
            height: 1,
            child: ColoredBox(color: Color(0xFFE9EAF0)),
          ),
          const Positioned(
            left: 38,
            top: 239,
            child: Text(
              '清除聊天记录',
              style: TextStyle(
                fontFamily: _fontFamily,
                fontSize: 14,
                height: 20 / 14,
                color: _ink,
              ),
            ),
          ),
          const Positioned(
            left: 37,
            top: 273,
            width: 302,
            height: 1,
            child: ColoredBox(color: Color(0xFFE9EAF0)),
          ),
          const Positioned.fill(child: ColoredBox(color: Color(0x66000000))),
          Positioned(
            left: 23,
            top: 22,
            width: 330,
            height: 228,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x2E000000),
                    blurRadius: 30,
                    offset: Offset(0, 18),
                  ),
                ],
              ),
            ),
          ),
          const Positioned(
            left: 23,
            top: 49,
            width: 330,
            child: Text(
              '清除缓存',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: _fontFamily,
                fontSize: 20,
                fontWeight: FontWeight.w600,
                height: 28 / 20,
                color: _ink,
              ),
            ),
          ),
          const Positioned(
            left: 53,
            top: 85,
            width: 270,
            child: Text(
              '确定要清除所有缓存吗？',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: _fontFamily,
                fontSize: 14,
                height: 20 / 14,
                color: _muted,
              ),
            ),
          ),
          Positioned(
            left: 46,
            top: 117,
            width: 289,
            height: 39,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xB3FDF7F0), Color(0xB3FDF5EE)],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          const Positioned(
            left: 55,
            top: 129,
            child: Text(
              '预计可释放',
              style: TextStyle(
                fontFamily: _fontFamily,
                fontSize: 12,
                height: 17 / 12,
                color: _ink,
              ),
            ),
          ),
          const Positioned(
            right: 53,
            top: 128,
            child: Text(
              '128.6MB',
              style: TextStyle(
                fontFamily: _fontFamily,
                fontSize: 13,
                fontWeight: FontWeight.w600,
                height: 18 / 13,
                color: _deepGold,
              ),
            ),
          ),
          Positioned(
            left: 42,
            top: 179,
            width: 140,
            height: 46,
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onCancel,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xB3FFFDF9),
                  borderRadius: BorderRadius.circular(27),
                  border:
                      Border.all(color: const Color(0xFFE9B96D), width: 0.5),
                ),
                child: const Center(
                  child: Text(
                    '取消',
                    style: TextStyle(
                      fontFamily: _fontFamily,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      height: 21 / 15,
                      color: _deepGold,
                    ),
                  ),
                ),
              ),
            ),
          ),
          Positioned(
            left: 193,
            top: 178,
            width: 140,
            height: 46,
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onConfirm,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.centerRight,
                    end: Alignment.centerLeft,
                    colors: [Color(0xFF372D22), Color(0xFF111111)],
                  ),
                  borderRadius: BorderRadius.circular(25),
                  border: Border.all(color: const Color(0x66D6A44A)),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x1AD6A44A),
                      blurRadius: 14,
                      offset: Offset(0, 8),
                    ),
                  ],
                ),
                child: const Center(
                  child: Text(
                    '清除记录',
                    style: TextStyle(
                      fontFamily: _fontFamily,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      height: 21 / 15,
                      color: _gold,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Frozen 375 x 98 reconstruction of the home-selected bottom navigation.
class Sol56NavigationComponentStage extends StatelessWidget {
  const Sol56NavigationComponentStage({super.key, this.onSelect});

  final ValueChanged<int>? onSelect;

  @override
  Widget build(BuildContext context) {
    const centers = <double>[55, 121, 188, 255, 315];
    const labels = <String>['首页', '消息', '关系', '任务', '我的'];
    return SizedBox(
      width: 375,
      height: 98,
      child: Stack(
        children: [
          const Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment(0, 0.46),
                  colors: [Color(0x00FFFFFF), Colors.white],
                ),
              ),
            ),
          ),
          Positioned(
            left: 14,
            top: 21,
            width: 347,
            height: 56,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0xE6FCFBFA), Color(0xFFF0EDEC)],
                ),
                borderRadius: BorderRadius.circular(28),
                border: Border.all(color: Colors.white),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x33C9C7AF),
                    blurRadius: 4,
                    offset: Offset(0, 2),
                  ),
                  BoxShadow(
                    color: Color(0x33C9C7AF),
                    blurRadius: 4,
                    offset: Offset(0, -2),
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            left: 25,
            top: 28,
            width: 60,
            height: 43,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0x33E8C77B),
                borderRadius: BorderRadius.circular(20),
              ),
            ),
          ),
          const Positioned(
            left: 45,
            top: 34,
            width: 20,
            height: 18,
            child: Image(
              image: AssetImage(
                'assets/lanhu/nav/assets/a8071fdef24e364d65fb5159f6ac36f47d869667d188aca77e99a1fa52207622.png',
              ),
              fit: BoxFit.fill,
            ),
          ),
          const Positioned(
            left: 111,
            top: 34,
            width: 20,
            height: 19,
            child: CustomPaint(painter: _MessageIconPainter()),
          ),
          const Positioned(
            left: 179,
            top: 36,
            width: 18,
            height: 16,
            child: CustomPaint(painter: _HeartIconPainter()),
          ),
          const Positioned(
            left: 247,
            top: 34,
            width: 16,
            height: 18,
            child: CustomPaint(painter: _TaskIconPainter()),
          ),
          const Positioned(
            left: 306,
            top: 34,
            width: 18,
            height: 18,
            child: CustomPaint(painter: _ProfileIconPainter()),
          ),
          for (var index = 0; index < labels.length; index++)
            Positioned(
              left: centers[index] - 18,
              top: 58,
              width: 36,
              height: 10,
              child: Text(
                labels[index],
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: _fontFamily,
                  fontSize: 9,
                  height: 10 / 9,
                  color: index < 2 ? _navInk : const Color(0xFF7B7980),
                ),
              ),
            ),
          for (var index = 0; index < centers.length; index++)
            Positioned(
              left: centers[index] - 30,
              top: 24,
              width: 60,
              height: 50,
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: onSelect == null ? null : () => onSelect!(index),
              ),
            ),
          Positioned(
            left: 121,
            top: 85,
            width: 134,
            height: 5,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(100),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Frozen 375 x 125 reconstruction of the appeal-available penalty card.
class Sol56AppealComponentStage extends StatelessWidget {
  const Sol56AppealComponentStage({super.key, this.onAppeal});

  final VoidCallback? onAppeal;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 375,
      height: 125,
      child: Stack(
        children: [
          const Positioned.fill(child: ColoredBox(color: Color(0xFFFFFEFA))),
          Positioned(
            left: 16,
            top: 4,
            width: 343,
            height: 116,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment(-0.88, -1),
                  end: Alignment(0.78, 1),
                  colors: [Color(0xFFFFFCF8), Color(0xFFFFF9F4)],
                ),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFFCF4EE)),
              ),
            ),
          ),
          const Positioned(
            left: 278,
            top: 12,
            width: 68,
            height: 79,
            child: Opacity(
              opacity: 0.05,
              child: Image(
                image: AssetImage(
                  'assets/lanhu/appeal/assets/3c01e52ce3c5fd7658e2bb85964bf19046d219e3f4f0a6e2e1562aefded0f5b4.png',
                ),
                fit: BoxFit.fill,
              ),
            ),
          ),
          const Positioned(
            left: 30,
            top: 15,
            child: Text(
              '处罚原因文案',
              style: TextStyle(
                fontFamily: _fontFamily,
                fontSize: 14,
                fontWeight: FontWeight.w600,
                height: 20 / 14,
                color: _ink,
              ),
            ),
          ),
          const Positioned(
            left: 31,
            top: 42,
            width: 313,
            height: 1,
            child: ColoredBox(color: Color(0xFFEAEAF0)),
          ),
          const _AppealText(left: 31, top: 51, text: '处罚结果', label: true),
          const _AppealText(left: 31, top: 72, text: '处罚时长', label: true),
          const _AppealText(left: 31, top: 92, text: '处罚编号', label: true),
          const _AppealText(
            left: 103,
            top: 50,
            text: '账号禁止登录 7天',
            color: Color(0xFFD9443A),
          ),
          const _AppealText(left: 103, top: 71, text: 'N小时'),
          const _AppealText(left: 103, top: 91, text: 'PN202607290126'),
          Positioned(
            left: 265,
            top: 66,
            width: 78,
            height: 28,
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onAppeal,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.centerRight,
                    end: Alignment.centerLeft,
                    colors: [Color(0xFF372D22), Color(0xFF111111)],
                  ),
                  borderRadius: BorderRadius.circular(25),
                  border: Border.all(color: const Color(0x66D6A44A)),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x1AD6A44A),
                      blurRadius: 14,
                      offset: Offset(0, 8),
                    ),
                  ],
                ),
                child: const Center(
                  child: Text(
                    '申诉',
                    style: TextStyle(
                      fontFamily: _fontFamily,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      height: 18 / 13,
                      color: _gold,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AppealText extends StatelessWidget {
  const _AppealText({
    required this.left,
    required this.top,
    required this.text,
    this.label = false,
    this.color,
  });

  final double left;
  final double top;
  final String text;
  final bool label;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: left,
      top: top,
      child: Text(
        text,
        style: TextStyle(
          fontFamily: _fontFamily,
          fontSize: label ? 11 : 12,
          height: label ? 16 / 11 : 17 / 12,
          color: color ?? (label ? const Color(0xFFA6AAB5) : _muted),
        ),
      ),
    );
  }
}

Paint _iconPaint() => Paint()
  ..color = _navInk
  ..style = PaintingStyle.stroke
  ..strokeWidth = 1.5
  ..strokeCap = StrokeCap.round
  ..strokeJoin = StrokeJoin.round;

class _MessageIconPainter extends CustomPainter {
  const _MessageIconPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = _iconPaint();
    final path = Path()
      ..moveTo(3.0, 15.2)
      ..cubicTo(1.3, 13.5, 0.6, 11.2, 0.9, 8.7)
      ..cubicTo(1.4, 4.5, 5.1, 1.2, 9.8, 1.2)
      ..cubicTo(15.2, 1.2, 19.0, 4.9, 19.0, 9.7)
      ..cubicTo(19.0, 14.5, 15.0, 17.8, 10.0, 17.8)
      ..cubicTo(8.4, 17.8, 6.8, 17.4, 5.5, 16.7)
      ..lineTo(2.4, 18.0)
      ..close();
    canvas.drawPath(path, paint);
    final dot = Paint()..color = _navInk;
    canvas.drawCircle(const Offset(7.1, 8.0), 0.9, dot);
    canvas.drawCircle(const Offset(13.0, 8.0), 0.9, dot);
    canvas.drawPath(
      Path()
        ..moveTo(6.8, 11.3)
        ..cubicTo(8.5, 14.1, 11.7, 14.1, 13.5, 11.3),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _HeartIconPainter extends CustomPainter {
  const _HeartIconPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(9, 15.5)
      ..cubicTo(7.2, 14.8, 0.7, 10.9, 0.7, 5.0)
      ..cubicTo(0.7, 1.7, 3.1, 0.3, 5.0, 0.3)
      ..cubicTo(7.3, 0.3, 8.4, 1.7, 9.0, 2.3)
      ..cubicTo(9.6, 1.7, 10.7, 0.3, 13.0, 0.3)
      ..cubicTo(14.9, 0.3, 17.3, 1.7, 17.3, 5.0)
      ..cubicTo(17.3, 10.9, 10.8, 14.8, 9, 15.5)
      ..close();
    canvas.drawPath(path, _iconPaint());
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _TaskIconPainter extends CustomPainter {
  const _TaskIconPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = _iconPaint();
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(1, 3.2, 14, 14), const Radius.circular(0.8)),
      paint,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(5, 0.5, 6, 5), const Radius.circular(2.4)),
      paint,
    );
    canvas.drawLine(const Offset(5, 9), const Offset(11, 9), paint);
    canvas.drawLine(const Offset(5, 13), const Offset(11, 13), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ProfileIconPainter extends CustomPainter {
  const _ProfileIconPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = _iconPaint();
    canvas.drawCircle(const Offset(9, 9), 8.2, paint);
    canvas.drawCircle(const Offset(9, 6), 2.5, paint);
    final shoulders = Path()
      ..moveTo(3.7, 14.4)
      ..cubicTo(4.7, 11.7, 6.4, 10.7, 9, 10.7)
      ..cubicTo(11.6, 10.7, 13.3, 11.7, 14.3, 14.4);
    canvas.drawPath(shoulders, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
