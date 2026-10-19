import 'package:flutter/material.dart';

class ComplaintRecordEmptyAssets {
  static const root = 'assets/lanhu/complaint_empty';
  static const illustration = '$root/empty_state.png';
  static const back = '$root/back.png';
  static const all = <String>[illustration, back];
}

class ComplaintRecordEmptyPage extends StatelessWidget {
  const ComplaintRecordEmptyPage({this.onBack, super.key});

  final VoidCallback? onBack;
  static const designSize = Size(375, 837);

  @override
  Widget build(BuildContext context) => SizedBox(
        key: const ValueKey('complaint-empty-canvas'),
        width: 375,
        height: 837,
        child: ColoredBox(
          color: const Color(0xFFFFFEFA),
          child: Stack(children: [
            const Positioned(
              left: 21,
              top: 14.3333,
              width: 54,
              height: 18,
              child: Text(
                '9:41',
                textScaler: TextScaler.noScaling,
                style: TextStyle(
                  fontFamily: 'PingFangSCFull',
                  fontSize: 15,
                  height: 18 / 15,
                  letterSpacing: -.3,
                  color: Colors.black,
                ),
              ),
            ),
            const Positioned(
              left: 294,
              top: 17,
              width: 67,
              height: 12,
              child: CustomPaint(painter: _StatusIconsPainter()),
            ),
            Positioned(
              left: 16,
              top: 55,
              width: 22,
              height: 22,
              child: Semantics(
                button: true,
                label: '返回',
                child: GestureDetector(
                  key: const ValueKey('complaint-empty-back'),
                  onTap: onBack,
                  child: const Image(
                    image: AssetImage(ComplaintRecordEmptyAssets.back),
                    fit: BoxFit.fill,
                    filterQuality: FilterQuality.high,
                  ),
                ),
              ),
            ),
            const Positioned(
              left: 156,
              top: 57.032,
              width: 64,
              height: 22,
              child: Text(
                '投诉记录',
                textScaler: TextScaler.noScaling,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'PingFangSCFull',
                  fontSize: 16,
                  height: 22 / 16,
                  fontWeight: FontWeight.w500,
                  color: Color(0xFF22242A),
                ),
              ),
            ),
            const Positioned(
              left: 83,
              top: 294,
              width: 210,
              height: 136,
              child: Image(
                image: AssetImage(ComplaintRecordEmptyAssets.illustration),
                fit: BoxFit.fill,
                filterQuality: FilterQuality.high,
              ),
            ),
            const Positioned(
              left: 158,
              top: 412,
              width: 60,
              height: 21,
              child: Text(
                '暂无数据',
                textScaler: TextScaler.noScaling,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'PingFangSCFull',
                  fontSize: 15,
                  height: 21 / 15,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF22242A),
                ),
              ),
            ),
            const Positioned(
              left: 134,
              top: 437,
              width: 108,
              height: 17,
              child: Text(
                '这里什么都没有哦～',
                textScaler: TextScaler.noScaling,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'PingFangSCFull',
                  fontSize: 12,
                  height: 17 / 12,
                  color: Color(0xFF686B77),
                ),
              ),
            ),
            const Positioned(
              left: 121,
              top: 824,
              width: 134,
              height: 5,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.all(Radius.circular(100)),
                ),
              ),
            ),
          ]),
        ),
      );
}

class _StatusIconsPainter extends CustomPainter {
  const _StatusIconsPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      final h = 4.5 + i * 2.1;
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(i * 5.1, 12 - h, 3.2, h),
          const Radius.circular(1),
        ),
        black,
      );
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(23, 0, 18, 14), 3.65, 2.15, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(27, 4, 10, 8), 3.65, 2.15, false, wifi);
    canvas.drawCircle(const Offset(32, 10.4), 1.25, black);
    final batteryOutline = Paint()
      ..color = const Color(0x59000000)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(44, 0, 22, 11.3), const Radius.circular(2)),
      batteryOutline,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(46, 2, 18, 7.3), const Radius.circular(1)),
      black,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(66.4, 3.7, 1.3, 4), const Radius.circular(.7)),
      batteryOutline,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
