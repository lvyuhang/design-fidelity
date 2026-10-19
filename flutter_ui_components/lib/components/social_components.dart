import 'package:flutter/material.dart';
import 'login_components.dart';
import 'source_primitives.dart';

/// Source exports; preview-only bitmap fallbacks are kept in a separate directory.
class SocialAssets {
  static const male =
      'assets/lanhu/gender_none/assets/a25cff5f9aabb90c8c6f286be1a49d34401850108d0459495065cdf59093df43.png';
  static const female =
      'assets/lanhu/gender_none/assets/d2855e7611728cfc07b1476da674344d477abedc8d9fbc67f9087bba0c093a49.png';
  static const femaleSelected =
      'assets/lanhu/gender_female/assets/eacdc3db8eff06ddcc26f3a404612bc55bc07315ac2ef98900c27fabedff1272.png';
  static const check =
      'assets/lanhu/gender_female/assets/946fd6e0fb04feeae95ea8730b2c3eb280c50393cc9848ac36ac39e1282fec1f.png';
  static const warning =
      'assets/lanhu/gender_female/assets/10416d514d09343fe90359c1170c63f1b6a2a75432844bdc11e568ac56157832.png';
  static const trash =
      'assets/lanhu/comments/assets/68d43b2e8420e3f48ab9e110471a43f1d9d2b2616c4e6e8e6f12dfa53c07cd31.png';
  static const close =
      'assets/lanhu/comments/assets/fcd96028e910eee6670bd792c8b85b2d21971e7636437a8e1a5326a0b3aae4e2.png';
  static const imageCount =
      'assets/lanhu/feed/assets/ec319ddb8728c45ca0d5f8df87183d6f3ab557c50e25869b0f1eda7597882d46.png';
  static const photo = 'assets/fixtures/feed-photo.png';
  static const feedAvatar = 'assets/fixtures/feed-avatar.png';
  static const commentAvatar = 'assets/fixtures/comment-avatar.png';
  static const replyAvatar = 'assets/fixtures/reply-avatar.png';
  static const shield = 'assets/fixtures/warning-shield.png';
  static const all = [
    male,
    female,
    femaleSelected,
    check,
    warning,
    trash,
    close,
    imageCount,
    photo,
    feedAvatar,
    commentAvatar,
    replyAvatar,
    shield
  ];
}

Widget _image(String asset, Rect rect, Offset origin) => Positioned(
    left: rect.left - origin.dx,
    top: rect.top - origin.dy,
    width: rect.width,
    height: rect.height,
    child: Image.asset(asset,
        fit: BoxFit.fill, filterQuality: FilterQuality.high));
Widget _action(String id, Rect rect, Offset origin, VoidCallback? onTap) =>
    Positioned(
        left: rect.left - origin.dx,
        top: rect.top - origin.dy,
        width: rect.width,
        height: rect.height,
        child: Semantics(
            button: true,
            label: id,
            child: MouseRegion(
                cursor: SystemMouseCursors.click,
                child: GestureDetector(
                    key: ValueKey(id),
                    behavior: HitTestBehavior.opaque,
                    onTap: onTap))));

/// Controlled selection: the caller owns state and submission. These fixtures
/// reproduce the two supplied states; the male action is still exposed.
class GenderSelection extends StatelessWidget {
  const GenderSelection(
      {this.femaleSelected = false, this.onSelect, super.key});
  final bool femaleSelected;
  final ValueChanged<String>? onSelect;
  @override
  Widget build(BuildContext context) {
    const o = Offset(0, 146);
    final category = femaleSelected ? 'gender_female' : 'gender_none';
    final ids = femaleSelected
        ? [
            '96B9E66F-DF54-4FCB-89C2-30CFDDF4A1DB',
            '627D3B3D-C4AD-4BA3-A837-0081DB5A0C81',
            '2EB2FB31-D891-43C6-91D9-22846C3A44A1',
            'DCAF469F-D3B8-49FB-A1A7-D468223E37B2',
            '5C0E1EC5-3069-4002-B3B0-248C1147418E',
            'ABF25D32-61F2-4BF5-9839-A594E668C747',
          ]
        : [
            '7A78618E-4FB9-448C-BDF6-87DC3F3828E6',
            '732C9E9A-B4C3-490E-9E55-DD995CDC17E2',
            '59833838-223E-4D14-A356-43D503F5C92E',
            '75FB03BA-104E-449D-9294-A6277ADF1EAC',
            '63C698CE-31FE-4303-941B-E5F440045057',
            'E91048A7-8E43-48A3-9672-CCA438875BD8',
          ];
    return SizedBox(
        width: 375,
        height: 350,
        child: ClipRect(
            child: Stack(children: [
          const Positioned.fill(
              child: CustomPaint(
                  painter: LoginBackground(Rect.fromLTWH(0, 146, 375, 350)))),
          for (final id in ids) sourceLayer(category, id, o),
          _image(SocialAssets.male, const Rect.fromLTWH(65, 309, 64, 64), o),
          _image(
              femaleSelected
                  ? SocialAssets.femaleSelected
                  : SocialAssets.female,
              const Rect.fromLTWH(241, 309, 64, 64),
              o),
          if (femaleSelected) ...[
            _image(
                SocialAssets.check, const Rect.fromLTWH(315, 259, 25, 25), o),
            sourceLayer(category, '0D56E6D2-04D3-4292-A13A-83B73456714F', o),
            // This small decorative shield has an absent boolean source path.
            _image(
                SocialAssets.shield, const Rect.fromLTWH(295, 445, 37, 34), o),
            _image(
                SocialAssets.warning, const Rect.fromLTWH(46, 448, 26, 26), o),
            sourceLayer(category, '539566F2-EA29-40A5-9F82-F89E172C7F6D', o),
          ],
          _action('选择男生', const Rect.fromLTWH(30, 259, 134, 168), o,
              () => onSelect?.call('male')),
          _action('选择女生', const Rect.fromLTWH(206, 259, 134, 168), o,
              () => onSelect?.call('female')),
        ])));
  }
}

