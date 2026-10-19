import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/widgets.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fidelity_smoke/main.dart';

void main() {
  testWidgets('render independent source fixture', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final key = GlobalKey();
    await tester.pumpWidget(Directionality(textDirection: TextDirection.ltr,
      child: RepaintBoundary(key: key, child: SourceFixture(
        iconOffset: double.parse(const String.fromEnvironment('OFFSET', defaultValue: '0'))))));
    await tester.runAsync(() => precacheImage(const AssetImage('assets/icon.png'), key.currentContext!));
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(key)), const Size(375, 812));
    expect(tester.takeException(), isNull);
    await tester.runAsync(() async {
      final boundary = key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 2);
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final file = File(const String.fromEnvironment('OUTPUT', defaultValue: 'render.png'));
      await file.parent.create(recursive: true);
      await file.writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  });
}
