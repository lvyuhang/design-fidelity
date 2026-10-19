import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/task_plan_44_page.dart';

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

  testWidgets('task plan 44 renders at source 4x', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final boundaryKey = GlobalKey();
    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        home: ColoredBox(
          color: Colors.white,
          child: Center(
            child: RepaintBoundary(
              key: boundaryKey,
              child: const TaskPlan44Screen(),
            ),
          ),
        ),
      ),
    );
    await tester.runAsync(() async {
      await precacheImage(
        const AssetImage('assets/fixtures/feed-photo.png'),
        boundaryKey.currentContext!,
      );
    });
    await tester.pumpAndSettle();

    expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
    expect(tester.takeException(), isNull);

    await tester.runAsync(() async {
      final boundary = boundaryKey.currentContext!.findRenderObject()!
          as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 4);
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final output = File(
        Platform.environment['TASK_PLAN_44_RENDER_OUTPUT'] ??
            '../design_evidence/task-plan-44/r0/render.png',
      );
      await output.parent.create(recursive: true);
      await output.writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  });

  testWidgets('task plan actions remain interactive', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var back = 0;
    var message = 0;
    var complete = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Center(
          child: TaskPlan44Screen(
            onBack: () => back++,
            onMessage: () => message++,
            onComplete: () => complete++,
          ),
        ),
      ),
    );
    await tester.tap(find.byKey(const ValueKey('task-plan-back')));
    await tester.tap(find.byKey(const ValueKey('task-plan-message')));
    await tester.tap(find.byKey(const ValueKey('task-plan-complete')));
    expect((back, message, complete), (1, 1, 1));
    expect(tester.takeException(), isNull);
  });
}
