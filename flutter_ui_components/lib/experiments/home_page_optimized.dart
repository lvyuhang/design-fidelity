import 'package:flutter/material.dart';

import '../components/expanded_components.dart';
import '../components/social_components.dart';

class HomePageAssets {
  static const root = 'assets/lanhu/home_page';
  static const header = '$root/assets/header.png';
  static const bellButton = '$root/assets/bell_button.png';
  static const filterButton = '$root/assets/filter_button.png';
  static const titleStar = '$root/assets/title_star.png';
  static const titleSwoosh = '$root/assets/title_swoosh.png';
  static const compose = '$root/assets/compose.png';
  static const heartRed = '$root/assets/heart_red.png';
  static const heartGrey1 = '$root/assets/heart_grey_1.png';
  static const heartGrey2 = '$root/assets/heart_grey_2.png';
  static const media = '$root/media_fallback';
  static const all = <String>[
    header,
    bellButton,
    filterButton,
    titleStar,
    titleSwoosh,
    compose,
    heartRed,
    heartGrey1,
    heartGrey2,
    '$media/photo_left_top.png',
    '$media/photo_right_top.png',
    '$media/photo_left_mid.png',
    '$media/photo_left_bottom.png',
    '$media/avatar_left_top.png',
    '$media/avatar_right_top.png',
    '$media/avatar_left_mid.png',
    '$media/avatar_quote_blue.png',
    '$media/avatar_quote_green.png',
    '$media/status_icons.png',
  ];
}

class HomePageOptimized extends StatelessWidget {
  const HomePageOptimized({
    this.onCard,
    this.onLike,
    this.onCompose,
    this.onNavigation,
    super.key,
  });

  final ValueChanged<int>? onCard;
  final ValueChanged<int>? onLike;
  final VoidCallback? onCompose;
  final ValueChanged<int>? onNavigation;
  static const designSize = Size(375, 812);

