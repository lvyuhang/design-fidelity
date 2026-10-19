import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/message_backup_45_page.dart';

class ProductionShadowBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

void main() {
  ProductionShadowBinding();
  setUpAll(() async {
    final fonts = FontLoader('SourcePingFang');
    for (final weight in ['Regular', 'Medium', 'Semibold']) {
      fonts.addFont(rootBundle.load('assets/fonts/PingFangSC-$weight.otf'));
    }
    await fonts.load();
    final fallback = FontLoader('SourceGiftGlyphs')
      ..addFont(rootBundle.load('assets/fonts/ArialUnicode-Gift.ttf'));
    await fallback.load();
  });

  testWidgets('message backup 45 renders at 4x source scale', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final boundaryKey = GlobalKey();
    await tester.pumpWidget(MaterialApp(
      debugShowCheckedModeBanner: false,
      home:
          RepaintBoundary(key: boundaryKey, child: const MessageBackup45Page()),
    ));
    await tester.runAsync(() async {
      for (final asset in MessageBackup45Assets.all) {
        await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
      }
    });
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
    expect(find.byType(MissingDesignAsset), findsNWidgets(11));
    expect(tester.takeException(), isNull);
    await tester.runAsync(() async {
      final boundary = boundaryKey.currentContext!.findRenderObject()!
          as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 4);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      final output = File(Platform
              .environment['MESSAGE_BACKUP_45_RENDER_OUTPUT'] ??
          '${Directory.systemTemp.createTempSync('message45-').path}/render.png');
      await output.parent.create(recursive: true);
      await output.writeAsBytes(data!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('message page actions remain interactive', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: MessageBackup45Page(
      onBack: () => events.add('back'),
      onRelationship: () => events.add('relationship'),
      onMore: () => events.add('more'),
      onInput: () => events.add('input'),
      onTool: (index) => events.add('tool:$index'),
    )));
    await tester.tap(find.byKey(const ValueKey('message45-back')));
    await tester.tap(find.byKey(const ValueKey('message45-relationship')));
    await tester.tap(find.byKey(const ValueKey('message45-more')));
    await tester.tap(find.byKey(const ValueKey('message45-input')));
    await tester.tap(find.byKey(const ValueKey('message45-tool-0')));
    expect(events, ['back', 'relationship', 'more', 'input', 'tool:0']);
  });
}
