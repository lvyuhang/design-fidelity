# GPT-5.6 Sol high R1 视觉修正清单

## 输出

- R1 实现：`flutter_ui_components/lib/experiments/full_page_sol56_r1.dart`
- R1 冻结：`design_evidence/full-page-models/sol56-r1-frozen.dart`
- 页面类：`Sol56PlatformIntroPageR1`
- 修正轮次：1

首版文件 `flutter_ui_components/lib/experiments/full_page_sol56.dart` 与 `design_evidence/full-page-models/sol56-frozen.dart` 未修改。

## 实际输入

- 首轮固定输入：`experiment-protocol.md`、`source-part-1.json`、`source-part-2.json`、`reference-4x.png`、`asset-receipt.md`、`flutter_ui_components/pubspec.yaml`、`assets/lanhu/full_page/` 原始资源
- 自身首版源码：`flutter_ui_components/lib/experiments/full_page_sol56.dart`
- 自身首版记录：`design_evidence/full-page-models/sol56-manifest.md`
- 自身首次渲染：`design_evidence/full-page-models/sol56-4x.png`
- 自身首次热图：`design_evidence/full-page-models/sol56-heat-4x.png`
- 自身区域指标：`design_evidence/full-page-models/evaluation.json` 中的 `sol56` 数据

未读取 GPT-6 的源码、渲染、热图、manifest 或比较页实现。

## R1 前观察到的偏差

- 实时中文文字出现大面积缺字和异常字间空洞，影响跳过、两个章节标题、四项能力文案、三项收益文案与 CTA；原始图片中的顶部文字没有该问题。
- `capability_badge.png`、`reward_badge.png` 与三张收益图标包含导出透明留白，首版直接压到节点可见尺寸后，徽章和收益图标的主体明显偏小。
- 收益卡右上自绘光效形成过大的半透明圆环与十字，明显强于原稿的小型星芒。
- 状态栏时间比原稿偏粗。
- 自身首版区域误差：完整页面 MAE 4.0372；排除原始切图后的原生结构 MAE 4.2043；平台能力 MAE 5.9004；创作者收益 MAE 6.1941；底部按钮 MAE 2.3305。能力和收益区域是本轮集中修正对象。

## 本轮一次性修正

- 移除所有实时文字上的 `SourcePingFang` 强制字体，让运行平台选择完整的中文回退字体；保留蓝湖字号、字重、行高、颜色和坐标。状态栏时间字重从 600 调整为 400。
- 两枚 155 × 155 的 4× 徽章按 38.75 × 38.75 显示，并围绕原 34 × 34 节点中心对齐。
- 三枚 252 × 252 的 4× 收益图标按 63 × 63 显示，并围绕原 43 × 43 节点中心对齐，使 PNG 内部的可见主体回到设计尺寸。
- 将收益卡右上光效改为半径更小的柔光、短星芒和少量微光点，移除首版的大圆环效果。
- 保持 375 × 812 画布、所有卡片几何、原始主视觉切图、能力图标、CTA 与回调行为不变。

## 冻结声明

R1 源码经 `dart format` 后复制为冻结文件。冻结前未运行 Flutter、测试、截图或像素比较，未查看任何 R1 渲染结果，也未进行第二轮视觉修正。
