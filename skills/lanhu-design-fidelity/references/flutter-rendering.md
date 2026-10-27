# Flutter 接入

仅在首次接入或修改渲染环境时读。

## 原语包

把 `assets/flutter/lanhu_fidelity` 复制到项目（如 `packages/lanhu_fidelity`），在 `pubspec.yaml` 中加 path 依赖，然后在包目录运行一次 `flutter test`，确认正反例像素测试全部通过。升级 Flutter 后重跑。阴影和模糊的半径到 sigma 换算只在 `LanhuEffectMapping` 中定义；需要重新校准时只改这一处，再重跑包测试和受影响页面。

## 字体

`pubspec.yaml` 声明实际字体文件与字重，字体映射（`font_map`）的 `runtime_family` 与之对应。生成的 token 使用 `runtime_family`。中文、数字、标点和状态文本都必须被覆盖；prepare 会按每个 text run 检查 cmap。取不到原字体时明确替代并单独校准，不声称像素一致。

## render 测试与 harness

`page generate` 首次会创建 `test/<page>_test.dart`，并把 `assets/flutter_render_harness.dart` 复制到 `test/support/`。之后由项目维护：

```dart
void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  testWidgets('source canvas', (tester) async {
    final output = fidelityOutputPath('PAGE_RENDER_OUTPUT');
    const page = WithdrawPage(/* 固定夹具数据 */);
    await captureFidelityPage(tester,
        page: page,
        appBuilder: (child) => ProductionAppRoot(child: child),
        size: Withdraw2Scene.designSize, scale: 4,
        imageAssets: Withdraw2Assets.all, output: output);
    await captureResponsiveVariants(tester,
        page: page,
        appBuilder: (child) => ProductionAppRoot(child: child),
        height: Withdraw2Scene.designSize.height, output: output);
  });
}
```

- `ProductionAppRoot` 是项目真实入口（Theme、Scaffold、DefaultTextStyle、locale），由 `main` 与截图共同调用，不在测试里另造默认样式。未传 `appBuilder` 的旧入口只用于孤立组件测试。
- harness 会加载 FontManifest 中的字体、开启生产阴影、预加载图片、固定画布，并写出几何与多尺寸 sidecar。
- 网络内容、动画和时间使用固定夹具。普通 `flutter test` 默认写到唯一临时路径，不会覆盖基线。

## 输入与目标环境

`implementation_inputs` 包含页面与组件、生成文件、render 测试、scene 测试、harness、`pubspec.yaml/lock`；图片和字体单独固定。页面配置的 `renderer_version`、`platform` 写入契约环境。Widget test 与实际交付渲染器的字形和效果可能不同，不能混用像素基线；Web 交付还要在浏览器中检查视口、资源和控制台。
