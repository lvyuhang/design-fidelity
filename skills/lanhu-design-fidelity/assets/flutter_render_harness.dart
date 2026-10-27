import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lanhu_fidelity/lanhu_fidelity.dart';

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

/// Loads every design font listed in the fidelity font map from disk under its
/// `runtime_family`, and makes generated tokens use those families.
///
/// The files (e.g. PingFang extracted on the developer's Mac) are only used to
/// render fidelity tests; they are never declared in pubspec or shipped.
Future<void> loadSourceFontMap(String path) async {
  SourceFonts.useDesignFonts = true;
  final file = File(path);
  final map = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
  final families = <String, Set<String>>{};
  for (final entry in (map['fonts'] as Map<String, dynamic>? ?? {}).values) {
    final font = entry as Map<String, dynamic>;
    final family = font['runtime_family'] as String?;
    final fontPath = font['path'] as String?;
    if (family == null || fontPath == null) continue;
    final home = Platform.environment['HOME'] ?? '';
    final expanded =
        fontPath.startsWith('~/') ? '$home/${fontPath.substring(2)}' : fontPath;
    final resolved = File(expanded).isAbsolute
        ? expanded
        : '${file.parent.path}/$expanded';
    families.putIfAbsent(family, () => <String>{}).add(resolved);
  }
  for (final MapEntry(key: family, value: paths) in families.entries) {
    final loader = FontLoader(family);
    for (final fontPath in paths) {
      final bytes = await File(fontPath).readAsBytes();
      loader.addFont(Future.value(ByteData.sublistView(bytes)));
    }
    await loader.load();
  }
}

/// Screen sizes and safe areas checked by [captureResponsiveVariants]
/// (logical px). Names must match the contract's `responsive_check.devices`.
class FidelityDevice {
  const FidelityDevice(this.name, this.size, this.padding);

  final String name;
  final Size size;
  final EdgeInsets padding;
}

const List<FidelityDevice> lanhuDefaultDevices = <FidelityDevice>[
  FidelityDevice('iphone_se', Size(375, 667), EdgeInsets.only(top: 20)),
  FidelityDevice('iphone_15', Size(393, 852), EdgeInsets.only(top: 59, bottom: 34)),
  FidelityDevice('iphone_15_pro_max', Size(430, 932), EdgeInsets.only(top: 59, bottom: 34)),
  FidelityDevice('android_compact', Size(360, 800), EdgeInsets.only(top: 24)),
  FidelityDevice('android_large', Size(412, 915), EdgeInsets.only(top: 24, bottom: 24)),
];

void _setViewPadding(WidgetTester tester, EdgeInsets padding) {
  // devicePixelRatio is 1 in fidelity renders, so logical == physical.
  final fake = FakeViewPadding(
      left: padding.left, top: padding.top, right: padding.right, bottom: padding.bottom);
  tester.view.padding = fake;
  tester.view.viewPadding = fake;
}

/// Union of the laid-out paragraphs under [root], relative to [origin].
///
/// An override fills the node frame, so the frame alone cannot show text
/// shifted inside it (padding, alignment); the paragraph rect can.
Rect? _paragraphRect(RenderObject root, Offset origin) {
  Rect? result;
  void visit(RenderObject child) {
    if (child is RenderParagraph && child.hasSize) {
      final rect = (child.localToGlobal(Offset.zero) - origin) & child.size;
      result = result == null ? rect : result!.expandToInclude(rect);
      return;
    }
    child.visitChildren(visit);
  }

  visit(root);
  return result;
}

/// Paragraph rects per keyed node (see [collectSourceGeometry]).
Map<String, List<double>> collectSourceText(WidgetTester tester, Finder boundary) {
  final origin = tester.getTopLeft(boundary);
  final result = <String, List<double>>{};
  for (final element in _keyedSourceElements().evaluate()) {
    final render = element.renderObject;
    if (render == null) continue;
    final rect = _paragraphRect(render, origin);
    if (rect == null) continue;
    final id = (element.widget.key! as ValueKey<String>).value.substring(6);
    result[id] = <double>[rect.left, rect.top, rect.width, rect.height];
  }
  return result;
}

