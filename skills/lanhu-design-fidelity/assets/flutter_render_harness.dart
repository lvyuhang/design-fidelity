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

/// Layout rects of every widget keyed with `sourceKey(nodeId)` (the
/// `ValueKey<String>('lanhu:<id>')` convention of package:lanhu_fidelity),
/// relative to [boundary]. The gate compares them with source bounds.
Map<String, List<double>> collectSourceGeometry(
    WidgetTester tester, Finder boundary) {
  final origin = tester.getTopLeft(boundary);
  final result = <String, List<double>>{};
  final keyed = find.byWidgetPredicate((widget) {
    final key = widget.key;
    return key is ValueKey<String> && key.value.startsWith('lanhu:');
  }, skipOffstage: true);
  for (final element in keyed.evaluate()) {
    final render = element.renderObject;
    if (render is! RenderBox || !render.hasSize) continue;
    final topLeft = render.localToGlobal(Offset.zero) - origin;
    final id = (element.widget.key! as ValueKey<String>).value.substring(6);
    result[id] = <double>[
      topLeft.dx,
      topLeft.dy,
      render.size.width,
      render.size.height,
    ];
  }
  return result;
}

Future<void> _writeJson(String path, Object value) async {
  final file = File(path);
  await file.parent.create(recursive: true);
  await file.writeAsString(const JsonEncoder.withIndent(' ').convert(value));
}

Widget _defaultApp(Widget boundary, Locale locale, {bool pinTextScale = true}) {
  return MaterialApp(
    debugShowCheckedModeBanner: false,
    locale: locale,
    builder: (context, child) => MediaQuery(
      data: pinTextScale
          ? MediaQuery.of(context).copyWith(textScaler: TextScaler.noScaling)
          : MediaQuery.of(context),
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
  );
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
  await tester.pumpWidget(appBuilder != null
      ? appBuilder(boundary)
      : _defaultApp(boundary, locale));
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
  final geometry = collectSourceGeometry(tester, find.byKey(boundaryKey));
  await tester.runAsync(() async {
    if (geometry.isNotEmpty) {
      await _writeJson('$output.geometry.json', <String, Object>{
        'schema': 1,
        'canvas': <double>[size.width, size.height],
        'nodes': geometry,
      });
    }
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

/// Lays the page out at other screen widths and accessibility text scales and
/// records geometry plus any framework exception (e.g. RenderFlex overflow).
///
/// Writes `<output>.variants.json`; `visual_fidelity_gate.py` checks it when
/// the contract enables `responsive_check`. Call after [captureFidelityPage]
/// in the same test with the same [page]/[appBuilder].
Future<void> captureResponsiveVariants(
  WidgetTester tester, {
  required Widget page,
  required double height,
  required String output,
  List<double> widths = const <double>[360, 414],
  List<double> textScales = const <double>[1.0, 1.3],
  Locale locale = const Locale('zh', 'CN'),
  Widget Function(Widget child)? appBuilder,
}) async {
  final variants = <Map<String, Object?>>[];
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  for (final width in widths) {
    for (final textScale in textScales) {
      tester.view.physicalSize = Size(width, height);
      tester.view.devicePixelRatio = 1;
      tester.platformDispatcher.textScaleFactorTestValue = textScale;
      final boundaryKey = GlobalKey();
      final boundary = RepaintBoundary(key: boundaryKey, child: page);
      await tester.pumpWidget(appBuilder != null
          ? appBuilder(boundary)
          : _defaultApp(boundary, locale, pinTextScale: false));
      await tester.pumpAndSettle();
      final error = tester.takeException();
      variants.add(<String, Object?>{
        'width': width,
        'height': height,
        'text_scale': textScale,
        'exception': error?.toString(),
        'nodes': collectSourceGeometry(tester, find.byKey(boundaryKey)),
      });
    }
  }
  tester.view.resetPhysicalSize();
  tester.view.resetDevicePixelRatio();
  await tester.runAsync(() => _writeJson('$output.variants.json',
      <String, Object>{'schema': 1, 'variants': variants}));
}