class FeedCard extends StatelessWidget {
  const FeedCard(
      {required this.photo,
      required this.avatar,
      this.caption = '可爱到心巴上的样子，这也太治愈了吧～',
      this.name = '元气小桃',
      this.imageCount = 6,
      this.online = true,
      this.mediaIncludesCountBadge = false,
      this.onOpen,
      this.onLike,
      this.onProfile,
      super.key});
  final ImageProvider photo, avatar;
  final String caption, name;
  final int imageCount;
  final bool online;

  /// Explicit fallback flag: a preview crop cannot pretend its baked badge is native.
  final bool mediaIncludesCountBadge;
  final VoidCallback? onOpen, onLike, onProfile;
  @override
  Widget build(BuildContext context) {
    assert(!mediaIncludesCountBadge || imageCount == 6);
    const o = Offset(4, 99);
    return SizedBox(
        width: 181.5,
        height: 318,
        child: Stack(children: [
          sourceLayer('feed', 'B4150442-CE31-4AC7-BCDE-B175E725AB72', o),
          Positioned(
              left: 0,
              top: 0,
              width: 181.5,
              height: 241.996253869969,
              child: ClipRRect(
                  borderRadius:
                      const BorderRadius.vertical(top: Radius.circular(4)),
                  child: Image(
                      image: photo,
                      fit: BoxFit.fill,
                      filterQuality: FilterQuality.high))),
          if (!mediaIncludesCountBadge) ...[
            sourceLayer('feed', '66AB5609-1E12-4632-80F3-BA3A833F2278', o),
            _image(SocialAssets.imageCount, const Rect.fromLTWH(151, 323, 9, 9),
                o),
            sourceLayer('feed', 'B5B67326-9305-4CF3-9716-FEE00EE68B4C', o,
                text: '$imageCount'),
          ],
          sourceLayer('feed', 'E830E0C6-5BB7-4C01-9846-85B5DCD6721E', o,
              text: caption, wrap: true),
          Positioned(
              left: 7,
              top: 293,
              width: 15,
              height: 15,
              child: ClipOval(
                  child: Image(
                      image: avatar,
                      fit: BoxFit.fill,
                      filterQuality: FilterQuality.high))),
          sourceLayer('feed', '4AAF6657-90BE-4B29-9C46-96E59DD50A6B', o,
              text: name),
          if (online)
            for (final id in [
              '452CCD14-1C86-448B-A9CF-A55D45BD950A',
              '9D75D8B1-476F-40F9-B115-8FC0509FF04C',
              'A4E8FFFB-905E-436A-AA75-DA990BEC8017'
            ])
              sourceLayer('feed', id, o),
          sourceLayer('feed', 'AB77E2C4-476B-40D1-AACE-CAD6A7CDF160', o),
          sourceLayer('feed', 'B5FBFF25-F7DE-487A-918F-FFD48E494136', o),
          _action('打开动态', const Rect.fromLTWH(4, 99, 181.5, 288), o, onOpen),
          _action('查看作者', const Rect.fromLTWH(8, 388, 105, 26), o, onProfile),
          _action('点赞动态', const Rect.fromLTWH(146, 388, 35, 26), o, onLike),
        ]));
  }
}

