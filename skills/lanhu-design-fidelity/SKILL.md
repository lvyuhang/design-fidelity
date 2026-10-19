---
name: lanhu-design-fidelity
description: Implement or repair Lanhu designs with original MCP assets, reproducible renders and visual checks, especially Flutter. Use for high-fidelity design-to-code work, not PRD-only analysis.
metadata:
  version: "2.18.6"
---

# 蓝湖高保真还原

交付可维护的界面代码、原稿对比与真实验收结果。默认只读本文件和一次[操作入口](references/session-entrypoint.md)。按工具的 `next_action` 和组件包的 `source_decision_groups` 执行；候选与阶段成功均不代表视觉通过。脚本直接运行，维护时才读源码；MCP 原数据落盘，通过 `page inspect --component` 一次读取完整组件及依赖；原始几何按节点补取，延迟展开不代表已审查。

## 关键决策

- 固定快照、版本、参考图、源逻辑画布、字体与环境，尺寸读取当前设计。overview/CSS 用于定位；样式和父效果以原始节点为准，缺证据补取。
- 原素材保留画框、透明边距与裁剪；完整通用矢量仅在绑定源 node_id 及可读取路径后精确绘制。熟悉的垃圾桶、回复、箭头等也不能凭截图仿画或换成框架图标；缺少原素材和完整路径时保形占位并提示“设计素材未切图”。仅授权的单个静态素材可源渲染回退；禁止整卡、业务文字、按钮、导航打平裁图或用近似 icon/emoji 替代。
- 几何需区分布局框、素材导出框、可见墨迹框；原图不可默认压入布局框。描边内/中/外、阴影扩散、渐变坐标与背景输入必须各自验证，见[节点决策](references/implementation-decisions.md#渲染语义验证)。
- 自定义绘制器先检查效果覆盖：节点存在不等于填充、描边、透明度、混合、模糊及父变换已实现。配置 `renderer_kind: custom` 与 `renderer_capabilities`；accept/validate 对未声明实现及测试的源效果阻断。声明不是验收证明，必须执行对应测试。小型复合控件单独检查背景与轮廓；浅色大面按顶部/中部/底部及边缘冻结空白采样，分别报告 RGB 有符号偏差，不能只用边缘窄条或大区域均值验收。
- 所有可见节点须处置，含父效果和独立装饰。先固定父框再换算子坐标；小图标、底纹、阴影/渐变、图文关系分别检查，整页误差不代替细节。
- 同一基线的名称、状态标签、计数等先恢复为复合行：保留源测量间距，主文字弹性截断，尾部控件固定；禁止分别绝对定位或把省略号预先写进动态数据。透明叠层复用时分离画布根背景，并在对比底色上验证透出，细则见[节点决策](references/implementation-decisions.md#复合行与透明叠层)。
- prepare 简报按样式去重，保留实例画框、父级、source_order、填充与效果；不能按面积省掉小色块。先处理 scene_requirements 中的背景依赖、裁剪和跨边界叠层，再填内容。按 geometry_ref 读取路径，不能从截图猜参数；复用分组声明和渲染器。
- 完整页已有规范化源场景时，先冻结实现策略并共享 source-driven 遍历；模型只能补渲染能力和修正实现，不能改成手写整页后再比较质量或效率。结构、绑定和组件存在性测试只证明机制，视觉结论必须经过相同参考图、排除规则和区域阈值的真实像素门禁。
- source-driven 仍需输入与实现审计：冻结前准备源数据并逐节点处置；实现后执行 compile、图形来源审计、能力测试与视觉验收。`CustomPaint`/`Icon(Icons.*)` 必须在 `graphics_provenance` 绑定可验证源路径或说明系统状态栏用途；未绑定即阻断。轻量案例走同一入口，只省略 Skill 研发与无关历史回归，不省略本页契约。源未读取、转换丢失、渲染器不支持均不能申报缺图；处置检查发现现成路径/素材或未查明几何时阻断，按返回动作补证据。祖先素材仅是覆盖候选，确认绑定后避免重复绘制。
- 缺图只替换内容，不替换容器、遮罩、叠层或背景效果。scene_checks 必须执行实际组件的源参数与合成行为测试；普通像素区域不能证明背景模糊，细则见[节点决策](references/implementation-decisions.md)。复用代码不免检：旧检查随本次渲染重跑，没有已验收基线就补齐。冻结源检测器；反例仅在新建/修改检查或环境变化时运行，不随每页重跑历史案例。
- 冻结 v2 契约并使用新渲染收据；不能放宽阈值、删检查或扩大排除以通过。校准保留旧记录另立关联试验；整页不能缩成局部验收，缺图逐项披露并标 PASS_WITH_EXCLUSIONS。
- 并列复查原稿/真实 Flutter 渲染，完成检查、构建与预览。preview 必须有当前代码的成功验收收据；缺失或失败用 diagnostic_preview。分别标注 Skill 版本、实现来源、验收范围；改标签不能成为新版测试，整区裁图也不证明原生组件。目标 2–3 轮，统计全任务失败/基线，校准不能归零。诊断预览只是中间产物；有可修复差异应继续处理，未完成验收不得计为同品质效率成功样本。

## 按需定位，不递归读完链接

| 当前需要 | 查阅 |
|---|---|
| 首次取证、分页或资源下载 | [MCP 取证](references/mcp-evidence.md) |
| 判断缺图、矢量、裁剪或效果 | [节点决策](references/implementation-decisions.md) |
| 字体/画框报错、编译 spec | [准备与编译](references/preparation.md)对应章节 |
| 创建检查项、排查检测误差 | [契约字段](references/visual-contract.md)对应类型 |
| 首次接入或修改截图环境 | [Flutter 适配](references/flutter-rendering.md) |
| 环境安装或其他框架 | [底层接入](references/usage.md) |
| 用户要求流程审计/性能分析 | [问题定位](references/process-gates.md)、[效率测量](references/efficient-execution.md) |
| 比较模型、提示词、流程的质量/耗时 | [公平实验](references/model-comparison.md) |
| 维护检测器或验证跨项目通用性 | [验证方法](references/validation.md) |

已有配置、字体和生产根节点直接复用；首次接入单独计时。按组件批量实施和修正，扁平图层可多选根节点；整页仍须覆盖全部节点。验收范围不随查询范围或输出预算缩小。
