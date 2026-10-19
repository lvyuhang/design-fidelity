import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// Install once at test main(), before registering testWidgets.
class FidelityTestBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

/// Ordinary flutter test runs must not overwrite a previous visual baseline.
String fidelityOutputPath(String environmentVariable) =>
    Platform.environment[environmentVariable] ??
    '${Directory.systemTemp.createTempSync('lanhu-fidelity-').path}/render.png';

/// Uses Flutter's generated pubspec manifest, so a new declared font cannot be
/// silently omitted from the test's manually maintained FontLoader list.
Future<void> loadDeclaredFidelityFonts() async {
  final manifest = jsonDecode(await rootBundle.loadString('FontManifest.json'))
      as List<dynamic>;
  for (final entry in manifest.cast<Map<String, dynamic>>()) {
    final loader = FontLoader(entry['family'] as String);
    for (final font in (entry['fonts'] as List).cast<Map<String, dynamic>>()) {
      loader.addFont(rootBundle.load(font['asset'] as String));
    }
    await loader.load();
  }
}

Future<void> captureFidelityPage(
  WidgetTester tester, {
  required Widget page,
  required Size size,
  required double scale,
  required Iterable<String> imageAssets,
  required String output,
  Locale locale = const Locale('zh', 'CN'),
  Widget Function(Widget child)? appBuilder,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final boundaryKey = GlobalKey();
  final boundary = RepaintBoundary(key: boundaryKey, child: page);
  // Whole-page captures use the exact production root (Theme/Scaffold/text).
  // The legacy wrapper remains available only for isolated component tests.
  await tester.pumpWidget(appBuilder != null ? appBuilder(boundary) : MaterialApp(
    debugShowCheckedModeBanner: false,
    locale: locale,
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(textScaler: TextScaler.noScaling),
      child: Localizations.override(
        context: context,
        locale: locale,
        child: child!,
      ),
    ),
    home: DefaultTextStyle(
        style: const TextStyle(decoration: TextDecoration.none),
        child: boundary,
    ),
  ));
  await tester.runAsync(() async {
    for (final path in imageAssets.toSet()) {
      await precacheImage(AssetImage(path), boundaryKey.currentContext!,
          onError: (error, stack) => Error.throwWithStackTrace(
              StateError('Image failed to load: $path: $error'),
              stack ?? StackTrace.current));
    }
  });
  await tester.pumpAndSettle();
  expect(tester.getSize(find.byKey(boundaryKey)), size);
  expect(tester.takeException(), isNull);
  await tester.runAsync(() async {
    final boundary = boundaryKey.currentContext!.findRenderObject()!
        as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: scale);
    try {
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final file = File(output);
      await file.parent.create(recursive: true);
      await file.writeAsBytes(bytes!.buffer.asUint8List());
    } finally {
      image.dispose();
    }
  });
}
