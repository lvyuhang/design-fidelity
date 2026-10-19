import 'package:flutter/material.dart';

class DetailPage2Assets {
  static const root = 'assets/lanhu/detail_page_2';
  static const back = '$root/back.png';
  static const more = '$root/more.png';
  static const authorTag = '$root/author-tag.png';
  static const meTag = '$root/me-tag.png';
  // The source filenames preserve the original export order. Their visual roles
  // are defined here from verified render bounds, rather than guessed names.
  static const inputSmile = '$root/heart.png';
  static const actionHeart = '$root/smile.png';
  static const actionComment = '$root/comment.png';
  static const reference = 'assets/reference/detail-page-2.png';
  static const all = <String>[
    back,
    more,
    authorTag,
    meTag,
    inputSmile,
    actionHeart,
    actionComment,
  ];
}

class DetailPage2Case extends StatelessWidget {
  const DetailPage2Case({this.onBack, this.onComment, super.key});

  final VoidCallback? onBack;
  final VoidCallback? onComment;
  static const designSize = Size(375, 1255);

  static const _body = TextStyle(
    fontFamily: 'PingFangSCFull',
    fontSize: 14,
    height: 20 / 14,
    color: Color(0xFF22242A),
  );
  static const _meta = TextStyle(
    fontFamily: 'PingFangSCFull',
    fontSize: 12,
    height: 17 / 12,
    color: Color(0xFF91919B),
  );

