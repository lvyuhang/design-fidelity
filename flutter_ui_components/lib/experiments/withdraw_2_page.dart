import 'package:flutter/material.dart';

class Withdraw2Assets {
  static const root = 'assets/lanhu/withdraw_2';
  static const wallet = '$root/wallet.png';
  static const alipay = '$root/alipay.png';
  static const chevron = '$root/chevron.png';
  static const reference = 'assets/reference/withdraw-2.png';
  static const all = <String>[wallet, alipay, chevron];
}

class Withdraw2Page extends StatelessWidget {
  const Withdraw2Page({this.onBack, this.onConfirm, super.key});

  final VoidCallback? onBack;
  final VoidCallback? onConfirm;
  static const designSize = Size(375, 812);

  static const _ink = Color(0xFF22242A);
  static const _muted = Color(0xFFA6AAB5);
  static const _warmBorder = Color(0xFFEEDCC4);

  static TextStyle _text(
    double size, {
    double? line,
    Color color = _ink,
    FontWeight weight = FontWeight.w400,
  }) =>
      TextStyle(
        fontFamily: 'PingFangSCFull',
        fontSize: size,
        height: line == null ? null : line / size,
        color: color,
        fontWeight: weight,
        letterSpacing: 0,
      );

  @override
  Widget build(BuildContext context) => SizedBox(
        key: const ValueKey('withdraw-2-canvas'),
        width: 375,
        height: 812,
        child: ColoredBox(
          color: const Color(0xFFFFFEFA),
          child: Stack(clipBehavior: Clip.hardEdge, children: [
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
              left: 13,
              top: 56,
              width: 18,
              height: 22,
              child: GestureDetector(
                key: const ValueKey('withdraw-2-back'),
                behavior: HitTestBehavior.opaque,
                onTap: onBack,
                child: const Center(
                  child: SizedBox(
                    width: 6,
                    height: 12,
                    child: CustomPaint(painter: _BackPathPainter()),
                  ),
                ),
              ),
            ),
            Positioned(
              left: 172,
              top: 55,
              width: 32,
              height: 22,
              child: Text(
                '提现',
                textScaler: TextScaler.noScaling,
                style: _text(16, line: 22, weight: FontWeight.w600),
              ),
            ),
            const Positioned(
              left: 16,
              top: 97,
              width: 343,
              height: 140,
              child: _BalanceCard(),
            ),
            Positioned(
              left: 16,
              top: 245,
              width: 343,
              height: 50,
              child: _WarmCard(
                radius: 18,
                child: Stack(children: [
                  const Positioned(
                    left: 19,
                    top: 16,
                    width: 22,
                    height: 22,
                    child: Image(
                      image: AssetImage(Withdraw2Assets.alipay),
                      fit: BoxFit.fill,
                      filterQuality: FilterQuality.high,
                    ),
                  ),
                  Positioned(
                    left: 50,
                    top: 17,
                    child: Text(
                      '支付宝（134****8888）',
                      textScaler: TextScaler.noScaling,
                      style: _text(14, line: 20),
                    ),
                  ),
                  Positioned(
                    left: 285,
                    top: 18,
                    child: Text(
                      '修改',
                      textScaler: TextScaler.noScaling,
                      style:
                          _text(12, line: 17, color: const Color(0xFFBC914A)),
                    ),
                  ),
                  const Positioned(
                    left: 317,
                    top: 23,
                    width: 4,
                    height: 8,
                    child: Image(
                      image: AssetImage(Withdraw2Assets.chevron),
                      fit: BoxFit.fill,
                      filterQuality: FilterQuality.high,
                    ),
                  ),
                ]),
              ),
            ),
            Positioned(
              left: 16,
              top: 303,
              width: 343,
              height: 146,
              child: _WarmCard(
                radius: 18,
                child: Stack(children: [
                  Positioned(
                    left: 22,
                    top: 28,
                    child: Text('提现金额',
                        textScaler: TextScaler.noScaling,
                        style: _text(14, line: 20)),
                  ),
                  Positioned(
                    left: 22,
                    top: 69,
                    child: Text('¥280',
                        textScaler: TextScaler.noScaling,
                        style: _text(24, line: 33, weight: FontWeight.w600)),
                  ),
                  const Positioned(
                    left: 23.5,
                    top: 114.5,
                    width: 296,
                    height: .5,
                    child: ColoredBox(color: Color(0xFFF1EDE1)),
                  ),
                  Positioned(
                    left: 26,
                    top: 123,
                    child: Text('将扣除2800星币',
                        textScaler: TextScaler.noScaling,
                        style: _text(11, line: 16, color: _muted)),
                  ),
                ]),
              ),
            ),
            Positioned(
              left: 16,
              top: 475,
              width: 343,
              height: 103,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: Colors.white, width: 1),
                  gradient: const LinearGradient(
                    begin: Alignment(-.9044776, -9.9629631),
                    end: Alignment(.8507463, -4.4074075),
                    colors: [Color(0xEDFFFDF9), Color(0xD1FEF7EA)],
                  ),
                ),
                child: Stack(children: [
                  Positioned(
                    left: 15,
                    top: 8,
                    child: Text('提现说明',
                        textScaler: TextScaler.noScaling,
                        style: _text(12,
                            line: 17,
                            color: const Color(0xFF948C83),
                            weight: FontWeight.w600)),
                  ),
                  const _Bullet(top: 39),
                  const _Bullet(top: 60),
                  const _Bullet(top: 81),
                  Positioned(
                    left: 26,
                    top: 33,
                    child: Text('首次提现不限时间，最低 5 元',
                        textScaler: TextScaler.noScaling,
                        style: _text(12,
                            line: 17, color: const Color(0xFFA7A199))),
                  ),
                  Positioned(
                    left: 26,
                    top: 54,
                    child: Text('后续仅周二、周三可申请，每周 1 次，最低 50 元',
                        textScaler: TextScaler.noScaling,
                        style: _text(12,
                            line: 17, color: const Color(0xFFA7A199))),
                  ),
                  Positioned(
                    left: 26,
                    top: 75,
                    child: Text('到账时间 1-3 个工作日',
                        textScaler: TextScaler.noScaling,
                        style: _text(12,
                            line: 17, color: const Color(0xFFA7A199))),
                  ),
                ]),
              ),
            ),
            Positioned(
              left: 28,
              top: 706,
              width: 320,
              height: 50,
              child: GestureDetector(
                key: const ValueKey('withdraw-2-confirm'),
                behavior: HitTestBehavior.opaque,
                onTap: onConfirm,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(25),
                    border:
                        Border.all(color: const Color(0x66D6A44A), width: 1),
                    gradient: const LinearGradient(
                      begin: Alignment.centerRight,
                      end: Alignment.centerLeft,
                      colors: [Color(0xFF372D22), Color(0xFF111111)],
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x1AD6A44A),
                        offset: Offset(0, 8),
                        blurRadius: 14,
                      ),
                    ],
                  ),
                  child: Center(
                    child: Text('确认提现',
                        textScaler: TextScaler.noScaling,
                        style: _text(15,
                            line: 21,
                            color: const Color(0xFFE6B55E),
                            weight: FontWeight.w600)),
                  ),
                ),
              ),
            ),
            const Positioned(
              left: 121,
              top: 799,
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

class _BalanceCard extends StatelessWidget {
  const _BalanceCard();

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          gradient: const LinearGradient(
            begin: Alignment(0, -1),
            end: Alignment(0, 1),
            colors: [Color(0xFFFFF9EC), Colors.white],
          ),
          boxShadow: const [
            BoxShadow(color: Color(0x1FE8C77B), blurRadius: 16),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(1),
          child: DecoratedBox(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(17),
              gradient: const LinearGradient(
                begin: Alignment(-.423, -.912),
                end: Alignment(1.218, 1.426),
                stops: [0, .001, 1],
                colors: [
                  Color(0xFFFFFBF4),
                  Color(0xFFFEF7EA),
                  Color(0xFFFCE5CA),
                ],
              ),
            ),
            child: Stack(clipBehavior: Clip.hardEdge, children: [
              Positioned(
                left: 13,
                top: 23,
                child: Text('可提现',
                    textScaler: TextScaler.noScaling,
                    style: Withdraw2Page._text(12,
                        line: 17, color: const Color(0xFFA6AAB5))),
              ),
              Positioned(
                left: 12,
                top: 57,
                child: Text('3800',
                    textScaler: TextScaler.noScaling,
                    style: Withdraw2Page._text(30,
                        line: 42, weight: FontWeight.w600)),
              ),
              Positioned(
                left: 87,
                top: 72,
                child: Text('星币',
                    textScaler: TextScaler.noScaling,
                    style: Withdraw2Page._text(12, line: 17)),
              ),
              Positioned(
                left: 15,
                top: 100,
                child: Text('≈ 380.0元',
                    textScaler: TextScaler.noScaling,
                    style: Withdraw2Page._text(14, line: 20)),
              ),
              const Positioned(
                left: 172,
                top: 0,
                width: 171,
                height: 147,
                child: Image(
                  image: AssetImage(Withdraw2Assets.wallet),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
            ]),
          ),
        ),
      );
}

class _WarmCard extends StatelessWidget {
  const _WarmCard({required this.radius, required this.child});
  final double radius;
  final Widget child;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xD9FFFDF9),
          borderRadius: BorderRadius.circular(radius),
          border: Border.all(color: Withdraw2Page._warmBorder, width: 1),
          boxShadow: const [
            BoxShadow(
              color: Color(0x14D89B47),
              offset: Offset(0, 1),
              blurRadius: 10,
            ),
          ],
        ),
        child: child,
      );
}

