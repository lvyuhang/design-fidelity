---
name: lanhu-design-fidelity
description: Implement and verify Lanhu designs as maintainable UI code, especially Flutter, with source assets and reproducible visual comparison.
metadata:
  version: "2.19.5"
  maturity: "candidate"
---

# 蓝湖到代码

2.19.5 是流程维护候选版（2.19.1 冻结基线保留）；在独立模型、未调优页面和全量成本口径验证完成前，不标记为成熟或商业可用。

默认只读本文件与 [执行入口](references/session-entrypoint.md)。先 `page start`，按返回的 `next_action` 操作；脚本直接运行，维护时才读源码。原始数据落盘，按组件读取去重后的完整证据。

## 六条交付约束

1. **固定输入**：快照、版本、逻辑画布、参考图和字体。所有可见节点及祖先效果逐项处置，不能按面积省略。未知先补取；源缺失、转换丢失、渲染不支持必须区分。
2. **素材来源**：原始导出素材或完整源矢量才可还原。缺素材用同外形同尺寸的“设计素材未切图”占位；禁止框架 icon、emoji、仿画和默认截图回填。单项回退须有用户对该项的明确授权，并写入页面配置 `pending_assets`，由统一入口传递；不得依赖临时 shell 环境。禁止自行把整卡、业务文字、按钮和导航截图打平。设计师原始导出素材中已包含的装饰文字必须随素材完整保留，不得遮白重打；先核对素材覆盖范围，再决定哪些文字另行实现。
3. **保留合成**：缺图只替换内容，容器、裁剪、透明叠层和背景效果保留。几何区分布局框/导出框/墨迹框；复合文字行保留固定间距、弹性文字和固定尾项。
4. **先验能力**：首轮前检查本页字形及实际出现的效果。绑定 node_id 不代表路径完整或效果已实现；自定义渲染器必须有能力声明和实际行为测试。完整规范化场景复用源遍历，不逐页重写整套坐标。
5. **验收顺序**：来源与覆盖 → 构建可运行 → 整页及局部视觉/行为 → 当前版本预览。统一入口产生收据；手动截图仅供诊断。不得修改阈值/排除范围换通过，缺图逐项披露为 PASS_WITH_EXCLUSIONS；受缺图影响的合成区域也需说明。
6. **成本口径**：从选页前 start 到预览后 finish，失败重试都计入。目标 2–3 轮、常规页约 10 分钟；超时说明瓶颈，不能降低质量。未取得实际 token 数据则留空。维护 Skill 与单页实验分别记录。

## 遇到问题才展开

| 需要 | 读取 |
|---|---|
| MCP 分页、版本或下载 | [取证](references/mcp-evidence.md) |
| 素材、裁剪、渐变/描边/模糊、复合行 | [节点决策](references/implementation-decisions.md)对应章节 |
| 字体、spec 或契约字段 | [准备](references/preparation.md) / [契约](references/visual-contract.md)对应章节 |
| 首次运行环境 | [Flutter 接入](references/flutter-rendering.md) |
| 连续失败或成本异常 | [定位](references/process-gates.md) / [效率](references/efficient-execution.md) |
| A/B 或维护检测器 | [公平实验](references/model-comparison.md) / [验证](references/validation.md) |

已有环境与相同哈希证据直接复用；默认不读取历史案例，不重跑无关回归。复用生产代码仍须运行本页检查。全部流程之外的手动操作不能被文案升级为正式验收。

### 源样式消费检查
准备摘要中的 `asset_coverage_candidates` 仅是覆盖候选，须查看原始导出确认；不可重复绘制已烘焙内容。自动生成的 `stroke` 与 `paint_stack` 义务必须接入现有 `scene_checks`：使用实际组件检查描边宽度、内外位置与有效透明度，以及同位置各填充层的合成结果。可合并为一个测试命令；不可用包围盒或轮廓通过代替描边和颜色通过。检查须读取实际组件输出，不能只断言抄写的常量。