  @override
  Widget build(BuildContext context) => SizedBox(
        key: const ValueKey('detail-page-2-canvas'),
        width: designSize.width,
        height: designSize.height,
        child: ColoredBox(
          color: Colors.white,
          child: Stack(clipBehavior: Clip.hardEdge, children: [
            const Positioned(left: 21, top: 14.33, child: _Clock()),
            const Positioned(
              left: 294,
              top: 17,
              width: 67,
              height: 12,
              child: CustomPaint(painter: _StatusIconsPainter()),
            ),
            Positioned(
              left: 16,
              top: 64,
              width: 10,
              height: 16,
              child: GestureDetector(
                key: const ValueKey('detail-page-2-back'),
                onTap: onBack,
                behavior: HitTestBehavior.opaque,
                child: const Image(
                  image: AssetImage(DetailPage2Assets.back),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
            ),
            const Positioned(
              left: 40,
              top: 52,
              width: 40,
              height: 40,
              child: _MissingAsset.circle(label: '头像'),
            ),
            const Positioned(
              left: 69,
              top: 83,
              width: 12,
              height: 12,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Color(0xFF19C75B),
                  shape: BoxShape.circle,
                  border: Border.fromBorderSide(
                    BorderSide(color: Colors.white, width: 1.5),
                  ),
                ),
              ),
            ),
            const Positioned(
              left: 90,
              top: 54,
              child: Text('胖小双',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 14,
                    height: 20 / 14,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF22242A),
                  )),
            ),
            const Positioned(
                left: 90,
                top: 75,
                child: Text('23岁',
                    textScaler: TextScaler.noScaling, style: _meta)),
            const Positioned(
                left: 119,
                top: 79,
                width: 1,
                height: 9,
                child: ColoredBox(color: Color(0xFFD8D9DE))),
            const Positioned(
                left: 126,
                top: 75,
                child:
                    Text('男', textScaler: TextScaler.noScaling, style: _meta)),
            const Positioned(
              left: 340,
              top: 70,
              width: 16,
              height: 4,
              child: Image(
                image: AssetImage(DetailPage2Assets.more),
                fit: BoxFit.fill,
                filterQuality: FilterQuality.high,
              ),
            ),
            const Positioned(
              left: 0,
              top: 100,
              width: 375,
              height: 500,
              child: _MissingAsset(label: '设计素材\n未切图', fontSize: 16),
            ),
            for (final thumb in const [
              17.0,
              67.0,
              117.0,
              163.0,
              213.0,
              263.0,
              311.0,
              361.0
            ])
              Positioned(
                left: thumb,
                top: 553,
                width: 40,
                height: 40,
                child: _MissingAsset(
                  label: '缺',
                  radius: 5,
                  selected: thumb == 67,
                  fontSize: 10,
                ),
              ),
            const Positioned(
              left: 17,
              top: 612,
              width: 300,
              height: 48,
              child: Text.rich(
                const TextSpan(children: [
                  TextSpan(text: '可爱到心巴上的样子，这也太治愈了吧～\n生活中的小美好，值得被认真收藏'),
                  WidgetSpan(
                    alignment: PlaceholderAlignment.middle,
                    child: SizedBox(
                      width: 14,
                      height: 14,
                      child: _MissingAsset(label: '缺', radius: 2, fontSize: 7),
                    ),
                  ),
                ]),
                textScaler: TextScaler.noScaling,
                style: TextStyle(
                  fontFamily: 'PingFangSCFull',
                  fontSize: 14,
                  height: 24 / 14,
                  color: Color(0xFF22242A),
                ),
              ),
            ),
            const Positioned(
              left: 17,
              top: 672,
              child: Text('2026-07-01  15:30  ·  杭州市',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                      fontFamily: 'PingFangSCFull',
                      fontSize: 12,
                      height: 17 / 12,
                      color: Color(0xFFA6AAB5))),
            ),
            const Positioned(
                left: 17,
                top: 701,
                width: 343,
                height: 1,
                child: ColoredBox(color: Color(0xFFEAEBF0))),
            const Positioned(
              left: 17,
              top: 714,
              child: Text('全部评论（19）',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                      fontFamily: 'PingFangSCFull',
                      fontSize: 12,
                      height: 17 / 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF18181B))),
            ),
            _commentOne(),
            _commentTwo(),
            _commentThree(),
            const Positioned(
                left: 0,
                top: 1169,
                width: 375,
                height: 1,
                child: ColoredBox(color: Color(0xFFEAEBF0))),
            Positioned(
              left: 0,
              top: 1170,
              width: 375,
              height: 51,
              child: ColoredBox(
                color: Colors.white.withValues(alpha: .90),
                child: Stack(children: [
                  Positioned(
                    left: 16,
                    top: 6,
                    width: 218,
                    height: 38,
                    child: GestureDetector(
                      key: const ValueKey('detail-page-2-comment-input'),
                      onTap: onComment,
                      behavior: HitTestBehavior.opaque,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          color: const Color(0xFFE3E3E3).withValues(alpha: .30),
                          borderRadius: BorderRadius.circular(19),
                        ),
                        child: const Stack(children: [
                          Positioned(
                              left: 18,
                              top: 10,
                              child: Text('说点什么吧～',
                                  textScaler: TextScaler.noScaling,
                                  style: TextStyle(
                                      fontFamily: 'PingFangSCFull',
                                      fontSize: 12,
                                      height: 17 / 12,
                                      color: Color(0xFFA6AAB5)))),
                          Positioned(
                              left: 187,
                              top: 10,
                              width: 18,
                              height: 18,
                              child: Image(
                                  image:
                                      AssetImage(DetailPage2Assets.inputSmile),
                                  fit: BoxFit.fill,
                                  filterQuality: FilterQuality.high)),
                        ]),
                      ),
                    ),
                  ),
                  const Positioned(
                      left: 248,
                      top: 16,
                      width: 20,
                      height: 17.16,
                      child: Image(
                          image: AssetImage(DetailPage2Assets.actionHeart),
                          fit: BoxFit.fill,
                          filterQuality: FilterQuality.high)),
                  const Positioned(
                      left: 274,
                      top: 18,
                      child: Text('98',
                          textScaler: TextScaler.noScaling,
                          style: TextStyle(
                              fontFamily: 'PingFangSCFull',
                              fontSize: 10,
                              height: 14 / 10,
                              color: Color(0xFF18181B)))),
                  const Positioned(
                      left: 315,
                      top: 17,
                      width: 17,
                      height: 17,
                      child: Image(
                          image: AssetImage(DetailPage2Assets.actionComment),
                          fit: BoxFit.fill,
                          filterQuality: FilterQuality.high)),
                  const Positioned(
                      left: 339,
                      top: 18,
                      child: Text('98',
                          textScaler: TextScaler.noScaling,
                          style: TextStyle(
                              fontFamily: 'PingFangSCFull',
                              fontSize: 10,
                              height: 14 / 10,
                              color: Color(0xFF18181B)))),
                ]),
              ),
            ),
            Positioned(
              left: 0,
              top: 1221,
              width: 375,
              height: 34,
              child: ColoredBox(
                color: Colors.white.withValues(alpha: .90),
                child: const Center(
                  child: Padding(
                    padding: EdgeInsets.only(top: 21),
                    child: SizedBox(
                        width: 134,
                        height: 5,
                        child: DecoratedBox(
                            decoration: BoxDecoration(
                                color: Colors.black,
                                borderRadius:
                                    BorderRadius.all(Radius.circular(100))))),
                  ),
                ),
              ),
            ),
          ]),
        ),
      );

  static Widget _avatar(double left, double top, double size) => Positioned(
        left: left,
        top: top,
        width: size,
        height: size,
        child: const _MissingAsset.circle(label: '头像'),
      );

  static Widget _replyMeta(double top) => Positioned(
        left: 52,
        top: top,
        child: const Row(mainAxisSize: MainAxisSize.min, children: [
          Text('2分钟前 · 浙江', textScaler: TextScaler.noScaling, style: _meta),
          SizedBox(width: 27),
          SizedBox(
            width: 12,
            height: 12,
            child: _MissingAsset(label: '缺', radius: 2, fontSize: 6),
          ),
          SizedBox(width: 6),
          Text('回复',
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                  fontFamily: 'PingFangSCFull',
                  fontSize: 12,
                  height: 17 / 12,
                  color: Color(0xFF686B77))),
        ]),
      );

  static Widget _commentOne() => Stack(children: [
        _avatar(16, 744, 30),
        const Positioned(
            left: 52,
            top: 744,
            child: Text('慢慢来会比较快',
                textScaler: TextScaler.noScaling, style: _meta)),
        const Positioned(
            left: 140,
            top: 746,
            width: 28,
            height: 14,
            child: Image(
                image: AssetImage(DetailPage2Assets.authorTag),
                fit: BoxFit.fill)),
        const Positioned(
            left: 52,
            top: 765,
            child: Text('这张照片好美呀，氛围感拉满了！',
                textScaler: TextScaler.noScaling, style: _body)),
        _replyMeta(795),
      ]);

  static Widget _commentTwo() => Stack(children: [
        _avatar(16, 844, 30),
        const Positioned(
            left: 52,
            top: 844,
            child:
                Text('momo', textScaler: TextScaler.noScaling, style: _meta)),
        const Positioned(
            left: 92,
            top: 846,
            width: 20,
            height: 14,
            child: Image(
                image: AssetImage(DetailPage2Assets.meTag), fit: BoxFit.fill)),
        const Positioned(
            right: 18,
            top: 850,
            width: 17,
            height: 19,
            child: _MissingAsset(label: '缺', radius: 3, fontSize: 7)),
        const Positioned(
            left: 52,
            top: 868,
            child: Text('给你发消息了～快回复我',
                textScaler: TextScaler.noScaling, style: _body)),
        _replyMeta(896),
        _avatar(53, 929, 24),
        const Positioned(
            left: 85,
            top: 930,
            child:
                Text('小王同学', textScaler: TextScaler.noScaling, style: _meta)),
        const Positioned(
          left: 85,
          top: 950,
          width: 236,
          height: 40,
          child: Text.rich(
            TextSpan(style: _body, children: [
              TextSpan(text: '回复'),
              TextSpan(
                  text: '@momo', style: TextStyle(color: Color(0xFFC59445))),
              TextSpan(text: '：给你发消息了～快回复\n我'),
            ]),
            textScaler: TextScaler.noScaling,
          ),
        ),
        const Positioned(
            left: 87,
            top: 998,
            child: Text('刚刚 · 浙江',
                textScaler: TextScaler.noScaling, style: _meta)),
        const Positioned(
            left: 56,
            top: 1037,
            width: 22,
            height: 1,
            child: ColoredBox(color: Color(0xFFC6C8D0))),
        const Positioned(
            left: 88,
            top: 1029,
            child: Text('展示3条回复',
                textScaler: TextScaler.noScaling,
                style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 12,
                    height: 17 / 12,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF686B77)))),
        const Positioned(
            left: 161,
            top: 1036,
            width: 8,
            height: 5,
            child: _MissingAsset(label: '', radius: 1, fontSize: 1)),
      ]);

  static Widget _commentThree() => Stack(children: [
        _avatar(16, 1082, 30),
        const Positioned(
            left: 52,
            top: 1082,
            child: Text('慢慢来会比较快',
                textScaler: TextScaler.noScaling, style: _meta)),
        const Positioned(
            left: 52,
            top: 1103,
            child: Text('这张照片好美呀，氛围感拉满了！',
                textScaler: TextScaler.noScaling, style: _body)),
        _replyMeta(1132),
      ]);
}

