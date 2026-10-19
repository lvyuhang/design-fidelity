# GPT-6 high 首版实现清单

## 实际读取的输入

- `experiment-protocol.md`
- `source-part-1.json`、`source-part-2.json`（节点、坐标、文本与 DDS 样式）
- `reference-4x.png`（原稿视觉参照）
- `asset-receipt.md`
- `flutter_ui_components/pubspec.yaml`
- `flutter_ui_components/assets/lanhu/full_page/` 文件清单，并查看其中 `hero.png`、`title_art.png`、`reward_1.png`

未读取既有 Dart 实现、测试、历史指标或另一模型的输出。

## 实现决策

- 以固定 375 × 812 画布和设计源坐标布置实时 Flutter 组件，背景、两组卡片、渐变、边框、阴影、分隔线及 CTA 由 Flutter 绘制。
- 标题艺术、顶部主视觉、两枚徽章、四枚能力图标及三枚收益图标使用蓝湖原始切图；页面主体没有使用完整参考图作为背景。
- 其余中文使用 `pubspec.yaml` 已登记的 `SourcePingFang` 字体，跳过和开始入驻分别暴露可选 `onSkip`、`onStart` 回调。
- 状态栏、页码、引号和收益卡星点以 Flutter 文字或图标近似。

## 资源缺口和冻结状态

- 蓝湖未单独导出状态栏图形、`01`/`02` 页码、引号、收益卡装饰星点；这些细节使用 Flutter 原生结构近似。
- 标题所需的方正字体未在 `pubspec.yaml` 注册，故直接使用登记的 `title_art.png`，没有重新排版标题文字。
- 已用 Dart SDK 的 `dart format` 格式化实现，并复制同一源码为 `gpt6-frozen.dart`。冻结前未运行 Flutter、测试、截图、像素比较，也未查看任何生成效果。
