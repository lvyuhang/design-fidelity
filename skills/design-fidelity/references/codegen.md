# 生成与组件化

## 生成了什么

`page generate`（`scripts/generate_flutter.py`）读取 prepare 计划和源节点，输出：

- `<page>.g.dart`：`<Page>Tokens`（颜色、文字样式）、`<Page>Assets`（已安装素材）、`<Page>Scene`（整页，按源层级分组的方法）。每个节点包在 `SourceNode`（`sourceKey(node_id)`）里，几何门禁靠它定位。
- `<page>.codegen.json`：每个节点的处置、`unsupported`、`issues`、系统 chrome、素材清单和 `draft_node_decisions`；`output_sha256` 用来检测手改。
- `test/<page>_scene_test.g.dart`：scene 义务测试，见下文。
- `test/<page>_test.dart`（仅首次）：render 测试，归项目所有，可以修改。

生成是确定性的：同一输入输出相同字节。源快照变化后先 `prepare` 再 `generate`。

## 页面代码怎么写

不要编辑 `.g.dart`。在登记于 `page_inputs` 的页面文件里组合 Scene：

```dart
class WithdrawPage extends StatelessWidget {
  const WithdrawPage({super.key, required this.account, required this.onConfirm});
  final String account;
  final VoidCallback onConfirm;

  @override
  Widget build(BuildContext context) => Withdraw2Scene(
        overrides: {
          // 动态文案：仍用源样式 token，宽度约束交给弹性布局。
          '支付宝账号节点ID': (context) => SourceText(account,
              style: Withdraw2Tokens.t14w400h20cFF22242A,
              maxLines: 1, overflow: TextOverflow.ellipsis),
        },
        onTap: {'确认按钮节点ID': onConfirm},
      );
}
```

- override 的组件放在原节点的布局框里，`sourceKey` 保留，几何门禁照常检查。
- 重复的业务行（列表项、卡片）抽成组件后，用 override 替换其所在的组；组件内部同样只用原语与 token。
- 需要真正可变的布局时，把对应的组改写为 Row/Column，间距取自源坐标差；复合行规则见[节点决策](implementation-decisions.md#复合行与动态文字)。
- 生成器的响应式规则：整宽元素随屏宽拉伸，居中元素保持居中，靠右元素按右边距锚定。
- 安全区与屏幕高度：`designPadding` 是设计稿中的状态栏与 Home Indicator 高度。根层节点在运行时按 `MediaQuery` 实际安全区平移（`dy`、`dyBottom`）；画布下部、距底部安全区 48 以内的根层节点是 footer，固定在底部安全区之上（报告 `layout.footer`、决策 `vertical_anchor: bottom`）。可用高度小于设计高度时主体可滚动，footer 不动；可用高度更大时中间留白。Scene 是整页组件：作为 `Scaffold.body`，不要外包 `SafeArea` 或加 `AppBar`；嵌入预览时传 `adaptSafeArea: false`。
- 字体：font map 条目的 `ios` / `android` 生成 `sourceFontFamily(...)`，`null` 为系统字体。还原度渲染时 harness 从磁盘加载 `path` 字体并让所有 token 使用设计字体。

## lint 规则

| 规则 | 拦截 | 改用 |
|---|---|---|
| L001 | `Icons.*` / `CupertinoIcons.*` | `SourceAsset`、完整 `SourcePathShape` 或 `SourcePlaceholder` |
| L002 | 只含箭头/emoji 字形的字符串 | 同上 |
| L003 | `Color(0x…)`、`Colors.*`（`transparent` 除外） | `<Page>Tokens` |
| L004 | `TextStyle(` | token 或 `sourceTextStyle` |
| L005 | `BoxShadow`、`Shadow`、`PhysicalModel`、`elevation:` | `SourceShadow` |
| L006 | `ImageFilter.blur`、`BackdropFilter`、`MaskFilter.blur` | `SourceBackdropBlur` / `SourceLayerBlur` |
| L007 | `Border.all`、`Border(`、`BorderSide`、`strokeAlign` | `SourceBorder(position: …)` |
| L008 | `IconButton` | `GestureDetector` 包源组件，热区单独外扩 |
| L009 | `FittedBox` | 修布局；确需缩放时写明原因 |
| L010 | `TextScaler.noScaling`、`textScaleFactor:` | 生产代码保留无障碍缩放 |
| L011 | 生成文件被手改 | override 或重新生成 |
| L012 | `Image.asset`、`AssetImage` | `SourceAsset(exportRect: …)` |
| L013 | `Text(`、`RichText(` | `SourceText` / `SourceText.rich` |

例外写法：在同一行或上一行写 `// fidelity-lint: allow L009 原因`，报告会列出所有例外。测试文件和原语包本身不受检查。

## scene 义务测试

源中出现的描边、重合填充栈、遮罩、背景模糊、跨遮罩叠层和缺图效果，都会生成对应用例：

- **绑定**：从生产 Scene 的 widget 树中找到该节点使用的原语，断言参数等于源值（例如描边宽度与位置、模糊半径与饱和度、填充层数）。
- **像素**：描边在灰底上分别渲染有边框与无边框两份，检查边框带位置正确且另一侧没有溢出；填充栈在整页渲染中找一个不被其他节点覆盖的采样点，与源颜色的合成结果比较。

原语自身的机制（内外描边、阴影挖空、模糊衰减等）由 `assets/flutter/design_fidelity/test` 中的正反例像素测试证明，接入时运行一次即可。

## 几何与多尺寸门禁

- render 测试里的 `captureFidelityPage` 会写出 `render.png.geometry.json`，`captureResponsiveVariants` 会写出 `render.png.variants.json`。这两个文件必须和渲染收据中记录的哈希一致。
- 几何：非文字节点的左、上、宽、高容差 0.5px；文字比较对齐边（1px）、top 和 line box 高度（0.5px），宽度偏差超过 3px 时提示检查字体文件、字重或字距。
- 多尺寸：在 `responsive_check.devices`（默认 iPhone SE / 15 / 15 Pro Max、Android 360×800 / 412×915，各带真实安全区）与 1.0/1.3 倍字体下检查。阻断项：`exceptions`、`horizontal_overflow`、`vertical_clip`（超出屏幕且不可滚动）、`under_status_bar`（文字进入顶部安全区）、`under_home_indicator`（footer 压到底部安全区）、`missing`（契约要求的机型没有渲染）；`text_overlap` 只报告。
