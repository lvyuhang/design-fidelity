import 'package:flutter/material.dart';

import 'message_backup_34_page.dart';

class MessageBackup36Page extends StatelessWidget {
  const MessageBackup36Page({
    super.key,
    this.onNotification,
    this.onFilter,
    this.onTab,
    this.onConversation,
    this.onNavigation,
    this.onPinnedConversation,
  });

  final VoidCallback? onNotification;
  final VoidCallback? onFilter;
  final ValueChanged<int>? onTab;
  final ValueChanged<int>? onConversation;
  final ValueChanged<int>? onNavigation;
  final VoidCallback? onPinnedConversation;

  static const _assetRoot = 'assets/lanhu/message_backup_36/assets/';

  @override
  Widget build(BuildContext context) => MessageBackup34Page(
        onNotification: onNotification,
        onFilter: onFilter,
        onTab: onTab,
        onConversation: onConversation,
        onNavigation: onNavigation,
        onPinnedConversation: onPinnedConversation,
        backgroundColor: const Color(0xFFFFFDF9),
        allConversationAvatarsMissing: true,
        preciseSystemArtwork: true,
        showPinnedConversationBar: true,
        officialNotificationAsset:
            '${_assetRoot}4942c8d9ffd41a52012b311e9a260d39b13004fcce7e952ea8b915267eb40240.png',
        pinnedCollapseAsset:
            '${_assetRoot}878bf0142fd15e2b935fff1f2a2bc871630338b10f3622c5a593b0db99179f9f.png',
      );
}

class MessageBackup36Assets {
  const MessageBackup36Assets._();

  static const all = <String>[
    ...MessageBackup34Assets.all,
    'assets/lanhu/message_backup_36/assets/4942c8d9ffd41a52012b311e9a260d39b13004fcce7e952ea8b915267eb40240.png',
    'assets/lanhu/message_backup_36/assets/878bf0142fd15e2b935fff1f2a2bc871630338b10f3622c5a593b0db99179f9f.png',
  ];
}
