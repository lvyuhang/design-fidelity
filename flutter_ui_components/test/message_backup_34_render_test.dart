import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/message_backup_34_page.dart';

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

  testWidgets('message backup 34 renders at native source scale',
      (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final boundaryKey = GlobalKey();
    await tester.pumpWidget(MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RepaintBoundary(key: boundaryKey, child: MessageBackup34Page()),
    ));
    await tester.runAsync(() async {
      for (final asset in MessageBackup34Assets.all) {
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
            Platform.environment['MESSAGE_BACKUP_34_RENDER_SCALE'] ?? '',
          ) ??
          2;
      final image = await boundary.toImage(pixelRatio: renderScale);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      final output = File(
        Platform.environment['MESSAGE_BACKUP_34_RENDER_OUTPUT'] ??
            '../design_evidence/message-backup-34/r0/render.png',
      );
      await output.parent.create(recursive: true);
      await output.writeAsBytes(data!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('message page primary actions are interactive', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: MessageBackup34Page(
        onNotification: () => events.add('notification'),
        onFilter: () => events.add('filter'),
        onConversation: (index) => events.add('row:$index'),
        onNavigation: (index) => events.add('nav:$index'),
      ),
    ));
    await tester.tapAt(const Offset(320, 119));
    await tester.tapAt(const Offset(34, 160));
    await tester.tapAt(const Offset(200, 210));
    await tester.tapAt(const Offset(55, 760));
    expect(events, ['notification', 'filter', 'row:0', 'nav:0']);
    expect(tester.takeException(), isNull);
  });

  testWidgets('missing official artwork keeps the source circular frame',
      (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: MessageBackup34Page()));
    final placeholder =
        find.byKey(const ValueKey('official-notification-missing-asset'));
    expect(placeholder, findsOneWidget);
    expect(tester.getSize(placeholder), const Size(45, 45));
    final semantics = tester.widget<Semantics>(
      find.descendant(of: placeholder, matching: find.byType(Semantics)).first,
    );
    expect(semantics.properties.label, '设计素材未切图：官方通知图标');
    final box = tester.widget<DecoratedBox>(
      find
          .descendant(of: placeholder, matching: find.byType(DecoratedBox))
          .first,
    );
    expect((box.decoration as BoxDecoration).shape, BoxShape.circle);
  });
}