  @override
  Widget build(BuildContext context) => SizedBox(
        key: const ValueKey('home-page-canvas'),
        width: 375,
        height: 812,
        child: ClipRect(
          child: ColoredBox(
            color: const Color(0xFFFEFDFA),
            child: Stack(children: [
              const Positioned(
                left: 0,
                top: 0,
                width: 375,
                height: 100,
                child: Image(
                  image: AssetImage(HomePageAssets.header),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
              const Positioned(
                left: 34,
                top: 17,
                child: Text(
                  '9:41',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 15,
                    height: 20 / 15,
                    color: Color(0xFF090909),
                  ),
                ),
              ),
              const Positioned(
                left: 293,
                top: 17,
                width: 69,
                height: 18,
                child: Image(
                  image: AssetImage(
                    '${HomePageAssets.media}/status_icons.png',
                  ),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
              const Positioned(
                left: 10,
                top: 54,
                width: 12,
                height: 12,
                child: Image(
                  image: AssetImage(HomePageAssets.titleStar),
                  fit: BoxFit.fill,
                ),
              ),
              const Positioned(
                left: 22,
                top: 51,
                child: Text(
                  '发现',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 28,
                    height: 39 / 28,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFF171719),
                  ),
                ),
              ),
              const Positioned(
                left: 63,
                top: 75,
                width: 24,
                height: 16.25,
                child: Image(
                  image: AssetImage(HomePageAssets.titleSwoosh),
                  fit: BoxFit.fill,
                ),
              ),
              const Positioned(
                left: 97,
                top: 62,
                child: Text(
                  '附近',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 14,
                    height: 20 / 14,
                    color: Color(0xFF9B9BA5),
                  ),
                ),
              ),
              const Positioned(
                left: 138,
                top: 62,
                child: Text(
                  '关注',
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 14,
                    height: 20 / 14,
                    color: Color(0xFF9B9BA5),
                  ),
                ),
              ),
              const Positioned(
                left: 281,
                top: 49,
                width: 45,
                height: 45,
                child: Image(
                  image: AssetImage(HomePageAssets.bellButton),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
              const Positioned(
                left: 327,
                top: 51,
                width: 45,
                height: 45,
                child: Image(
                  image: AssetImage(HomePageAssets.filterButton),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
              Positioned(
                left: 306,
                top: 47,
                child: Container(
                  width: 16,
                  height: 16,
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                    color: Color(0xFFFF4B36),
                    shape: BoxShape.circle,
                  ),
                  child: const Text(
                    '2',
                    textScaler: TextScaler.noScaling,
                    style: TextStyle(
                      fontFamily: 'PingFangSCFull',
                      fontSize: 9,
                      height: 1,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
              Positioned(
                left: 4,
                top: 99,
                child: FeedCard(
                  photo: const AssetImage(
                    '${HomePageAssets.media}/photo_left_top.png',
                  ),
                  avatar: const AssetImage(
                    '${HomePageAssets.media}/avatar_left_top.png',
                  ),
                  mediaIncludesCountBadge: true,
                  onOpen: onCard == null ? null : () => onCard!(0),
                  onLike: onLike == null ? null : () => onLike!(0),
                ),
              ),
              Positioned(
                left: 190,
                top: 99,
                child: _PhotoCard(
                  index: 1,
                  height: 296,
                  imageHeight: 242,
                  photo: '${HomePageAssets.media}/photo_right_top.png',
                  caption: '想找一个灵魂伴侣～',
                  name: '少年葩',
                  status: '在线',
                  statusColor: Color(0xFF1EBA3E),
                  avatar: '${HomePageAssets.media}/avatar_right_top.png',
                  heart: HomePageAssets.heartRed,
                  heartLabel: '98',
                  onOpen: onCard,
                  onLike: onLike,
                ),
              ),
              Positioned(
                left: 190,
                top: 399,
                child: _QuoteCard(
                  index: 2,
                  height: 213,
                  background: Color(0xFFEFF5FF),
                  quoteColor: Color(0xFFD7E8FF),
                  avatar: '${HomePageAssets.media}/avatar_quote_blue.png',
                  text: '怎么没人找我聊\n天？',
                  onOpen: onCard,
                  onLike: onLike,
                ),
              ),
              Positioned(
                left: 4,
                top: 421,
                child: _PhotoCard(
                  index: 3,
                  height: 193,
                  imageHeight: 136,
                  photo: '${HomePageAssets.media}/photo_left_mid.png',
                  caption: '记录每一次旅游',
                  name: '胖小双',
                  status: '忙碌',
                  statusColor: Color(0xFFF94F2D),
                  avatar: '${HomePageAssets.media}/avatar_left_mid.png',
                  heart: HomePageAssets.heartGrey1,
                  heartLabel: '98',
                  onOpen: onCard,
                  onLike: onLike,
                ),
              ),
              Positioned(
                left: 4,
                top: 618,
                child: _MediaOnlyCard(
                  index: 4,
                  photo: '${HomePageAssets.media}/photo_left_bottom.png',
                  onOpen: onCard,
                ),
              ),
              Positioned(
                left: 190,
                top: 616,
                child: _QuoteCard(
                  index: 5,
                  height: 196,
                  background: Color(0xFFF0F9E9),
                  quoteColor: Color(0xFFE2F2D9),
                  avatar: '${HomePageAssets.media}/avatar_quote_green.png',
                  text: '怎么没人找我聊\n天？',
                  onOpen: onCard,
                  onLike: onLike,
                ),
              ),
              Positioned(
                left: 288,
                top: 657,
                width: 75,
                height: 75,
                child: Semantics(
                  button: true,
                  label: '发布内容',
                  child: GestureDetector(
                    key: const ValueKey('home-compose'),
                    onTap: onCompose,
                    child: const Image(
                      image: AssetImage(HomePageAssets.compose),
                      fit: BoxFit.fill,
                      filterQuality: FilterQuality.high,
                    ),
                  ),
                ),
              ),
              Positioned(
                left: 0,
                top: 714,
                child: NavigationComponentStage(
                  onSelect: onNavigation,
                  includeCanvasBackground: false,
                ),
              ),
            ]),
          ),
        ),
      );
}

class _PhotoCard extends StatelessWidget {
  const _PhotoCard({
    required this.index,
    required this.height,
    required this.imageHeight,
    required this.photo,
    required this.caption,
    required this.name,
    required this.status,
    required this.statusColor,
    required this.avatar,
    required this.heart,
    required this.heartLabel,
    this.onOpen,
    this.onLike,
  });

  final int index;
  final double height, imageHeight;
  final String photo, caption, name, status, avatar, heart, heartLabel;
  final Color statusColor;
  final ValueChanged<int>? onOpen, onLike;

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 181.5,
        height: height,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: Material(
            color: Colors.white,
            child: Stack(children: [
              Positioned(
                left: 0,
                top: 0,
                width: 181.5,
                height: imageHeight,
                child: InkWell(
                  key: ValueKey('home-card-$index'),
                  onTap: onOpen == null ? null : () => onOpen!(index),
                  child: Image.asset(
                    photo,
                    fit: BoxFit.fill,
                    filterQuality: FilterQuality.high,
                  ),
                ),
              ),
              Positioned(
                left: 8,
                right: 6,
                top: imageHeight + 4,
                child: Text(
                  caption,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textScaler: TextScaler.noScaling,
                  style: const TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 14,
                    height: 20 / 14,
                    color: Color(0xFF171719),
                  ),
                ),
              ),
              Positioned(
                left: 8,
                top: imageHeight + 30,
                width: 15,
                height: 15,
                child: ClipOval(
                  child: Image.asset(avatar, fit: BoxFit.cover),
                ),
              ),
              Positioned(
                left: 26,
                top: imageHeight + 30,
                // Source contract: up to 55 px for the name, a measured 2 px
                // gap, then the fixed 33 px presence chip. Using the current
                // short text union (68 px) would make sub-pixel font metric
                // differences trigger an early ellipsis.
                width: 90,
                child: AuthorStatusLine(
                  name: name,
                  status: status,
                  statusColor: statusColor,
                ),
              ),
              Positioned(
                right: 31,
                top: height - 24,
                width: 14,
                height: 12,
                child: GestureDetector(
                  key: ValueKey('home-like-$index'),
                  onTap: onLike == null ? null : () => onLike!(index),
                  child: Image.asset(heart, fit: BoxFit.fill),
                ),
              ),
              Positioned(
                right: 8,
                top: height - 27,
                child: Text(
                  heartLabel,
                  textScaler: TextScaler.noScaling,
                  style: TextStyle(
                    fontFamily: 'SourcePingFang',
                    fontSize: 11,
                    height: 17 / 11,
                    color: statusColor == const Color(0xFF1EBA3E)
                        ? const Color(0xFFFF5B4B)
                        : const Color(0xFF9B9BA5),
                  ),
                ),
              ),
            ]),
          ),
        ),
      );
}

class AuthorStatusLine extends StatelessWidget {
  const AuthorStatusLine({
    required this.name,
    required this.status,
    required this.statusColor,
    this.gap = 2,
    super.key,
  });

  final String name, status;
  final Color statusColor;
  final double gap;

  @override
  Widget build(BuildContext context) => SizedBox(
        height: 16,
        child: Row(children: [
          Flexible(
            child: Text(
              name,
              key: const ValueKey('author-status-name'),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textScaler: TextScaler.noScaling,
              style: const TextStyle(
                fontFamily: 'PingFangSCFull',
                fontSize: 11,
                height: 16 / 11,
                color: Color(0xFFA6AAB5),
              ),
            ),
          ),
          SizedBox(width: gap),
          _PresenceTag(text: status, color: statusColor),
        ]),
      );
}

class _PresenceTag extends StatelessWidget {
  const _PresenceTag({required this.text, required this.color});
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) => SizedBox(
        key: const ValueKey('author-status-chip'),
        width: 33,
        height: 12,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: color == const Color(0xFF1EBA3E)
                ? const Color(0xCCF1FFE8)
                : const Color(0x17F94F2D),
            border: Border.all(
              color: color == const Color(0xFF1EBA3E)
                  ? const Color(0xFFD0EED6)
                  : const Color(0xFFFCD8D3),
              width: .5,
            ),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Container(
              width: 5,
              height: 5,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            ),
            const SizedBox(width: 2),
            Text(
              text,
              textScaler: TextScaler.noScaling,
              style: TextStyle(
                fontFamily: 'PingFangSCFull',
                fontSize: 8,
                height: 11 / 8,
                color: color == const Color(0xFF1EBA3E)
                    ? const Color(0xFF2F9D46)
                    : const Color(0xFFFF7C62),
              ),
            ),
          ]),
        ),
      );
}

