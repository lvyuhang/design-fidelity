import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/voice_calling_backup_2_page.dart';

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

  testWidgets('voice calling backup 2 renders at source 4x', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final boundaryKey = GlobalKey();
    await tester.pumpWidget(MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RepaintBoundary(
          key: boundaryKey, child: const VoiceCallingBackup2Page()),
    ));
    await tester.runAsync(() async {
      for (final asset in VoiceCallingBackup2Assets.all) {
        await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
      }
    });
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
    expect(tester.takeException(), isNull);
    await tester.runAsync(() async {
      final boundary = boundaryKey.currentContext!.findRenderObject()!
          as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 4);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      final output = File(
          Platform.environment['VOICE_CALLING_BACKUP_2_RENDER_OUTPUT'] ??
              '../design_evidence/voice-calling-backup-2/r0/render.png');
      await output.parent.create(recursive: true);
      await output.writeAsBytes(data!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('voice calling controls are interactive', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final taps = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: VoiceCallingBackup2Page(
      onMinimize: () => taps.add('minimize'),
      onMore: () => taps.add('more'),
      onClose: () => taps.add('close'),
      onRelationship: () => taps.add('relationship'),
      onMessage: () => taps.add('message'),
      onPhoto: () => taps.add('photo'),
      onGift: () => taps.add('gift'),
    )));
    for (final key in [
      'voice-control-minimize',
      'voice-control-more',
      'voice-control-close',
      'voice-relationship',
      'voice-message',
      'voice-glass-发送图片',
      'voice-glass-送礼物'
    ]) {
      await tester.tap(find.byKey(ValueKey(key)));
    }
    expect(taps, [
      'minimize',
      'more',
      'close',
      'relationship',
      'message',
      'photo',
      'gift'
    ]);
    expect(tester.takeException(), isNull);
  });
}
