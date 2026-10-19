import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/components/social_components.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    final loader = FontLoader('SourcePingFang');
    loader.addFont(rootBundle.load('assets/fonts/PingFangSC-Regular.otf'));
    loader.addFont(rootBundle.load('assets/fonts/PingFangSC-Medium.otf'));
    loader.addFont(rootBundle.load('assets/fonts/PingFangSC-Semibold.otf'));
    await loader.load();
  });
  testWidgets('half-column feed retains source size and independent actions',
      (tester) async {
    final actions = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: Center(
            child: FeedComponentStage(
                onOpen: () => actions.add('open'),
                onLike: () => actions.add('like'),
                onProfile: () => actions.add('profile')))));
    expect(
        tester.getSize(find.byType(FeedComponentStage)), const Size(375, 342));
    expect(tester.getSize(find.byType(FeedCard)), const Size(181.5, 318));
    for (final id in ['打开动态', '点赞动态', '查看作者']) {
      await tester.tap(find.byKey(ValueKey(id)));
    }
    expect(actions, ['open', 'like', 'profile']);
    final caption = tester.widget<Text>(find.text('可爱到心巴上的样子，这也太治愈了吧～'));
    expect(caption.softWrap, true);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
      'controlled gender state shows source-selected asset and emits both choices',
      (tester) async {
    final selections = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: Center(child: GenderSelection(onSelect: selections.add))));
    expect(find.text('选择性别提交后将不可修改'), findsNothing);
    await tester.tap(find.byKey(const ValueKey('选择女生')));
    await tester.tap(find.byKey(const ValueKey('选择男生')));
    expect(selections, ['female', 'male']);
    await tester.pumpWidget(MaterialApp(
        home: Center(
            child: GenderSelection(
                femaleSelected: true, onSelect: selections.add))));
    expect(find.text('选择性别提交后将不可修改'), findsOneWidget);
    expect(tester.getSize(find.byType(GenderSelection)), const Size(375, 350));
    expect(tester.takeException(), isNull);
  });
  testWidgets('comments retain rich mention and route five independent actions',
      (tester) async {
    final events = <String>[];
    await tester.pumpWidget(MaterialApp(
        home: Center(
            child: CommentPanel(
                onClose: () => events.add('close'),
                onReply: (id) => events.add(id),
                onDelete: () => events.add('delete'),
                onExpand: () => events.add('expand')))));
    for (final id in ['关闭评论', '回复作者', '回复momo', '删除评论', '展开3条回复']) {
      await tester.tap(find.byKey(ValueKey(id)));
    }
    expect(events, ['close', 'author', 'momo', 'delete', 'expand']);
    final body = tester.widget<Text>(find.text('回复@momo：给你发消息了～快回复我'));
    final mention = (body.textSpan as TextSpan).children![1] as TextSpan;
    expect(mention.text, '@momo');
    expect(mention.style!.color, const Color(0xFFBC914A));
    expect(body.softWrap, true);
    expect(tester.takeException(), isNull);
  });
  for (final entry in <String, Widget>{
    'feed-stage': const FeedComponentStage(),
    'gender_none': const GenderSelection(),
    'gender_female': const GenderSelection(femaleSelected: true),
    'comments': const CommentPanel(),
  }.entries) {
    testWidgets('render ${entry.key} at source 4x', (tester) async {
      final key = GlobalKey();
      await tester.pumpWidget(MaterialApp(
          home: Center(child: RepaintBoundary(key: key, child: entry.value))));
      await tester.runAsync(() async {
        for (final asset in SocialAssets.all) {
          await precacheImage(AssetImage(asset), key.currentContext!);
        }
      });
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.runAsync(() async {
        final boundary =
            key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
        final img = await boundary.toImage(pixelRatio: 4);
        final bytes = await img.toByteData(format: ui.ImageByteFormat.png);
        await File('../design_evidence/flutter-${entry.key}-4x.png')
            .writeAsBytes(bytes!.buffer.asUint8List());
        img.dispose();
      });
    });
  }
}