class _QuoteCard extends StatelessWidget {
  const _QuoteCard({
    required this.index,
    required this.height,
    required this.background,
    required this.quoteColor,
    required this.avatar,
    required this.text,
    this.onOpen,
    this.onLike,
  });

  final int index;
  final double height;
  final Color background, quoteColor;
  final String avatar, text;
  final ValueChanged<int>? onOpen, onLike;

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: Material(
          color: background,
          child: SizedBox(
            width: 181.5,
            height: height,
            child: InkWell(
              key: ValueKey('home-card-$index'),
              onTap: onOpen == null ? null : () => onOpen!(index),
              child: Stack(children: [
                Positioned(
                  left: 14,
                  top: 4,
                  child: Text(
                    '“',
                    textScaler: TextScaler.noScaling,
                    style: TextStyle(
                      fontFamily: 'PingFangSCFull',
                      fontSize: 42,
                      height: 1,
                      fontWeight: FontWeight.w600,
                      color: quoteColor,
                    ),
                  ),
                ),
                Positioned(
                  left: 10,
                  right: 10,
                  top: height > 200 ? 61 : 65,
                  child: Text(
                    text,
                    textAlign: TextAlign.center,
                    textScaler: TextScaler.noScaling,
                    style: const TextStyle(
                      fontFamily: 'PingFangSCFull',
                      fontSize: 18,
                      height: 23 / 18,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF171719),
                    ),
                  ),
                ),
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: 37,
                  child: ColoredBox(
                    color: Colors.white,
                    child: Stack(children: [
                      Positioned(
                        left: 8,
                        top: 9,
                        width: 15,
                        height: 15,
                        child: ClipOval(
                          child: Image.asset(avatar, fit: BoxFit.cover),
                        ),
                      ),
                      const Positioned(
                        left: 27,
                        top: 10,
                        width: 90,
                        child: AuthorStatusLine(
                          name: '少年葩葩…',
                          status: '忙碌',
                          statusColor: Color(0xFFF94F2D),
                        ),
                      ),
                      Positioned(
                        right: 31,
                        top: 11,
                        width: 14,
                        height: 12,
                        child: GestureDetector(
                          key: ValueKey('home-like-$index'),
                          onTap: onLike == null ? null : () => onLike!(index),
                          child: Image.asset(
                            HomePageAssets.heartGrey2,
                            fit: BoxFit.fill,
                          ),
                        ),
                      ),
                      const Positioned(
                        right: 8,
                        top: 8,
                        child: Text(
                          '98',
                          textScaler: TextScaler.noScaling,
                          style: TextStyle(
                            fontFamily: 'PingFangSCFull',
                            fontSize: 11,
                            height: 17 / 11,
                            color: Color(0xFF9B9BA5),
                          ),
                        ),
                      ),
                    ]),
                  ),
                ),
              ]),
            ),
          ),
        ),
      );
}

class _MediaOnlyCard extends StatelessWidget {
  const _MediaOnlyCard({required this.index, required this.photo, this.onOpen});
  final int index;
  final String photo;
  final ValueChanged<int>? onOpen;

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: GestureDetector(
          key: ValueKey('home-card-$index'),
          onTap: onOpen == null ? null : () => onOpen!(index),
          child: Image.asset(
            photo,
            width: 181.5,
            height: 194,
            fit: BoxFit.fill,
            filterQuality: FilterQuality.high,
          ),
        ),
      );
}
