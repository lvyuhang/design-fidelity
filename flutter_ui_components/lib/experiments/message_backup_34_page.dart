import 'package:flutter/material.dart';

class MessageBackup34Page extends StatelessWidget {
  const MessageBackup34Page({
    super.key,
    this.onNotification,
    this.onFilter,
    this.onTab,
    this.onConversation,
    this.onNavigation,
    this.onPinnedConversation,
    this.backgroundColor = Colors.white,
    this.allConversationAvatarsMissing = false,
    this.officialNotificationAsset,
    this.preciseSystemArtwork = false,
    this.showPinnedConversationBar = false,
    this.pinnedCollapseAsset,
  });

  final VoidCallback? onNotification;
  final VoidCallback? onFilter;
  final ValueChanged<int>? onTab;
  final ValueChanged<int>? onConversation;
  final ValueChanged<int>? onNavigation;
  final VoidCallback? onPinnedConversation;
  final Color backgroundColor;
  final bool allConversationAvatarsMissing;
  final String? officialNotificationAsset;
  final bool preciseSystemArtwork;
  final bool showPinnedConversationBar;
  final String? pinnedCollapseAsset;

  static const Size designSize = Size(375, 812);
  static const Color ink = Color(0xFF22242A);
  static const Color muted = Color(0xFFA6AAB5);
  static const Color gold = Color(0xFFB27A31);
  static const String _assetRoot = 'assets/lanhu/message_backup_34/assets/';