class DetailPage2CasePreviewPage extends StatelessWidget {
  const DetailPage2CasePreviewPage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFFF2F3F5),
        body: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Column(children: [
            const Text('详情页-2 · Skill 2.18.5 复杂独立案例',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            const Text('粉色占位表示蓝湖 MCP 未提供原始位图素材',
                style: TextStyle(fontSize: 12, color: Color(0xFF687482))),
            const SizedBox(height: 14),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _PreviewPanel(label: '蓝湖原稿', child: _ReferenceImage()),
                    SizedBox(width: 24),
                    _PreviewPanel(label: 'Flutter', child: DetailPage2Case()),
                  ]),
            ),
          ]),
        ),
      );
}

class _ReferenceImage extends StatelessWidget {
  const _ReferenceImage();
  @override
  Widget build(BuildContext context) => const Image(
        image: AssetImage(DetailPage2Assets.reference),
        width: 375,
        height: 1255,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );
}

class _PreviewPanel extends StatelessWidget {
  const _PreviewPanel({required this.label, required this.child});
  final String label;
  final Widget child;
  @override
  Widget build(BuildContext context) => Column(children: [
        Text(label,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        DecoratedBox(
            decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFCBD1D9))),
            child: child),
      ]);
}

class _MissingAsset extends StatelessWidget {
  const _MissingAsset(
      {required this.label,
      this.radius = 0,
      this.selected = false,
      this.fontSize = 12});
  const _MissingAsset.circle({required this.label})
      : radius = 999,
        selected = false,
        fontSize = 8;
  final String label;
  final double radius;
  final bool selected;
  final double fontSize;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFFFFE8EE),
          borderRadius: BorderRadius.circular(radius),
          border: Border.all(
              color:
                  selected ? const Color(0xFFC99C4B) : const Color(0xFFFF5A79),
              width: selected ? 2 : 1),
        ),
        child: Center(
            child: Text(label,
                textScaler: TextScaler.noScaling,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: fontSize,
                    height: 1.2,
                    color: const Color(0xFFE23A59)))),
      );
}

class _Clock extends StatelessWidget {
  const _Clock();
  @override
  Widget build(BuildContext context) => const Text('9:41',
      textScaler: TextScaler.noScaling,
      style: TextStyle(
          fontFamily: 'PingFangSCFull',
          fontSize: 15,
          height: 18 / 15,
          fontWeight: FontWeight.w500,
          color: Colors.black));
}

class _StatusIconsPainter extends CustomPainter {
  const _StatusIconsPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      final h = 4.0 + i * 2.3;
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.2, 12 - h, 3.3, h), const Radius.circular(1)),
          black);
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.7
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(25, 0, 19, 14), 3.75, 1.68, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(29, 4, 11, 8), 3.75, 1.68, false, wifi);
    canvas.drawCircle(const Offset(34.5, 11), 1.2, black);
    final outline = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(49, 1, 17, 10), const Radius.circular(2)),
        outline);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(51, 3, 13, 6), const Radius.circular(1)),
        black);
    canvas.drawRect(const Rect.fromLTWH(66.5, 4, 1.5, 4), black);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
