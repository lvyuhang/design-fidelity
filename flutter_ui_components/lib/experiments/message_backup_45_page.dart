import 'package:flutter/material.dart';

class MessageBackup45Page extends StatelessWidget {
  const MessageBackup45Page({
    super.key,
    this.onBack,
    this.onRelationship,
    this.onMore,
    this.onInput,
    this.onTool,
  });

  final VoidCallback? onBack;
  final VoidCallback? onRelationship;
  final VoidCallback? onMore;
  final VoidCallback? onInput;
  final ValueChanged<int>? onTool;

  static const Size designSize = Size(375, 812);
  static const String _root = 'assets/lanhu/message_backup_45/assets/';
  static const Color _ink = Color(0xFF22242A);
  static const Color _greenInk = Color(0xFF2E4613);

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 375,
        height: 812,
        child: ClipRect(
          child: ColoredBox(
            color: const Color(0xFFF8F8F8),
            child: Stack(children: [
              const Positioned(
                left: 0,
                top: 0,
                width: 375,
                height: 100,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFFFFF9EE), Color(0xFFF8F8F8)],
                    ),
                  ),
                ),
              ),
              _statusBar(),
              _header(),
              _text('02-01 15:39', 157, 105, 62, 16, 11, 16,
                  const Color(0xFFC6C8D0),
                  align: TextAlign.center),
              ..._messages(),
              _bottomComposer(),
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
            ]),
          ),
        ),
      );

  Widget _statusBar() => Stack(children: [
        _text('9:41', 21, 14.33, 54, 18, 15, 18, Colors.black,
            align: TextAlign.center),
        const Positioned(
          left: 294,
          top: 17,
          width: 67,
          height: 12,
          child: CustomPaint(painter: _StatusPainter()),
        ),
      ]);

  Widget _header() => Stack(children: [
        Positioned(
          left: 8,
          top: 51,
          width: 30,
          height: 32,
          child: GestureDetector(
            key: const ValueKey('message45-back'),
            behavior: HitTestBehavior.opaque,
            onTap: onBack,
            child: const Stack(
              children: [
                Positioned(
                    left: 7,
                    top: 9,
                    child: Image(
                      image: AssetImage(
                          '${_root}01045e724ac333aaf7960b181f0dbe64b7cfa8995df8e32f04d8f0a44fb067c5.png'),
                      width: 8,
                      height: 14,
                    ))
              ],
            ),
          ),
        ),
        const Positioned(
          left: 44,
          top: 51,
          child: MissingDesignAsset.circle(size: 30, compact: true),
        ),
        _text('送礼大神', 80, 50, 64, 22, 16, 22, _ink, weight: FontWeight.w600),
        Positioned(
          left: 82,
          top: 73,
          width: 33,
          height: 12,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xFFF0FFF2),
              borderRadius: BorderRadius.circular(7),
              border: Border.all(color: const Color(0xFFBAEBC2), width: .5),
            ),
            child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  DecoratedBox(
                    decoration: BoxDecoration(
                        color: Color(0xFF20C744), shape: BoxShape.circle),
                    child: SizedBox(width: 5, height: 5),
                  ),
                  SizedBox(width: 2),
                  Text('在线',
                      textScaler: TextScaler.noScaling,
                      style: TextStyle(
                          inherit: false,
                          decoration: TextDecoration.none,
                          fontFamily: 'SourcePingFang',
                          fontSize: 8,
                          height: 1.1,
                          color: Color(0xFF2F9D46))),
                ]),
          ),
        ),
        Positioned(
          left: 216,
          top: 57,
          width: 100,
          height: 22,
          child: GestureDetector(
            key: const ValueKey('message45-relationship'),
            onTap: onRelationship,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0x99FFFDF8),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE8C990), width: .5),
              ),
              child: Stack(children: [
                const Positioned(
                  left: 8,
                  top: 4,
                  width: 14,
                  height: 14,
                  child: Image(
                      image: AssetImage(
                          '${_root}08fca307478b8e93d16bd790ce8dd5fae2d49445adeb780644a9fd8db2e523a4.png')),
                ),
                _text('和Ta的关系', 24, 3, 57, 16, 11, 16, const Color(0xFFB27A31)),
                const Positioned(
                    right: 8,
                    top: 7,
                    width: 5,
                    height: 8,
                    child: CustomPaint(painter: _ChevronPainter())),
              ]),
            ),
          ),
        ),
        Positioned(
          left: 326,
          top: 51,
          width: 40,
          height: 32,
          child: GestureDetector(
            key: const ValueKey('message45-more'),
            behavior: HitTestBehavior.opaque,
            onTap: onMore,
            child: const Center(
              child: Image(
                image: AssetImage(
                    '${_root}11ed38326abaa866cb04a777b29f87ed61d8883548f59cd4dbb3c7a58a341354.png'),
                width: 20,
                height: 4,
              ),
            ),
          ),
        ),
      ]);

  List<Widget> _messages() => [
        const Positioned(
            left: 17,
            top: 135,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(57, 135, 38, 38, Colors.white),
        _text('hi', 68, 143, 12, 20, 14, 20, _ink),
        const Positioned(
            left: 17,
            top: 187,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(57, 188, 94, 38, Colors.white),
        _text('在干嘛呀？', 71, 197, 70, 20, 14, 20, _ink),
        const Positioned(
            left: 331,
            top: 240,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(205, 241, 116, 38, const Color(0xFFFFF0DD), right: true),
        _text('在看你的视频', 221, 250, 84, 20, 14, 20, _greenInk),
        const Positioned(
            left: 17,
            top: 298,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(57, 298, 94, 38, Colors.white),
        _asset(
            '4ce502bbb85ac0e705ae32bf59df17eee1feaac3f6d184a75344aaa09c39bb87.png',
            72,
            309,
            13,
            17),
        _text('7”', 90, 307, 16, 20, 14, 20, const Color(0xFF18181B)),
        const Positioned(
            left: 331,
            top: 357,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(233, 357, 88, 38, const Color(0xFFFFF0DD), right: true),
        _text('5”', 269, 366, 16, 20, 14, 20, _greenInk),
        _asset(
            'f6d85e26334465a730d9b10d9e245094f3bb3b98262e4e9d43b5779da992896d.png',
            294.25,
            368.25,
            12.75,
            16.5),
        const Positioned(
            left: 17,
            top: 412,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(57, 412, 111, 38, Colors.white),
        _asset(
            '365fcb5cb9336213dcabe3bfcce0af04bdefc504800d6721533ed78ddd64712a.png',
            71.25,
            423.25,
            20.5,
            15.5),
        _text('00:22:10', 98, 421, 56, 20, 14, 20, const Color(0xFF18181B)),
        const Positioned(
            left: 17,
            top: 465,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _bubble(57, 465, 111, 38, Colors.white),
        _asset(
            'cfcb5cb661dba2406f4f6b4d4baf0c947a1171632d214e5da56e1519c7ac8c63.png',
            72,
            474,
            18,
            18),
        _text('00:22:10', 98, 474, 56, 20, 14, 20, const Color(0xFF18181B)),
        const Positioned(
            left: 17,
            top: 518,
            child: MissingDesignAsset.circle(size: 30, compact: true)),
        _asset(
            'ab6a6c0fef0982c778ba7a079fca62ed29f885397c30df3ec1d4dd13451737e7.png',
            57,
            519,
            198,
            70),
        const Positioned(
            left: 62, top: 527, child: MissingDesignAsset.circle(size: 55)),
        _text('礼物名称', 121, 534, 52, 18, 13, 18, const Color(0xFFBC914A),
            fontFamily: 'SourceGiftGlyphs'),
        _text('X 1', 179, 535, 17, 17, 12, 17, const Color(0xFFBC914A),
            weight: FontWeight.w600),
        const Positioned(
            left: 121,
            top: 558,
            child:
                MissingDesignAsset.rounded(width: 19, height: 19, label: '缺')),
        _text('300', 141, 557, 26, 20, 14, 20, const Color(0xFFE6B55E),
            weight: FontWeight.w600),
      ];

  Widget _bottomComposer() => Stack(children: [
        const Positioned(
          left: 0,
          top: 672,
          width: 375,
          height: 140,
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0xF2FFFFFF), Colors.white]),
            ),
          ),
        ),
        Positioned(
          left: 17,
          top: 686,
          width: 308,
          height: 40,
          child: GestureDetector(
            key: const ValueKey('message45-input'),
            onTap: onInput,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(22),
                boxShadow: const [
                  BoxShadow(color: Color(0x0D18181B), blurRadius: 8)
                ],
              ),
              child: Stack(children: [
                _asset(
                    '8c5be3f7395e68ec561136eac626989e6f73656ae874d2df8ae94331140c39b8.png',
                    13,
                    8,
                    24,
                    24),
                _text('发消息…', 48, 10, 56, 20, 14, 20, const Color(0xFFC6C8D0)),
              ]),
            ),
          ),
        ),
        const Positioned(
            left: 337.17,
            top: 695.17,
            width: 21.67,
            height: 21.67,
            child: CustomPaint(painter: _EmojiPainter())),
        _tool(
            '119269dd3094426a4c2894248e3066907234bfa620f6febfefad39849fdde4fd.png',
            34,
            747,
            25,
            21,
            0),
        _tool(
            'e4bde104171cbf1a9335ad95ec8e6f04861f56d910ebcf93913091bef6895d4e.png',
            126.6,
            745.6,
            22.8,
            22.88,
            1),
        _tool(
            'eb9b1d88520c73841df2e22cb48bc13afe7696352adfc5138a4ea78b2aef9b7b.png',
            223,
            748,
            26,
            18,
            2),
        _tool(
            'ac8d19b350ed3a4b8212a82d1ffc1180cda43c77e688527793ceb461c1a2f318.png',
            316,
            744,
            24,
            22,
            3),
      ]);

  Widget _tool(
          String name, double x, double y, double w, double h, int index) =>
      Positioned(
        left: x - 10,
        top: y - 8,
        width: w + 20,
        height: h + 16,
        child: GestureDetector(
          key: ValueKey('message45-tool-$index'),
          behavior: HitTestBehavior.opaque,
          onTap: () => onTool?.call(index),
          child: Center(
              child: Image.asset('$_root$name',
                  width: w, height: h, fit: BoxFit.fill)),
        ),
      );

  static Widget _asset(String name, double x, double y, double w, double h) =>
      Positioned(
        left: x,
        top: y,
        width: w,
        height: h,
        child: Image.asset('$_root$name',
            fit: BoxFit.fill, filterQuality: FilterQuality.high),
      );

  static Widget _bubble(double x, double y, double w, double h, Color color,
          {bool right = false}) =>
      Positioned(
        left: x,
        top: y,
        width: w,
        height: h,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(right ? 18 : 0),
              topRight: Radius.circular(right ? 0 : 18),
              bottomLeft: const Radius.circular(18),
              bottomRight: const Radius.circular(18),
            ),
            boxShadow: const [
              BoxShadow(color: Color(0x0FE4E4E4), blurRadius: 8)
            ],
          ),
        ),
      );

  static Widget _text(String value, double x, double y, double w, double h,
          double size, double line, Color color,
          {FontWeight weight = FontWeight.w400,
          TextAlign align = TextAlign.left,
          String fontFamily = 'SourcePingFang'}) =>
      Positioned(
        left: x,
        top: y,
        width: w,
        height: h,
        child: Text(value,
            textAlign: align,
            textScaler: TextScaler.noScaling,
            maxLines: 1,
            overflow: TextOverflow.clip,
            style: TextStyle(
                inherit: false,
                decoration: TextDecoration.none,
                fontFamily: fontFamily,
                fontSize: size,
                height: line / size,
                fontWeight: weight,
                color: color)),
      );
}

