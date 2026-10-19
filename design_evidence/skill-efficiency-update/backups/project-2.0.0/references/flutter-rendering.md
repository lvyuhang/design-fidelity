# Flutter 固定渲染适配

## 页面实现

- 设计画布为 375px 时，让待测根 Widget 的逻辑宽度保持 375，不根据桌面浏览器宽度拉伸。预览器可以在外层居中或缩放，待测 Widget 本身保持源画布尺寸。
- 对页面级精确还原优先使用源节点层级和明确约束。不要把所有节点绝对定位在一个 Stack 中；可重复业务行仍应封装成组件，但其外部几何需与源节点一致。
- 图片按蓝湖导出的画框放置。`BoxFit.cover`、`contain`、裁剪和九宫格会改变可见主体，必须与源图层行为一致。
- 所有关键 Widget 使用稳定 Key 或保留源节点 ID 映射，便于渲染测试和后续更新。

## 字体

1. 在 `pubspec.yaml` 声明实际字体文件和每个 weight。
2. 运行时 `fontFamily` 必须与声明一致；只写系统字体名称不能证明测试环境已加载该字体。
3. Widget 测试中使用 `FontLoader` 加载相同文件，加载完成后再 pump 页面。
4. 字体子集必须覆盖页面全部中文、数字、标点和状态文本。子集变化后重新跑整页视觉回归。
5. 原字体无法合法取得时，记录替代字体并单独校准文字区域；不能声称其像素级一致。

## 稳定截图测试骨架

```dart
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class ProductionShadowBinding extends AutomatedTestWidgetsFlutterBinding {
  @override
  bool get disableShadows => false;
}

void main() {
  ProductionShadowBinding();

  // 在此声明 imageAssets 并导入 TargetPage。
  setUpAll(() async {
    final loader = FontLoader('DesignFont')
      ..addFont(rootBundle.load('assets/fonts/Design-Regular.otf'));
    await loader.load();
  });

  testWidgets('renders source canvas at 4x', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final boundaryKey = GlobalKey();
    await tester.pumpWidget(MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RepaintBoundary(key: boundaryKey, child: const TargetPage()),
    ));

    await tester.runAsync(() async {
      for (final asset in imageAssets) {
        await precacheImage(AssetImage(asset), boundaryKey.currentContext!);
      }
    });
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(boundaryKey)), const Size(375, 812));
    expect(tester.takeException(), isNull);

    await tester.runAsync(() async {
      final boundary = boundaryKey.currentContext!.findRenderObject()
          as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 4);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      await File('candidate-4x.png').writeAsBytes(data!.buffer.asUint8List());
      image.dispose();
    });
  });
}
```

骨架中的 `TargetPage`、`imageAssets`、字体文件和输出路径需要映射到项目实际值；`imageAssets` 必须列出该页面的全部图片。把图片列表集中管理并在截图前逐一 `precacheImage`。如果页面有网络图片、时间、动画或随机内容，替换为固定测试夹具。

## 双环境检查

Flutter test 的 Skia 字形和浏览器 CanvasKit/HTML 渲染可能不同。自动门禁使用交付目标渲染器建立基线；如果产品交付 Web，再用浏览器打开页面检查一次控制台、资源加载和实际视口。两个环境的截图不要混在同一个像素基线中。


## 收据与最终环境

在契约 `implementation_inputs` 中登记此测试、页面及其子组件、pubspec.yaml、pubspec.lock；图片和字体登记为 pinned_files。截图前将布局文本缩放固定到 environment.text_scale，并固定语言与选中状态。把实际 Flutter/engine 版本记录到 environment.renderer_version。

通过 `render_with_receipt.py` 调用截图测试，避免单独重用以前的 PNG。包装器检查输入前后哈希、输出新鲜度和尺寸，不会解析 Flutter Widget 树；文件声明、真实字体应用和浏览器检查仍由执行者负责。

源图尺寸代表整张画板。现版本初始化器会拒绝直接拿局部截图匹配整张画布；局部组件应保存完整源图并以节点 ROI 检测，或另行实现并验证坐标转换，不能拉伸局部截图充当整页。
