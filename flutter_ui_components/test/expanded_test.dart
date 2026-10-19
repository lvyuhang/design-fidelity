import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/components/expanded_components.dart';
import 'package:juxing_components/main.dart';
import 'package:juxing_components/components/social_components.dart';
import 'package:juxing_components/components/login_components.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    final loader = FontLoader('SourcePingFang');
    loader.addFont(rootBundle.load('assets/fonts/PingFangSC-Regular.otf'));
    loader.addFont(rootBundle.load('assets/fonts/PingFangSC-Medium.otf'));
    loader.addFont(rootBundle.load('assets/fonts/PingFangSC-Semibold.otf'));
    await loader.load();
  });
  for (final width in [375.0, 1240.0]) {
    testWidgets('gallery keeps all eight samples at 375px on $width viewport',
        (tester) async {
      tester.view.physicalSize = Size(width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(const ComponentLab());
      await tester.pumpAndSettle();
      for (final type in [
        ModalComponentStage,
        NavigationComponentStage,
        AppealComponentStage,
        LoginComponentStage,
        FeedComponentStage,
        CommentPanel,
      ]) {
        expect(tester.getSize(find.byType(type)).width, 375);
      }
      for (final stage in find.byType(GenderSelection).evaluate()) {
        expect((stage.renderObject as RenderBox).size.width, 375);
      }
      expect(find.text('04 / 登录按钮与协议'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets('modal maintains source geometry and emits both actions',
      (tester) async {
    var cancel = 0, confirm = 0;
    await tester.pumpWidget(MaterialApp(
        home: Center(
            child: ModalComponentStage(
                onCancel: () => cancel++, onConfirm: () => confirm++))));
    expect(
        tester.getSize(find.byType(ModalComponentStage)), const Size(375, 280));
    expect(tester.getSize(find.byType(CacheClearDialog)), const Size(330, 228));
    expect(
        tester.getTopLeft(find.byType(CacheClearDialog)) -
            tester.getTopLeft(find.byType(ModalComponentStage)),
        const Offset(23, 22));
    // Tap on the text, not only empty button padding, to check hit testing.
    await tester.tapAt(tester.getCenter(find.text('取消')));
    await tester.tapAt(tester.getCenter(find.text('清除记录')));
    expect([cancel, confirm], [1, 1]);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
      'navigation emits every item without fabricating unchecked states',
      (tester) async {
    final selected = <int>[];
    await tester.pumpWidget(MaterialApp(
        home: Center(child: NavigationComponentStage(onSelect: selected.add))));
    expect(tester.getSize(find.byType(NavigationComponentStage)),
        const Size(375, 98));
    expect(tester.getSize(find.byType(JuxingBottomNavigation)),
        const Size(347, 56));
    for (var i = 0; i < 5; i++) {
      await tester.tap(find.byKey(ValueKey('nav-$i')));
    }
    expect(selected, [0, 1, 2, 3, 4]);
    expect(tester.takeException(), isNull);
  });
  testWidgets('business card retains 16px inset and appeal action',
      (tester) async {
    var actions = 0;
    await tester.pumpWidget(MaterialApp(
        home: Center(child: AppealComponentStage(onAppeal: () => actions++))));
    expect(tester.getSize(find.byType(AppealComponentStage)),
        const Size(375, 125));
    expect(tester.getSize(find.byType(AppealCard)), const Size(343, 116));
    expect(
        tester.getTopLeft(find.byType(AppealCard)) -
            tester.getTopLeft(find.byType(AppealComponentStage)),
        const Offset(16, 4));
    await tester.tapAt(tester.getCenter(find.text('申诉')));
    expect(actions, 1);
    expect(tester.takeException(), isNull);
  });
  for (final entry in <String, Widget>{
    'modal': const ModalComponentStage(),
    'nav': const NavigationComponentStage(),
    'appeal': const AppealComponentStage()
  }.entries) {
    testWidgets('render ${entry.key} at original 4x', (tester) async {
      final key = GlobalKey();
      await tester.pumpWidget(MaterialApp(
          home: Center(child: RepaintBoundary(key: key, child: entry.value))));
      await tester.runAsync(() async {
        for (final asset in [ExpandedAssets.home, ExpandedAssets.shield]) {
          await precacheImage(AssetImage(asset), key.currentContext!);
        }
      });
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.runAsync(() async {
        final boundary =
            key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
        final image = await boundary.toImage(pixelRatio: 4);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        await File('../design_evidence/flutter-${entry.key}-4x.png')
            .writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    });
  }
}
