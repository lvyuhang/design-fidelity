# Flutter 截图接入

仅在首次接入或修改渲染环境时读。页面已有测试与 harness 时复用，只改页面参数。

## 页面与字体

根 Widget 保持源逻辑画布，375px 稿按 375 展示；桌面外壳可居中/缩放。使用源层级与明确约束，重复业务行封装组件。图片 fit/裁剪符合源图层；保留稳定 Key/node_id。

pubspec.yaml 声明实际字体文件与 weight，Widget 使用对应 family/weight。测试加载同文件，中文/数字/标点/状态文本及历史页字符必须全覆盖。无法取得原字体时明确替代并单独校准，不声称像素一致。

## 复用 harness

首次复制 assets/flutter_render_harness.dart 到 test/support/fidelity_render_harness.dart，并登记为 implementation_inputs。它加载 FontManifest 字体、开启生产阴影、预加载图片、固定画布。整页传 appBuilder，直接复用 main.dart 使用的生产根节点（包含 Theme、Scaffold、DefaultTextStyle、locale/textScaler）；不能在测试中另造一套默认样式。已有项目复用字体文件与映射，prepare 只校验本页字符覆盖，缺字才补字体。

```dart
void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  testWidgets('source canvas', (tester) async {
    await captureFidelityPage(tester,
      page: const TargetPage(),
      appBuilder: (child) => ProductionAppRoot(child: child),
      size: const Size(375, 812), scale: 4,
      locale: const Locale('zh', 'CN'),
      imageAssets: TargetPageAssets.all,
      output: fidelityOutputPath('PAGE_RENDER_OUTPUT'),
    );
    // 添加本页必要的形状/交互断言。
  });
}
```

ProductionAppRoot 是项目的真实入口，不是新增依赖。它须可注入页面 child，并由 main 与截图共同调用。helper 未传 appBuilder 的旧入口仅用于孤立组件测试。导入 material、flutter_test、helper 与页面；尺寸/倍数按真实参考图修改。图片清单完整，网络内容/动画/时间使用固定夹具。helper 只校验已声明图片，cmap 有字不证明运行时选对字重。所有已加载项目字体列入 pinned_files；SDK 自带字体随固定 SDK 记录。

## 输入与目标环境

implementation_inputs 列页面/子组件、测试、harness、pubspec.yaml/lock；图片/字体 pinned。记录实际 Flutter/engine、locale、text_scale、状态；截图使用配置入口生成新 PNG 与收据。普通 flutter test 的 helper 默认唯一临时路径，避免覆盖基线。

locale 与实际环境一致；迁移语言可能改变字形，先保留旧环境回放再校准，不能静默放宽。完整本地化 delegates 由项目提供。

Widget test 与实际交付渲染器的字形/效果可能不同，不能混用像素基线。Web 交付还须浏览器检查视口、资源、控制台和真实页面；包装器不检查 Widget 树。局部组件用完整源图 ROI，不能把局部截图拉伸到整页。