  @override
  Widget build(BuildContext context) => SizedBox(
        width: designSize.width,
        height: designSize.height,
        child: ClipRect(
          child: ColoredBox(
            color: backgroundColor,
            child: Stack(
              children: [
                const Positioned(
                  left: 0,
                  top: 0,
                  width: 375,
                  height: 111,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [Color(0xE6FFFBF3), Color(0x00FFFEFA)],
                      ),
                    ),
                  ),
                ),
                _statusBar(),
                _header(),
                _notification(),
                _filters(),
                _conversationRows(),
                if (showPinnedConversationBar) _pinnedConversationBar(),
                _bottomNavigation(),
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

  Widget _statusBar() => Stack(children: [
        _text('9:41', 21, 15.5, 54, 18, 15, 18, Colors.black,
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
        _text('消息', 16, 51, 60, 37, 26, 37, const Color(0xFF18181B),
            weight: FontWeight.w600),
        const Positioned(
          left: 55.7,
          top: 73,
          width: 23.5,
          height: 16.5,
          child: Image(
            image: AssetImage(
                '${_assetRoot}7770bd50d14ae591e54a1b0b3df11747bb86d312886b8476d748cb4be6e485db.png'),
            fit: BoxFit.fill,
            filterQuality: FilterQuality.none,
          ),
        ),
        _text('通话记录', 92, 58, 65, 21, 15, 21, const Color(0xFF91919B)),
        _badge(145, 47),
      ]);

  Widget _notification() => Positioned(
        left: 16,
        top: 104,
        width: 343,
        height: 30,
        child: Semantics(
          button: true,
          label: '开启推送通知',
          child: GestureDetector(
            onTap: onNotification,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0x8AFFFDF6),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0x99F2E2C6), width: .5),
              ),
              child: Stack(children: [
                _text('推送通知未开启，会错过重要消息哦', 13, 6, 205, 17, 12, 17, ink),
                _text('去开启', 265, 6, 37, 16, 11, 16, const Color(0xFFBC914A),
                    weight: FontWeight.w600),
                const Positioned(
                  left: 301.25,
                  top: 10,
                  width: 5.5,
                  height: 10,
                  child: Image(
                    image: AssetImage(
                        '${_assetRoot}a25881b7d5ce15dcdb2811888680942ed9ce92f2384e935c5e9eb672bcc64457.png'),
                    fit: BoxFit.fill,
                    filterQuality: FilterQuality.high,
                  ),
                ),
                const Positioned(
                  left: 322,
                  top: 10,
                  width: 10,
                  height: 10,
                  child: Image(
                    image: AssetImage(
                        '${_assetRoot}ba6ad713213694bd6d892e33d0effb4a9384c7002553201e6aad73e35f56276f.png'),
                    fit: BoxFit.fill,
                    filterQuality: FilterQuality.high,
                  ),
                ),
              ]),
            ),
          ),
        ),
      );

  Widget _filters() => Stack(children: [
        Positioned(
          left: 16,
          top: 145,
          width: 38,
          height: 30,
          child: GestureDetector(
            onTap: onFilter,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0x33DFE2E9),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Center(
                child: Image(
                  image: AssetImage(
                      '${_assetRoot}133aceb46ccc07583e92c605bc539afd2e22fd2c024af2f90025e03941ab4544.png'),
                  width: 16,
                  height: 14,
                  filterQuality: FilterQuality.none,
                ),
              ),
            ),
          ),
        ),
        Positioned(
          left: 60,
          top: 144,
          width: 285,
          height: 32,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0x33DFE2E9),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Stack(children: [
              Positioned(
                left: 4,
                top: 3,
                width: 66,
                height: 26,
                child: GestureDetector(
                  onTap: () => onTab?.call(0),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(18),
                    ),
                  ),
                ),
              ),
              _text('全部', 24, 7, 28, 18, 13, 18, gold, weight: FontWeight.w600),
              _text('熟人', 88, 7, 28, 18, 13, 18, muted),
              _text('深夜聊的...', 133, 7, 68, 18, 13, 18, muted),
              _text('我关注的', 215, 7, 56, 18, 13, 18, muted),
            ]),
          ),
        ),
      ]);

  Widget _conversationRows() => Stack(children: [
        _row(0, 184, '阿珍同学', '你在干嘛呀？',
            badge: '生人',
            online: true,
            unread: true,
            placeholderColor: const Color(0xFFDDE7E3)),
        _row(1, 249, '旎旎马克', '[微笑][微笑]',
            badge: '熟人',
            online: true,
            placeholderColor: const Color(0xFFF2DCD9)),
        _row(2, 315, '晚风', '[图片]',
            genericAvatar: !allConversationAvatarsMissing, offlineRed: true),
        _row(3, 380, '花花', '未接',
            missed: true, placeholderColor: const Color(0xFFE5D5D2)),
        _row(4, 445, '物简则明', '已取消',
            canceled: true,
            online: true,
            placeholderColor: const Color(0xFFD4E2D2)),
        _row(5, 510, '跳舞机宝贝', '[语音]',
            online: true, placeholderColor: const Color(0xFFE0D5C8)),
        _systemRow(6, 574, '官方通知', 'XXXXXXXXXXXXXXXXXXXX XXXX XXXX XX', 'cc'),
        _systemRow(7, 639, '提醒消息', 'XX XXXX XXXXXXXXXXXXXXXXXXXXXX X', 'bell'),
      ]);

  Widget _row(
    int index,
    double top,
    String name,
    String detail, {
    String? badge,
    bool online = false,
    bool unread = false,
    bool genericAvatar = false,
    bool offlineRed = false,
    bool missed = false,
    bool canceled = false,
    Color placeholderColor = const Color(0xFFE4E7EC),
  }) =>
      Positioned(
        left: 0,
        top: top,
        width: 375,
        height: 65,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => onConversation?.call(index),
          child: Stack(children: [
            Positioned(
              left: 16,
              top: 9,
              width: 45,
              height: 45,
              child: genericAvatar
                  ? const Image(
                      image: AssetImage(
                          '${_assetRoot}cc123c6bf5380b980ceb60f97f87b37e3118b855f479282363ec453729369e98.png'),
                      fit: BoxFit.fill,
                    )
                  : _MissingAvatar(
                      key: ValueKey('message-avatar-placeholder-$index'),
                      color: placeholderColor,
                      semanticLabel: '设计素材未切图：$name头像',
                    ),
            ),
            if (online || offlineRed)
              Positioned(
                left: 49,
                top: 43,
                width: 10,
                height: 10,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: offlineRed
                        ? const Color(0xFFF94F2D)
                        : const Color(0xFF1EBA3E),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 1),
                  ),
                ),
              ),
            _text(name, 71, [12.0, 13.0, 13.0, 13.0, 13.0, 14.0][index], 110,
                21, 15, 21, ink,
                weight: FontWeight.w600),
            if (badge != null)
              Positioned(
                left: badge == '生人' ? 138 : 137,
                top: badge == '生人' ? 13 : 16,
                width: 31,
                height: 14,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: badge == '生人'
                        ? const Color(0xFFFFF3ED)
                        : const Color(0xFFFCEAF0),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Center(
                    child: Text(badge,
                        textScaler: TextScaler.noScaling,
                        style: TextStyle(
                            inherit: false,
                            fontFamily: 'SourcePingFang',
                            fontSize: 9,
                            height: 13 / 9,
                            color: badge == '生人'
                                ? const Color(0xFFC98771)
                                : const Color(0xFF955468))),
                  ),
                ),
              ),
            if (missed || canceled)
              Positioned(
                left: missed ? 73.25 : 72,
                top: missed ? 37.25 : 38,
                width: missed ? 16.5 : 17,
                height: missed ? 12.5 : 13,
                child: Image(
                  image: AssetImage(
                    '${_assetRoot}${missed ? '302d40e3cddc0c5dc27b8fca1058f2e9e4266b93ce88e0e3bbdc9dd8d49189dd.png' : 'f905dce5939b9af6544739ee7933e79aef295cd8228323f52ddea84e9bfcc124.png'}',
                  ),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
            _text(
              detail,
              missed ? 95 : (canceled ? 94 : (index == 5 ? 69.5 : 71)),
              [36.0, 35.0, 35.0, 35.0, 35.0, 36.0][index],
              195,
              17,
              12,
              17,
              missed
                  ? const Color(0xFFD9443A)
                  : canceled
                      ? muted
                      : const Color(0xFF91919B),
            ),
            _text('15:33', 332, [16.0, 17.0, 17.0, 17.0, 17.0, 18.0][index], 28,
                14, 10, 14, const Color(0xFFACAFB7)),
            if (unread) _badge(337, 37),
          ]),
        ),
      );

  Widget _systemRow(
          int index, double top, String name, String detail, String kind) =>
      Positioned(
        left: 0,
        top: top,
        width: 375,
        height: 65,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => onConversation?.call(index),
          child: Stack(children: [
            Positioned(
              left: preciseSystemArtwork ? 17 : 16,
              top: preciseSystemArtwork ? (kind == 'cc' ? 11 : 12) : 10,
              width: preciseSystemArtwork ? 44 : 45,
              height: preciseSystemArtwork ? 44 : 45,
              child: kind == 'cc'
                  ? officialNotificationAsset == null
                      ? const _MissingAssetPlaceholder(
                          key: ValueKey('official-notification-missing-asset'),
                          semanticLabel: '设计素材未切图：官方通知图标',
                        )
                      : Image(
                          image: AssetImage(officialNotificationAsset!),
                          fit: BoxFit.fill,
                        )
                  : const Image(
                      image: AssetImage(
                        '${_assetRoot}711bc34d080a29cb67efeb89cd437f9d2d85882884085eb93a584d436983bfba.png',
                      ),
                      fit: BoxFit.fill,
                    ),
            ),
            _text(
                name,
                71,
                preciseSystemArtwork
                    ? (kind == 'bell' ? 12.25 : 12)
                    : (kind == 'bell' ? 12.25 : 11),
                90,
                21,
                15,
                21,
                ink,
                weight: FontWeight.w600),
            _text(detail, 71, 34, 253, 17, 12, 17, const Color(0xFF91919B)),
            _text('15:33', 332, 14, 28, 14, 10, 14, const Color(0xFFACAFB7)),
            _badge(337, 35),
          ]),
        ),
      );

  Widget _pinnedConversationBar() => Positioned(
        left: 0,
        top: 691,
        width: 375,
        height: 44,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: onPinnedConversation,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: backgroundColor,
              border: const Border(
                top: BorderSide(color: Color(0xFFF0EEE9), width: 1),
              ),
            ),
            child: Stack(children: [
              const Positioned(
                left: 23.5,
                top: 14.5,
                width: 12,
                height: 12,
                child: CustomPaint(painter: _PinnedListPainter()),
              ),
              _text('折叠置顶会话', 46, 12, 78, 18, 13, 18, ink),
              if (pinnedCollapseAsset != null)
                Positioned(
                  left: 347.5,
                  top: 19.5,
                  width: 9,
                  height: 5,
                  child: Image(
                    image: AssetImage(pinnedCollapseAsset!),
                    fit: BoxFit.fill,
                    filterQuality: FilterQuality.high,
                  ),
                ),
            ]),
          ),
        ),
      );

  Widget _bottomNavigation() => Positioned(
        left: 0,
        top: 714,
        width: 375,
        height: 85,
        child: DecoratedBox(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0x00FFFFFF), Colors.white],
            ),
          ),
          child: Stack(children: [
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
                    colors: [Color(0xCFFFFFFF), Color(0xE6F8F6ED)],
                  ),
                  borderRadius: BorderRadius.circular(28),
                  border: Border.all(color: Colors.white),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x33C9C7AF),
                      blurRadius: 4,
                      offset: Offset(0, -2),
                    ),
                  ],
                ),
              ),
            ),
            const Positioned(
              left: 91,
              top: 28,
              width: 60,
              height: 43,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Color(0x33FFEA7B),
                  borderRadius: BorderRadius.all(Radius.circular(20)),
                ),
              ),
            ),
            _nav(0, 44.25, 33.125, 21.5, 19.75, '首页',
                'a3109e049196a732525f8c4d7b65981c9d4b943e1da00cdad33c576bf2b1d0e9.png'),
            _nav(1, 111, 34, 20, 19, '消息',
                '58ae7275356d68146c2e4d681bb589158c06ac2106b49b6365258198825ddb9c.png',
                selected: true),
            _nav(2, 178.043, 35.157, 19.75, 17.75, '关系',
                '3d9c1507231ab4216545fd4d47fc4e0016d132646d95dee832583047252607ef.png'),
            _nav(3, 247.364, 33.957, 14.75, 17.75, '任务',
                '1cc08b902b88aba143242c42b1b3f8f2b3427a06f64b9c66746997c46790c075.png'),
            _nav(4, 305.25, 33.25, 19.5, 19.5, '我的',
                'c5b435df1b9694e954a0f7039592d6b377caf13f87a26314173e862966065822.png'),
            _badge(135, 26),
          ]),
        ),
      );

  Widget _nav(int index, double left, double top, double width, double height,
          String label, String asset,
          {bool selected = false}) =>
      Positioned(
        left: left - 14,
        top: top - 4,
        width: width + 28,
        height: 48,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => onNavigation?.call(index),
          child: Stack(children: [
            Positioned(
              left: 14,
              top: 4,
              width: width,
              height: height,
              child: Image(
                  image: AssetImage('$_assetRoot$asset'),
                  fit: BoxFit.fill,
                  filterQuality:
                      index == 2 ? FilterQuality.medium : FilterQuality.none),
            ),
            _text(
                label,
                index == 3 ? 7.25 : 10,
                index == 2 ? 26.95 : (index == 3 ? 27.25 : 29),
                28,
                10,
                9,
                10,
                selected ? gold : const Color(0xFF7B7980),
                align: TextAlign.center),
          ]),
        ),
      );

  Widget _badge(double left, double top) => Positioned(
        left: left,
        top: top,
        width: 18,
        height: 14,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFFF94F2D),
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Center(
            child: Text('2',
                textScaler: TextScaler.noScaling,
                style: TextStyle(
                    inherit: false,
                    fontFamily: 'SourcePingFang',
                    fontSize: 10,
                    height: 14 / 10,
                    color: Colors.white)),
          ),
        ),
      );

  Widget _text(String value, double left, double top, double width,
          double height, double size, double lineHeight, Color color,
          {FontWeight weight = FontWeight.w400,
          TextAlign align = TextAlign.left}) =>
      Positioned(
        left: left,
        top: top,
        width: width,
        height: height,
        child: Text(
          value,
          textScaler: TextScaler.noScaling,
          maxLines: 1,
          overflow: TextOverflow.clip,
          textAlign: align,
          style: TextStyle(
            inherit: false,
            decoration: TextDecoration.none,
            fontFamily: 'SourcePingFang',
            fontSize: size,
            height: lineHeight / size,
            fontWeight: weight,
            color: color,
          ),
        ),
      );
}