class _Bullet extends StatelessWidget {
  const _Bullet({required this.top});
  final double top;

  @override
  Widget build(BuildContext context) => Positioned(
        left: 15,
        top: top,
        width: 5,
        height: 5,
        child: const DecoratedBox(
          decoration:
              BoxDecoration(color: Color(0xFFDAC8A3), shape: BoxShape.circle),
        ),
      );
}

class _BackPathPainter extends CustomPainter {
  const _BackPathPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF333333)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(
        Path()
          ..moveTo(size.width, 0)
          ..lineTo(0, size.height / 2)
          ..lineTo(size.width, size.height),
        paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _StatusIconsPainter extends CustomPainter {
  const _StatusIconsPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      final h = 4.4 + i * 2.05;
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.1, 11 - h, 3.2, h), const Radius.circular(1)),
          black);
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(23, 0, 18, 14), 3.65, 2.15, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(27, 4, 10, 8), 3.65, 2.15, false, wifi);
    canvas.drawCircle(const Offset(32, 10.4), 1.25, black);
    final outline = Paint()
      ..color = const Color(0x59000000)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(44, 0, 22, 11.3), const Radius.circular(2)),
        outline);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(46, 2, 18, 7.3), const Radius.circular(1)),
        black);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(66.4, 3.7, 1.3, 4), const Radius.circular(.7)),
        outline);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class Withdraw2PreviewPage extends StatelessWidget {
  const Withdraw2PreviewPage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFFF1F2F4),
        body: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 36),
          child: Center(
            child: Column(children: [
              const Text('提现-2 · Skill 2.18.6 新案例',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              const Text('左：蓝湖原稿　右：Flutter 实现',
                  style: TextStyle(fontSize: 13, color: Color(0xFF69717D))),
              const SizedBox(height: 16),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _frame(const Image(
                      image: AssetImage(Withdraw2Assets.reference),
                      width: 375,
                      height: 812,
                      fit: BoxFit.fill,
                    )),
                    const SizedBox(width: 20),
                    _frame(const Withdraw2Page()),
                  ],
                ),
              ),
            ]),
          ),
        ),
      );

  Widget _frame(Widget child) => DecoratedBox(
        decoration: BoxDecoration(
          border: Border.all(color: const Color(0xFFCED3DB)),
          boxShadow: const [
            BoxShadow(color: Color(0x22000000), blurRadius: 14)
          ],
        ),
        child: child,
      );
}