class MissingDesignAsset extends StatelessWidget {
  const MissingDesignAsset.circle(
      {super.key, required double size, this.compact = false})
      : width = size,
        height = size,
        radius = size / 2,
        label = '未切';

  const MissingDesignAsset.rounded(
      {super.key, required this.width, required this.height, this.label = '未切'})
      : radius = 5,
        compact = true;

  final double width;
  final double height;
  final double radius;
  final String label;
  final bool compact;

  @override
  Widget build(BuildContext context) => Semantics(
        label: '设计素材未切图',
        child: SizedBox(
          width: width,
          height: height,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xFFFFE5EA),
              border: Border.all(color: const Color(0xFFFF4D6D), width: .75),
              borderRadius: BorderRadius.circular(radius),
            ),
            child: Center(
                child: Text(label,
                    textScaler: TextScaler.noScaling,
                    style: TextStyle(
                        inherit: false,
                        decoration: TextDecoration.none,
                        fontFamily: 'SourcePingFang',
                        fontSize: compact ? 6 : 7,
                        height: 1,
                        color: const Color(0xFFC52245)))),
          ),
        ),
      );
}

class MessageBackup45Assets {
  const MessageBackup45Assets._();
  static const root = 'assets/lanhu/message_backup_45/assets/';
  static const all = <String>[
    '${root}01045e724ac333aaf7960b181f0dbe64b7cfa8995df8e32f04d8f0a44fb067c5.png',
    '${root}08fca307478b8e93d16bd790ce8dd5fae2d49445adeb780644a9fd8db2e523a4.png',
    '${root}119269dd3094426a4c2894248e3066907234bfa620f6febfefad39849fdde4fd.png',
    '${root}11ed38326abaa866cb04a777b29f87ed61d8883548f59cd4dbb3c7a58a341354.png',
    '${root}365fcb5cb9336213dcabe3bfcce0af04bdefc504800d6721533ed78ddd64712a.png',
    '${root}4ce502bbb85ac0e705ae32bf59df17eee1feaac3f6d184a75344aaa09c39bb87.png',
    '${root}71a71135b57da5d61e28735d476bf3400c6ddfee9dcafadb7e4bdfa6d94cc839.png',
    '${root}8c5be3f7395e68ec561136eac626989e6f73656ae874d2df8ae94331140c39b8.png',
    '${root}ab6a6c0fef0982c778ba7a079fca62ed29f885397c30df3ec1d4dd13451737e7.png',
    '${root}ac8d19b350ed3a4b8212a82d1ffc1180cda43c77e688527793ceb461c1a2f318.png',
    '${root}cfcb5cb661dba2406f4f6b4d4baf0c947a1171632d214e5da56e1519c7ac8c63.png',
    '${root}e4bde104171cbf1a9335ad95ec8e6f04861f56d910ebcf93913091bef6895d4e.png',
    '${root}eb9b1d88520c73841df2e22cb48bc13afe7696352adfc5138a4ea78b2aef9b7b.png',
    '${root}f6d85e26334465a730d9b10d9e245094f3bb3b98262e4e9d43b5779da992896d.png',
  ];
}

