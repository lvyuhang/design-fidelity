# 原生 Android（Compose）/ iOS（SwiftUI）接入 — 预览版

仅在原生项目首次接入时读。流程、证据、契约与门禁和 Flutter 相同；生成器、原语与 harness 已提供，**尚未在真机工具链上编译和像素校准**，首个页面请按文末清单验证。

## 安装

```sh
# Android（有 settings.gradle(.kts) 时自动选 compose）
python3 <skill>/scripts/install_app.py init --app .
python3 <skill>/scripts/install_app.py page --app . --name order_detail --kotlin-package com.example.shop.fidelity

# iOS（有 .xcodeproj 时自动选 swiftui）
python3 <skill>/scripts/install_app.py init --app .
python3 <skill>/scripts/install_app.py page --app . --name order_detail --scheme Shop
```

`init` 复制原语：Android 为 Gradle 模块 `design-fidelity/`，iOS 为本地 Swift Package `DesignFidelity/`，并输出需要手动完成的工程配置（include 模块与测试依赖 / 添加本地 Package、素材文件夹引用、宿主为 App 的单元测试 target）。

| | Compose | SwiftUI |
|---|---|---|
| 生成文件 | `app/src/main/kotlin/<包>/<Page>.g.kt` | `<App>/Fidelity/<Page>.g.swift` |
| 素材 | `app/src/main/assets/design/<page>/`（AssetManager 读取） | `<App>/DesignAssets/<page>/`（文件夹引用） |
| 渲染测试 | `app/src/test/kotlin/fidelity/<Page>FidelityTest.kt`（Robolectric） | `<App>Tests/Fidelity/<Page>FidelityTests.swift`（模拟器 XCTest） |
| 场景义务 | `<Page>FidelitySceneTest.kt` + `<Page>.scene.g.json` | `<Page>FidelitySceneTests.swift` + `<Page>.scene.g.json` |
| 运行 | `./gradlew :app:testDebugUnitTest --tests '*<Page>FidelityTest'` | `xcodebuild test -scheme <Scheme> -only-testing:<Tests>/<Page>FidelityTests` |
| lint | `K001`–`K013`（Material 图标、`Color(0x…)`、`TextStyle(`、`.shadow`、`.border`、`Text(` 等） | `S001`–`S013`（SF Symbol、`Color(red:)`、`.font(`、`.shadow`、`.stroke`、`Text(` 等） |

页面写法与 Flutter 相同：把 `<Page>Scene` 作为整屏内容（Compose 不再加 `systemBarsPadding`，SwiftUI 不再包 `safeAreaInset`），用 `overrides` / `onTap` 接数据和交互，不改生成文件。Robolectric 需要 `testOptions.unitTests.isIncludeAndroidResources = true`；模拟器测试用 `TEST_RUNNER_PAGE_RENDER_OUTPUT` 接收输出路径（runner 会同时设置）。

## 与 Flutter 的差异

- **背景模糊不绘制**：Compose 无法取样节点背后的内容，SwiftUI 的 Material 没有可校准半径。生成报告会列为 `unsupported`，场景义务不可绑定，`spec` 因此不能编译——需要在页面里接受近似并对该节点写明排除原因，或改用切图。
- 图层模糊：Compose 需 API 31+；模糊半径换算集中在 `FidelityEffectMapping`（Android 框架半径与 sigma 的换算也在这里）。
- 文字：Compose 用 `LineHeightStyle(Center, Trim.None)` 与 `includeFontPadding = false` 实现等分行距；SwiftUI 用 `lineSpacing` + 上下各半行距模拟，Dynamic Type 1.3 倍按 `xxxLarge` 检查。
- 设计字体在测试中从磁盘注册（Compose `Font(File)`，iOS `CTFontManagerRegisterFontsForURL`），不进入安装包。上线字体看 `font-map.json` 的 `android` / `ios` 键。

## 首个页面验证清单

1. 原语模块能编译：Compose 模块、Swift Package 加入工程后 Debug 构建通过。
2. `<Page>FidelitySceneTest` / `SceneTests` 通过：描边带像素探测、填充叠加、蒙版和素材导出框都绑定到原语。
3. `<Page>FidelityTest` 产出 PNG 与 `.geometry.json`、`.variants.json`；`page accept` 走完门禁。
4. 与 Flutter 版本对比同一页面的门禁报告：形状、阴影、渐变区域应同样通过；若阴影或模糊整体偏软/偏硬，只调整 `FidelityEffectMapping` 一处，再重跑。
5. 把结果反馈给工具维护者，确认后移除"预览"标记。
