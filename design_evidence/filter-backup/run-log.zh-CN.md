# 筛选备份 · 5.6 Sol 高保真实现运行日志

## 执行基线

- 使用 `lanhu-design-fidelity` Skill 2.5.0；固定蓝湖 snapshot `e1197e5a27c6e2ad489b2f1386fc07c4`，resolved version `653aa9f3-6fb6-4216-b3e9-06468e9ec4df`。
- MCP 完整分页读取 236 个节点；15/15 个可导出资源获取成功。画布为 375×812，验收图以 Flutter Skia 4× 渲染。
- 两张发现页照片、四个待配置任务图标没有独立资源。依照 Skill 的缺图规则保留原画框、圆角和尺寸，使用“未切图”色块；没有裁切参考图或仿画素材。

## 复查与修正

1. 首轮发现 Flutter 测试字体回退、任务标签中心偏移、筛选文字继承色不稳定。
2. 正式视觉合同复查又发现任务卡阴影、到期时间底纹、行分隔线和漏斗路径不完整。
3. 将字体固定为 SourcePingFang；坐标、渐变、阴影、底纹和分隔线按 MCP 节点参数重建；漏斗补齐闭合路径。
4. 中断后曾产生一份只检查少量项目的简化报告。该报告已作废，最终结果只采用 Skill 自带 `render_with_receipt.py` 和 `visual_fidelity_gate.py`。

## 最终验收

- 最终轮次：r8；状态 `PASS_WITH_EXCLUSIONS`；失败检查 0。
- 正式合同覆盖 193 个源节点，包含 39 个特征、6 个关系和 4 个颜色采样；排除区只覆盖确实缺失的照片/业务图标以及被弹窗完全遮挡的背景节点。
- 全页 MAE 1.7622、P95 12；弹窗主体 MAE 1.2363、P95 3；CTA MAE 2.8333、P95 1。
- Flutter 渲染测试、交互测试和 Web 构建通过。

- 正式报告：`r8/visual-gate/visual-gate-report.html`
- 可复现收据：`r8/render-receipt.json`