class MessageBackup34Assets {
  const MessageBackup34Assets._();
  static const root = 'assets/lanhu/message_backup_34/assets/';
  static const all = <String>[
    '${root}133aceb46ccc07583e92c605bc539afd2e22fd2c024af2f90025e03941ab4544.png',
    '${root}1cc08b902b88aba143242c42b1b3f8f2b3427a06f64b9c66746997c46790c075.png',
    '${root}302d40e3cddc0c5dc27b8fca1058f2e9e4266b93ce88e0e3bbdc9dd8d49189dd.png',
    '${root}3d9c1507231ab4216545fd4d47fc4e0016d132646d95dee832583047252607ef.png',
    '${root}58ae7275356d68146c2e4d681bb589158c06ac2106b49b6365258198825ddb9c.png',
    '${root}711bc34d080a29cb67efeb89cd437f9d2d85882884085eb93a584d436983bfba.png',
    '${root}7770bd50d14ae591e54a1b0b3df11747bb86d312886b8476d748cb4be6e485db.png',
    '${root}a25881b7d5ce15dcdb2811888680942ed9ce92f2384e935c5e9eb672bcc64457.png',
    '${root}a3109e049196a732525f8c4d7b65981c9d4b943e1da00cdad33c576bf2b1d0e9.png',
    '${root}ba6ad713213694bd6d892e33d0effb4a9384c7002553201e6aad73e35f56276f.png',
    '${root}c5b435df1b9694e954a0f7039592d6b377caf13f87a26314173e862966065822.png',
    '${root}cc123c6bf5380b980ceb60f97f87b37e3118b855f479282363ec453729369e98.png',
    '${root}f905dce5939b9af6544739ee7933e79aef295cd8228323f52ddea84e9bfcc124.png',
  ];
}

