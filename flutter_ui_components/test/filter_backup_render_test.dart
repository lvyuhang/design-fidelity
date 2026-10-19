import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/filter_backup_page.dart';

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

  testWidgets('filter backup renders at source 4x', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final boundaryKey = GlobalKey();
    await tester.pumpWidget(MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RepaintBoundary(key: boundaryKey, child: const FilterBackupPage()),
    ));
    await tester.runAsync(() async {
      for (final asset in FilterBackupAssets.all) {
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
      final output = File(Platform.environment['FILTER_BACKUP_RENDER_OUTPUT'] ??
          '../design_evidence/filter-backup/r0/render.png');
      await output.parent.create(recursive: true);
      await output.writeAsBytes(data!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('filter backup actions are interactive', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var close = 0;
    var configure = 0;
    var task = -1;
    var enabled = -1;
    await tester.pumpWidget(MaterialApp(
        home: FilterBackupPage(
      onClose: () => close++,
      onConfigure: () => configure++,
      onTaskTap: (value) => task = value,
      onEnabledTaskTap: (value) => enabled = value,
    )));
    await tester.tap(find.byKey(const ValueKey('filter-close')));
    await tester.tap(find.byKey(const ValueKey('filter-configure')));
    await tester.tap(find.byKey(const ValueKey('filter-task-3')));
    await tester.tap(find.byKey(const ValueKey('filter-enabled-1')));
    expect((close, configure, task, enabled), (1, 1, 3, 1));
    expect(tester.takeException(), isNull);
  });
}
