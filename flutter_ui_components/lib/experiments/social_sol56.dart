import 'package:flutter/material.dart';

const _feedPhoto = 'assets/fixtures/feed-photo.png';
const _feedAvatar = 'assets/fixtures/feed-avatar.png';
const _commentAvatar = 'assets/fixtures/comment-avatar.png';
const _replyAvatar = 'assets/fixtures/reply-avatar.png';

const _fontFamily = 'SourcePingFang';
const _ink = Color(0xFF22242A);
const _muted = Color(0xFF91919B);
const _action = Color(0xFF686B77);

/// A fixed source-fidelity stage for the centered feed card.
///
/// The photo and avatar assets are explicitly preview-crop fixtures because
/// the design source did not expose their original downloadable bitmaps.
class Sol56FeedComponentStage extends StatelessWidget {
  const Sol56FeedComponentStage({
    super.key,
    this.onOpen,
    this.onLike,
    this.onProfile,
  });

  final VoidCallback? onOpen;
  final VoidCallback? onLike;
  final VoidCallback? onProfile;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 375,
      height: 342,
      child: ColoredBox(
        color: const Color(0xFFFEFDFA),
        child: Center(
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: onOpen,
            child: Container(
              width: 181.5,
              height: 318,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x0D000000),
                    blurRadius: 6,
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: Stack(
                  children: [
                    Positioned(
                      left: 0,
                      top: 0,
                      width: 181.5,
                      height: 242,
                      child: Image.asset(_feedPhoto, fit: BoxFit.cover),
                    ),
                    const Positioned(
                      left: 8,
                      top: 248,
                      width: 165.5,
                      height: 36,
                      child: Text(
                        '可爱到心巴上的样子，这也太治愈了吧～',
                        style: TextStyle(
                          color: Color(0xFF18181B),
                          fontFamily: _fontFamily,
                          fontSize: 13,
                          fontWeight: FontWeight.w400,
                          height: 18 / 13,
                        ),
                      ),
                    ),
                    Positioned(
                      left: 6,
                      top: 289,
                      width: 107,
                      height: 24,
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: onProfile,
                        child: Stack(
                          children: [
                            Positioned(
                              left: 1,
                              top: 4,
                              width: 15,
                              height: 15,
                              child: ClipOval(
                                child: Image.asset(
                                  _feedAvatar,
                                  fit: BoxFit.cover,
                                ),
                              ),
                            ),
                            const Positioned(
                              left: 20,
                              top: 3,
                              child: Text(
                                '元气小桃',
                                style: TextStyle(
                                  color: Color(0xFFA6AAB5),
                                  fontFamily: _fontFamily,
                                  fontSize: 11,
                                  height: 16 / 11,
                                ),
                              ),
                            ),
                            Positioned(
                              left: 67,
                              top: 5,
                              width: 33,
                              height: 12,
                              child: DecoratedBox(
                                decoration: BoxDecoration(
                                  color: const Color(0xCCF1FFE8),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(
                                    color: const Color(0xFFD0EED6),
                                    width: 0.5,
                                  ),
                                ),
                                child: const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    DecoratedBox(
                                      decoration: BoxDecoration(
                                        color: Color(0xFF1EBA3E),
                                        shape: BoxShape.circle,
                                      ),
                                      child: SizedBox(width: 5, height: 5),
                                    ),
                                    SizedBox(width: 2),
                                    Text(
                                      '在线',
                                      style: TextStyle(
                                        color: Color(0xFF2F9D46),
                                        fontFamily: _fontFamily,
                                        fontSize: 8,
                                        height: 11 / 8,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    Positioned(
                      right: 3.5,
                      top: 289,
                      width: 36,
                      height: 25,
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: onLike,
                        child: const Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.favorite_border_rounded,
                              size: 16,
                              color: Color(0xFF909196),
                            ),
                            SizedBox(width: 2),
                            Text(
                              '赞',
                              style: TextStyle(
                                color: Color(0xFF909196),
                                fontFamily: _fontFamily,
                                fontSize: 10,
                                height: 14 / 10,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// A fixed source-fidelity comment panel.
///
/// Both avatar assets are explicitly preview-crop fixtures because the source
/// only supplied raster previews, not the original downloadable resources.
class Sol56CommentPanel extends StatelessWidget {
  const Sol56CommentPanel({
    super.key,
    this.onClose,
    this.onDelete,
    this.onExpand,
    this.onReply,
  });

  final VoidCallback? onClose;
  final VoidCallback? onDelete;
  final VoidCallback? onExpand;
  final ValueChanged<String>? onReply;

  static const _regular12 = TextStyle(
    color: _muted,
    fontFamily: _fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w400,
    height: 17 / 12,
  );

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 375,
      height: 374,
      child: ColoredBox(
        color: const Color(0xFFF7F7F8),
        child: Stack(
          clipBehavior: Clip.hardEdge,
          children: [
            const Positioned(
              left: 17,
              top: 9,
              child: Text(
                '全部评论（19）',
                style: TextStyle(
                  color: Color(0xFF18181B),
                  fontFamily: _fontFamily,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  height: 17 / 12,
                ),
              ),
            ),
            Positioned(
              right: 7,
              top: 1,
              width: 40,
              height: 40,
              child: IconButton(
                padding: EdgeInsets.zero,
                splashRadius: 18,
                onPressed: onClose,
                icon: const Icon(
                  Icons.close_rounded,
                  size: 17,
                  color: Color(0xFFA6AAB5),
                ),
              ),
            ),
            _avatar(_commentAvatar, left: 16, top: 47, size: 30),
            const Positioned(
              left: 52,
              top: 47,
              child: Text('慢慢来会比较快', style: _regular12),
            ),
            Positioned(
              left: 141,
              top: 49,
              width: 28,
              height: 14,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  border: Border.all(
                    color: const Color(0xFFEAEBF0),
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(7),
                ),
                child: const Center(
                  child: Text(
                    '作者',
                    style: TextStyle(
                      color: Color(0xFFA6AAB5),
                      fontFamily: _fontFamily,
                      fontSize: 9,
                      fontWeight: FontWeight.w500,
                      height: 13 / 9,
                    ),
                  ),
                ),
              ),
            ),
            const Positioned(
              left: 52,
              top: 68,
              child: Text(
                '这张照片好美呀，氛围感拉满了！',
                style: TextStyle(
                  color: _ink,
                  fontFamily: _fontFamily,
                  fontSize: 14,
                  height: 20 / 14,
                ),
              ),
            ),
            const Positioned(
              left: 52,
              top: 98,
              child: Text('2分钟前  ·  浙江', style: _regular12),
            ),
            Positioned(
              left: 153,
              top: 92,
              width: 58,
              height: 30,
              child: _replyButton(
                onTap: () => onReply?.call('慢慢来会比较快'),
              ),
            ),
            _avatar(_commentAvatar, left: 16, top: 147, size: 30),
            const Positioned(
              left: 52,
              top: 147,
              child: Text('momo', style: _regular12),
            ),
            const Positioned(
              left: 52,
              top: 171,
              child: Text(
                '给你发消息了～快回复我',
                style: TextStyle(
                  color: _ink,
                  fontFamily: _fontFamily,
                  fontSize: 14,
                  height: 20 / 14,
                ),
              ),
            ),
            Positioned(
              right: 9,
              top: 142,
              width: 36,
              height: 40,
              child: IconButton(
                padding: EdgeInsets.zero,
                splashRadius: 17,
                onPressed: onDelete,
                icon: const Icon(
                  Icons.delete_outline_rounded,
                  size: 22,
                  color: Color(0xFFC6C8D0),
                ),
              ),
            ),
            const Positioned(
              left: 52,
              top: 199,
              child: Text('2分钟前  ·  浙江', style: _regular12),
            ),
            Positioned(
              left: 153,
              top: 194,
              width: 58,
              height: 30,
              child: _replyButton(onTap: () => onReply?.call('momo')),
            ),
            _avatar(_replyAvatar, left: 53, top: 232, size: 24),
            const Positioned(
              left: 85,
              top: 233,
              child: Text('小王同学', style: _regular12),
            ),
            Positioned(
              left: 85,
              top: 253,
              width: 236,
              height: 40,
              child: RichText(
                text: TextSpan(
                  style: TextStyle(
                    color: _ink,
                    fontFamily: _fontFamily,
                    fontSize: 14,
                    height: 20 / 14,
                  ),
                  children: [
                    TextSpan(text: '回复'),
                    TextSpan(
                      text: '@momo',
                      style: TextStyle(color: Color(0xFFB88D42)),
                    ),
                    TextSpan(text: '：给你发消息了～快回复我'),
                  ],
                ),
              ),
            ),
            const Positioned(
              left: 87,
              top: 301,
              child: Text('刚刚  ·  浙江', style: _regular12),
            ),
            Positioned(
              left: 53,
              top: 321,
              width: 130,
              height: 45,
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: onExpand,
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    SizedBox(
                      width: 22,
                      child: Divider(
                        height: 1,
                        thickness: 0.5,
                        color: Color(0xFFC6C8D0),
                      ),
                    ),
                    SizedBox(width: 10),
                    Text(
                      '展示3条回复',
                      style: TextStyle(
                        color: _action,
                        fontFamily: _fontFamily,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        height: 17 / 12,
                      ),
                    ),
                    SizedBox(width: 5),
                    Icon(
                      Icons.keyboard_arrow_down_rounded,
                      size: 16,
                      color: _action,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Widget _avatar(
    String asset, {
    required double left,
    required double top,
    required double size,
  }) {
    return Positioned(
      left: left,
      top: top,
      width: size,
      height: size,
      child: ClipOval(child: Image.asset(asset, fit: BoxFit.cover)),
    );
  }

  static Widget _replyButton({required VoidCallback onTap}) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: const Row(
        children: [
          Icon(Icons.mode_comment_outlined, size: 14, color: _action),
          SizedBox(width: 6),
          Text(
            '回复',
            style: TextStyle(
              color: _action,
              fontFamily: _fontFamily,
              fontSize: 12,
              height: 17 / 12,
            ),
          ),
        ],
      ),
    );
  }
}
