# GPT-6 R2 视觉校准

- 基线：`gpt6-r1-frozen.dart` 与固定蓝湖快照。
- 校准依据：`visual-contract.json`、R1 4× 渲染和自动门禁报告。
- 修正：恢复并补全嵌入的 PingFang 字形；撤销 R1 过度放大的章节徽章；按可见像素校准标题、能力卡和收益行；保留模型原有装饰绘制方式。
- 冻结：`gpt6-r2-frozen.dart` 在最终 R2 指标计算前复制。