Finder _keyedSourceElements() => find.byWidgetPredicate((widget) {
      final key = widget.key;
      return key is ValueKey<String> && key.value.startsWith('lanhu:');
    }, skipOffstage: true);

/// Layout rects of every widget keyed with `sourceKey(nodeId)` (the
/// `ValueKey<String>('lanhu:<id>')` convention of package:lanhu_fidelity),
/// relative to [boundary]. The gate compares them with source bounds.
Map<String, List<double>> collectSourceGeometry(
    WidgetTester tester, Finder boundary) {
  final origin = tester.getTopLeft(boundary);
  final result = <String, List<double>>{};
  for (final element in _keyedSourceElements().evaluate()) {
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
  EdgeInsets padding = EdgeInsets.zero,
  Locale locale = const Locale('zh', 'CN'),
  Widget Function(Widget child)? appBuilder,
}) async {
  SourceFonts.useDesignFonts = true;
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  // Render with the design's own safe area so the page keeps source coordinates.
  _setViewPadding(tester, padding);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(tester.view.resetPadding);
  addTearDown(tester.view.resetViewPadding);
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
  final textGeometry = collectSourceText(tester, find.byKey(boundaryKey));
  await tester.runAsync(() async {
    if (geometry.isNotEmpty) {
      await _writeJson('$output.geometry.json', <String, Object>{
        'schema': 1,
        'canvas': <double>[size.width, size.height],
        'nodes': geometry,
        'text_nodes': textGeometry,
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

/// Lays the page out on each device profile (screen size + safe area) at each
/// text scale, and records geometry, paragraphs, whether the page scrolls and
/// any framework exception (e.g. RenderFlex overflow).
///
/// Writes `<output>.variants.json`; `visual_fidelity_gate.py` checks it when
/// the contract enables `responsive_check`. Call after [captureFidelityPage]
/// in the same test with the same [page]/[appBuilder].
Future<void> captureResponsiveVariants(
  WidgetTester tester, {
  required Widget page,
  required String output,
  List<FidelityDevice> devices = lanhuDefaultDevices,
  List<double> textScales = const <double>[1.0, 1.3],
  Locale locale = const Locale('zh', 'CN'),
  Widget Function(Widget child)? appBuilder,
}) async {
  SourceFonts.useDesignFonts = true;
  final variants = <Map<String, Object?>>[];
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  for (final device in devices) {
    for (final textScale in textScales) {
      tester.view.physicalSize = device.size;
      tester.view.devicePixelRatio = 1;
      _setViewPadding(tester, device.padding);
      tester.platformDispatcher.textScaleFactorTestValue = textScale;
      final boundaryKey = GlobalKey();
      final boundary = RepaintBoundary(key: boundaryKey, child: page);
      await tester.pumpWidget(appBuilder != null
          ? appBuilder(boundary)
          : _defaultApp(boundary, locale, pinTextScale: false));
      await tester.pumpAndSettle();
      final error = tester.takeException();
      final root = find.byKey(boundaryKey);
      variants.add(<String, Object?>{
        'device': device.name,
        'width': device.size.width,
        'height': device.size.height,
        'padding': <String, double>{'top': device.padding.top, 'bottom': device.padding.bottom},
        'text_scale': textScale,
        'exception': error?.toString(),
        'scrollable': find
            .descendant(of: root, matching: find.byType(Scrollable))
            .evaluate()
            .isNotEmpty,
        'nodes': collectSourceGeometry(tester, root),
        'text_nodes': collectSourceText(tester, root),
      });
    }
  }
  tester.view.resetPhysicalSize();
  tester.view.resetDevicePixelRatio();
  tester.view.resetPadding();
  tester.view.resetViewPadding();
  await tester.runAsync(() => _writeJson('$output.variants.json',
      <String, Object>{'schema': 2, 'variants': variants}));
}
