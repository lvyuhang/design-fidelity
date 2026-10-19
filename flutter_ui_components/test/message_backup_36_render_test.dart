import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/message_backup_36_page.dart';

class ProductionShadowTestBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

void main() {
  ProductionShadowTestBinding();

  setUpAll(() async {
    final fonts = FontLoader('SourcePingFang');
    for (final weight in ['Regular', 'Medium', 'Semibold']) {
      fonts.addFont(rootBundle.load('assets/fonts/PingFangSC-$weight.otf'));
    }
    await fonts.load();
  });

  testWidgets('message backup 36 renders at native source scale',
      (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final boundaryKey = GlobalKey();
    await tester.pumpWidget(MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RepaintBoundary(key: boundaryKey, child: MessageBackup36Page()),
    ));
    await tester.runAsync(() async {
      for (final asset in MessageBackup36Assets.all) {
        await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
      }
    });
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
    expect(tester.takeException(), isNull);
    await tester.runAsync(() async {
      final boundary = boundaryKey.currentContext!.findRenderObject()!
          as RenderRepaintBoundary;
      final renderScale = double.tryParse(
            Platform.environment['MESSAGE_BACKUP_36_RENDER_SCALE'] ?? '',
          ) ??
          2;
      final image = await boundary.toImage(pixelRatio: renderScale);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      final output = File(
        Platform.environment['MESSAGE_BACKUP_36_RENDER_OUTPUT'] ??
            '../design_evidence/message-backup-36/r0/render.png',
      );
      await output.parent.create(recursive: true);
      await output.writeAsBytes(data!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('new fold action and existing actions remain interactive',
      (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: MessageBackup36Page(
        onNotification: () => events.add('notification'),
        onFilter: () => events.add('filter'),
        onConversation: (index) => events.add('row:$index'),
        onPinnedConversation: () => events.add('fold'),
        onNavigation: (index) => events.add('nav:$index'),
      ),
    ));
    await tester.tapAt(const Offset(320, 119));
    await tester.tapAt(const Offset(34, 160));
    await tester.tapAt(const Offset(200, 210));
    await tester.tapAt(const Offset(80, 712));
    await tester.tapAt(const Offset(55, 760));
    expect(events, ['notification', 'filter', 'row:0', 'fold', 'nav:0']);
    expect(tester.takeException(), isNull);
  });

  testWidgets('all six unavailable portraits use circular placeholders',
      (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: MessageBackup36Page()));
    for (var index = 0; index < 6; index++) {
      final placeholder = find.byKey(
        ValueKey('message-avatar-placeholder-$index'),
      );
      expect(placeholder, findsOneWidget);
      expect(tester.getSize(placeholder), const Size(45, 45));
    }
  });
}