class _MissingAvatar extends StatelessWidget {
  const _MissingAvatar({
    super.key,
    required this.color,
    required this.semanticLabel,
  });
  final Color color;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) => Semantics(
        label: semanticLabel,
        image: true,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(color: const Color(0xFFFF4D6D), width: .8),
          ),
          child: const Center(
            child: Text(
              '未切',
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                inherit: false,
                fontFamily: 'SourcePingFang',
                fontSize: 9,
                color: Color(0xFFFF4D6D),
              ),
            ),
          ),
        ),
      );
}

class _MissingAssetPlaceholder extends StatelessWidget {
  const _MissingAssetPlaceholder({super.key, required this.semanticLabel});

  final String semanticLabel;

  @override
  Widget build(BuildContext context) => Semantics(
        label: semanticLabel,
        image: true,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFFFFE5EA),
            shape: BoxShape.circle,
            border: Border.all(color: const Color(0xFFFF4D6D), width: .8),
          ),
          child: const Center(
            child: Text(
              '未切',
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                inherit: false,
                fontFamily: 'SourcePingFang',
                fontSize: 9,
                color: Color(0xFFC52245),
              ),
            ),
          ),
        ),
      );
}

class _StatusPainter extends CustomPainter {
  const _StatusPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(i * 4.6, 10 - i * 2.3, 3, 2 + i * 2.3),
          const Radius.circular(1),
        ),
        p,
      );
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8;
    canvas.drawArc(const Rect.fromLTWH(24, 0, 16, 13), 3.75, 1.68, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(28, 4, 8, 7), 3.75, 1.68, false, wifi);
    canvas.drawCircle(const Offset(32, 11), 1.2, p);
    final border = Paint()
      ..color = Colors.black.withValues(alpha: .35)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(45, 1, 21, 10), const Radius.circular(2)),
      border,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
          const Rect.fromLTWH(47, 3, 17, 6), const Radius.circular(1)),
      p,
    );
    canvas.drawRect(const Rect.fromLTWH(67, 4, 1, 4), border);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _PinnedListPainter extends CustomPainter {
  const _PinnedListPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFFA6AAB5)
      ..style = PaintingStyle.fill;
    for (final y in <double>[0, 5.5, 11]) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(-.5, y, 2.5, 2),
          const Radius.circular(1),
        ),
        paint,
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(3.5, y, 9, 2),
          const Radius.circular(1),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
