# GPT-6 high R1 视觉修正清单

## 本轮实际输入

- 首版证据：`reference-4x.png`，以及上一轮已读取的 `experiment-protocol.md`、`source-part-1.json`、`source-part-2.json`、`asset-receipt.md`、`flutter_ui_components/pubspec.yaml` 和蓝湖原始切图。
- 本轮反馈：自己的 `gpt6-4x.png`、`gpt6-heat-4x.png`、`evaluation.json`。
- 自己的首版源码 `flutter_ui_components/lib/experiments/full_page_gpt6.dart` 和 `gpt6-manifest.md`。

未读取 GPT-5.6 的源码、渲染、热图或 manifest，也未读取比较页实现。

## 观察到的偏差

- 首版多处中文缺字或显示空白，影响能力标题、说明、收益文案、跳过和 CTA；材料图标及装饰性引号、页码在首版渲染中出现方框或异常形状。
- 徽章及三枚收益图标的可见图案比原稿小；原始 PNG 有透明边距，按节点外框直接绘制缩小了可见内容。
- 自身首版区域误差为：整页 RGB MAE 4.4477，能力区 6.134，收益区 6.618；热图在文字、收益图标及装饰元素处最集中。

## 一次集中修正

- 新建 `Gpt6PlatformIntroPageR1`，保留原页面结构和跳过、开始入驻回调；中文改用系统字体回退，以覆盖首版缺失的字形。
- 依照切图透明边距，扩大两枚徽章和三枚收益图标的绘制尺寸，同时保持可见图案中心在原节点位置。
- 将状态栏信号与 Wi-Fi、引号及收益卡星点改为 Flutter `CustomPainter` 绘制；页码改用系统字体斜体，避免首版的异常字形。
- 使用 Dart SDK 的 `dart format` 格式化后，复制完全相同源码为 `gpt6-r1-frozen.dart`。原 `full_page_gpt6.dart` 与 `gpt6-frozen.dart` 未修改。

冻结前未运行 Flutter、测试、截图或像素比较，也未查看 R1 修正后的渲染结果。
