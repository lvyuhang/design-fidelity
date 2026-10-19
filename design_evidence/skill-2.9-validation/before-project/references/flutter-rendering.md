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

## 统一截图工具

首次接入复制 `assets/flutter_render_harness.dart` 到项目 `test/support/`，后续页面复用。把 helper 也登记为 `implementation_inputs`。它按 Flutter 自动生成的 FontManifest 加载所有已声明字体、启用阴影、预加载传入图片，并固定画布、语言和文本缩放；无需逐页复制 FontLoader 和截图管线。

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'support/fidelity_render_harness.dart';
// 导入项目 TargetPage 和页面图片清单。

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  testWidgets('source canvas', (tester) async {
    await captureFidelityPage(tester,
      page: const TargetPage(),
      size: const Size(375, 812),
      scale: 4,
      locale: const Locale('zh', 'CN'),
      imageAssets: TargetPageAssets.all,
      output: fidelityOutputPath('PAGE_RENDER_OUTPUT'),
    );
    // 补本页必要的占位形状、几何和交互断言。
  });
}
```

页面图片列表必须完整。网络图片、时间、动画或随机内容使用固定测试夹具。helper 会阻止声明图片加载失败，但无法发现没有登记的图片。字体文件含字不等于 Widget 用了正确 family/weight，仍需代码映射与视觉验收。将所有已加载项目字体纳入 pinned_files；框架自带字体随固定 SDK 版本记录。

正常门禁由运行器设置输出变量。直接执行普通 `flutter test` 时，`fidelityOutputPath` 使用唯一临时目录，避免覆盖已存 R0/最终基线。

`locale` 必须与契约环境一致。旧测试仅在契约声明 zh_CN、实际却使用默认 en_US 时，迁移会改变个别字形像素。先在实际旧环境做兼容回放，再记录语言修正；不要掩盖差异或改阈值。框架本地化文案需要项目相应 delegates，此 helper 不替应用配置完整本地化。

## 双环境检查

Flutter test 的 Skia 字形和浏览器 CanvasKit/HTML 渲染可能不同。自动门禁使用交付目标渲染器建立基线；如果产品交付 Web，再用浏览器打开页面检查一次控制台、资源加载和实际视口。两个环境的截图不要混在同一个像素基线中。


## 收据与最终环境

在契约 `implementation_inputs` 中登记此测试、页面及其子组件、pubspec.yaml、pubspec.lock；图片和字体登记为 pinned_files。截图前将布局文本缩放固定到 environment.text_scale，并固定语言与选中状态。把实际 Flutter/engine 版本记录到 environment.renderer_version。

通过 `render_with_receipt.py` 调用截图测试，避免单独重用以前的 PNG。包装器检查输入前后哈希、输出新鲜度和尺寸，不会解析 Flutter Widget 树；文件声明、真实字体应用和浏览器检查仍由执行者负责。

源图尺寸代表整张画板。现版本初始化器会拒绝直接拿局部截图匹配整张画布；局部组件应保存完整源图并以节点 ROI 检测，或另行实现并验证坐标转换，不能拉伸局部截图充当整页。