class _ChevronPainter extends CustomPainter {
  const _ChevronPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = const Color(0xFFB27A31)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(
        Path()
          ..moveTo(.5, .5)
          ..lineTo(size.width - .5, size.height / 2)
          ..lineTo(.5, size.height - .5),
        p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _EmojiPainter extends CustomPainter {
  const _EmojiPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = const Color(0xFF22242A)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;
    canvas.drawCircle(size.center(Offset.zero), size.width / 2 - .75, p);
    canvas.drawCircle(Offset(size.width * .34, size.height * .43), .9,
        Paint()..color = const Color(0xFF22242A));
    canvas.drawCircle(Offset(size.width * .66, size.height * .43), .9,
        Paint()..color = const Color(0xFF22242A));
    canvas.drawArc(
        Rect.fromLTWH(size.width * .30, size.height * .43, size.width * .40,
            size.height * .34),
        0.2,
        2.74,
        false,
        p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _StatusPainter extends CustomPainter {
  const _StatusPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.2, 10 - i * 2.3, 3.2, 2 + i * 2.3),
              const Radius.circular(1)),
          black);
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(27, 0, 16, 13), 3.75, 1.68, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(31, 4, 8, 7), 3.75, 1.68, false, wifi);
    canvas.drawCircle(const Offset(35, 11), 1.2, black);
    final border = Paint()
      ..color = const Color(0xFF888888)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(44, 0.5, 22, 11), const Radius.circular(2.5)),
        border);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(46, 2.3, 18, 7.4), const Radius.circular(1.3)),
        black);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(66.5, 4, 1.4, 4), const Radius.circular(.7)),
        Paint()..color = const Color(0xFF8E8E93));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
