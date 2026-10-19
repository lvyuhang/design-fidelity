# GPT-5.6 Sol high 首版实现清单

## 输出

- 实现文件：`flutter_ui_components/lib/experiments/full_page_sol56.dart`
- 冻结文件：`design_evidence/full-page-models/sol56-frozen.dart`
- 页面类：`Sol56PlatformIntroPage`
- 逻辑画布：375 × 812
- 交互入口：可选 `VoidCallback onSkip`、`VoidCallback onStart`

## 实际读取输入

- `design_evidence/full-page-models/experiment-protocol.md`
- `design_evidence/full-page-models/source-part-1.json`
- `design_evidence/full-page-models/source-part-2.json`
- `design_evidence/full-page-models/reference-4x.png`
- `design_evidence/full-page-models/asset-receipt.md`
- `flutter_ui_components/pubspec.yaml`
- `flutter_ui_components/assets/lanhu/full_page/` 的文件清单；其中直接查看了 `hero.png`、`title_art.png`、`capability_badge.png`、`reward_badge.png`，其余图标资源依据蓝湖节点边界和资源收据接入：`capability_1.png` 至 `capability_4.png`、`reward_1.png` 至 `reward_3.png`

未读取 `flutter_ui_components/lib` 下的既有 Dart 实现、测试、历史指标或另一模型输出。

## 实现决策

- 使用 `Material`、固定尺寸 `SizedBox`、`ClipRect` 和绝对定位 `Stack` 保持蓝湖 375 × 812 源坐标，不引入响应式缩放或安全区偏移。
- 顶部主视觉、标题文字组、两枚章节徽章、四枚能力图标和三枚收益图标直接使用蓝湖原始 PNG；所有资源按蓝湖逻辑边界缩放。
- 两张章节外卡、四张能力卡、收益内卡、分隔线、CTA、文字、阴影、描边和渐变均使用实时 Flutter 组件构建。
- 页面正文统一使用 `pubspec.yaml` 已登记的 `SourcePingFang`，按 DDS 的字号、字重、行高和颜色设置。
- 状态栏图标用 `CustomPainter` 绘制；跳过入口保留更大的透明点击区，显示文字仍对齐设计位置。
- 收益卡右上装饰光点使用轻量 `CustomPainter` 近似；章节编号和引号使用低透明度实时文字。
- CTA 与跳过入口使用 `InkWell`，分别调用可选的 `onStart` 与 `onSkip`。

## 资源缺口与近似

- 设计声明的 `FZDBSJW--GB1-0`、`Alibaba-PuHuiTi-R` 和 iOS 系统字体未在 `pubspec.yaml` 登记。顶部对应文字已包含在蓝湖导出的 `title_art.png` 中；状态栏时间改用 `SourcePingFang`。
- 蓝湖未提供 iOS 状态栏图标切图，信号、Wi-Fi 与电池为 Flutter 画布近似。
- 收益外卡右上角位图光效没有独立可用切图，使用渐变与少量绘制光点近似。
- `reference.png` 存在于资源目录但未作为页面组成部分使用。

## 冻结声明

实现源码经 `dart format` 后复制为冻结文件。冻结前未运行 Flutter、测试、截图或像素比较，也未查看任何生成页面效果；未依据渲染结果进行视觉修正。