class FeedComponentStage extends StatelessWidget {
  const FeedComponentStage(
      {this.onOpen, this.onLike, this.onProfile, super.key});
  final VoidCallback? onOpen, onLike, onProfile;
  @override
  Widget build(BuildContext context) => SizedBox(
      width: 375,
      height: 342,
      child: ColoredBox(
          color: const Color(0xFFFEFDFA),
          child: Stack(children: [
            // Preserve the reference crop's shadow gutters, with the card centered.
            Positioned(
                left: 92.75,
                top: 11,
                width: 188,
                height: 320,
                child: ClipRect(
                    child: Stack(children: [
                  Positioned(
                      left: 4,
                      top: 1,
                      child: FeedCard(
                          photo: const AssetImage(SocialAssets.photo),
                          avatar: const AssetImage(SocialAssets.feedAvatar),
                          mediaIncludesCountBadge: true,
                          onOpen: onOpen,
                          onLike: onLike,
                          onProfile: onProfile)),
                ]))),
          ])));
}

/// A source-sized comment thread. Data and actions can be supplied by a caller.
class CommentPanel extends StatelessWidget {
  const CommentPanel(
      {this.onClose,
      this.onReply,
      this.onDelete,
      this.onExpand,
      this.firstText = '这张照片好美呀，氛围感拉满了！',
      this.secondText = '给你发消息了～快回复我',
      super.key});
  final VoidCallback? onClose, onDelete, onExpand;
  final ValueChanged<String>? onReply;
  final String firstText, secondText;
  @override
  Widget build(BuildContext context) {
    const o = Offset(0, 350);
    return SizedBox(
        width: 375,
        height: 374,
        child: ClipRect(
            child: Stack(children: [
          sourceLayer('comments', '3EB47F3A-BB49-41F2-8216-FFFD664991DD', o),
          sourceLayer('comments', 'E10B062A-D927-4825-ACEA-9036F16524F3', o),
          for (final id in [
            '9302CA47-CC58-47BB-9D30-BACFD3719375',
            'FE855C3A-F763-4C89-8853-C5DD5CC4EE6E',
            '046DA58D-F2E5-4A4B-B11C-D37926D1F5A9',
            '7E7F84DD-D428-4CE4-AE82-B7E20B2EA8A5',
            '6B71A3B5-250B-4FDB-B84F-7E1D503FBDE9',
            '1D79D44D-3405-4AEF-8A98-78C1052A5A4B',
            'F0880EB2-CED5-4342-AAC2-05FBB4D98A34',
            'D9FD6778-754D-42A7-9267-AB4A17362095',
            '07115D35-408E-4FD5-895A-605DA0CD7810',
            '8A883BD3-CDA3-44EB-9463-6623A79FF6A1',
            'E43DBF2F-A03D-4696-B535-95D272C3A52C',
            '15959333-AF71-4E5D-9226-9B45E91900ED',
            'B1C798B2-A8D4-4874-B654-010F4651F5D3',
            '0140282D-7D61-46AB-BC26-0CB8E87C7BAE',
            '175D101A-26FE-49F3-958D-22A0605E9120',
            'AC09B782-5C8F-44DE-9F7D-292A1E68095A',
          ])
            sourceLayer('comments', id, o),
          sourceLayer('comments', 'E67C58E4-08BD-423D-AEA2-597112ED2F84', o,
              text: firstText, wrap: true),
          sourceLayer('comments', 'A897D7AD-AB9F-4A56-AEDC-F8B83041F041', o,
              text: secondText, wrap: true),
          sourceLayer('comments', 'C80F5AAC-6D9C-4824-BFD3-2C3E387E88B6', o,
              wrap: true),
          _image(SocialAssets.commentAvatar,
              const Rect.fromLTWH(16, 397, 30, 30), o),
          _image(SocialAssets.commentAvatar,
              const Rect.fromLTWH(16, 497, 30, 30), o),
          _image(SocialAssets.replyAvatar, const Rect.fromLTWH(53, 582, 24, 24),
              o),
          _image(SocialAssets.trash, const Rect.fromLTWH(338, 502, 20, 20), o),
          // Export is 10x10 including the 1px outline padding around the 8px path.
          _image(SocialAssets.close, const Rect.fromLTWH(343, 363, 10, 10), o),
          _action('关闭评论', const Rect.fromLTWH(332, 352, 32, 32), o, onClose),
          _action('回复作者', const Rect.fromLTWH(155, 442, 54, 28), o,
              () => onReply?.call('author')),
          _action('回复momo', const Rect.fromLTWH(155, 544, 54, 28), o,
              () => onReply?.call('momo')),
          _action('删除评论', const Rect.fromLTWH(332, 496, 32, 32), o, onDelete),
          _action('展开3条回复', const Rect.fromLTWH(52, 675, 125, 32), o, onExpand),
        ])));
  }
}
