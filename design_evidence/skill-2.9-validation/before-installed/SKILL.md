---
name: lanhu-design-fidelity
description: Implement or repair Lanhu UI designs with original MCP assets, source-node coverage, reproducible renders and visual acceptance checks. Use for high-fidelity Lanhu design-to-code work, especially Flutter. Includes a Flutter render recipe; other frameworks need their own renderer adapter. Not for PRD-only analysis.
metadata:
  version: "2.8.0"
---

# 蓝湖高保真设计还原

交付可运行页面和可重复的视觉验收。目标是减少漏图、错字、颜色与对齐错误；规则通过只代表声明范围内的检查通过，不能换算成“还原度百分比”。

## 关键约束

先读 [流程问题定义与交付门禁](references/process-gates.md)。素材齐全、像素指标改善或达到目标轮数都不是交付条件；必须同时闭环源证据、可见节点、v2 契约和最终并列复查。

- 同一轮固定 MCP `snapshot_id`、`resolved_version` 和源参考图。原始节点与资源优先于生成的 CSS。
- 保留原始资源的透明画框，另外检查可见像素中心与图文关系。禁止用整页截图替代可交互页面来通过验收。
- 契约先于修正冻结；不要降低阈值、删除失败项或扩大遮罩来获得通过。确实需要变更基线时另存契约并记录证据和原因。
- 固定逻辑画布、输出倍数、字体、渲染器和页面状态。原稿只有 2× 时不伪造 4× 信息；以真实参考分辨率比较。
- 检测颜色和几何只能覆盖已配置特征。仍需看一次最终原稿/实现并列图，发现漏检时补规则。
- `assets x/x` 只表示资源下载结果。编码前必须让每个可见节点都有明确实现、源渲染回退、保形占位或有理由排除，且 `unaccounted_visible_nodes = 0`。
- overview、生成 CSS 或删减后的旧缓存不够描述渐变、阴影、蒙版、透明叠层和特殊字体。高风险节点必须保存定向 inspect 的 `raw_style`；证据不足时先补取，不从截图猜值。
- 编码前按 [节点实现决策](references/implementation-decisions.md) 分类：原始资源优先；完整通用矢量按源数据绘制；缺失的定制素材保形占位；下划线等独立装饰单独实现。完整性包括变换、裁剪、曲线、填充与描边，不能用近似路径代替。
- 小图标和装饰采用 `profile: small_visual`，独立检查位置、尺寸、墨迹量及轮廓重叠。阴影/渐变检查峰值与衰减；还要审核父容器效果，叶节点清单不能覆盖所有效果。检测细节见 [视觉契约](references/visual-contract.md)。

## 执行流程

首次接入或用户要求优化耗时时，先读 [高效执行](references/efficient-execution.md)。复用工具，按页面复杂度分配时间；不设统一交付分钟数，不以时间压力降低质量门槛。

1. **检查 MCP 能力并取证。** 阅读 [mcp-evidence.md](references/mcp-evidence.md)。确认连接支持快照、节点区域检查、原始资源导出。完成分页，保存源 JSON、干净参考 PNG 和资源清单，并建立可见节点处置清单。对效果、特殊字体、无资源位图和复杂矢量定向 inspect；连接名称本身不代表兼容。
2. **编码前准备。** 新页面先用 `scripts/prepare_page.py` 合并完整证据、校验原始素材、区分布局/导出/透明墨迹画框，并按文本 run 检查字体。按 [准备工具](references/preparation.md) 配置一次项目字体映射；查看摘要和问题列表，按需读节点详情。原始文件完整保留。未切图只阻塞该素材；导出坐标不明时不得退回猜测节点尺寸。该工具不会下载 MCP 二进制、自动补字体或批准节点分类。
3. **完成覆盖审核并编译契约。** 用 `init_visual_contract.py` 生成草稿，按 [visual-contract.md](references/visual-contract.md) 审核可见特征、父级效果、关系、颜色与缺图。小图标、低透明装饰和独立底纹分别建 blocking 检查。优先保存审核后的声明式 spec，用 `compile_contract.py` 自动生成 coverage 和哈希，不再写逐页 Python 构建脚本；见 [准备工具](references/preparation.md)。草稿、v1 diagnostic 和未闭环 coverage 绝不能用于当前实现验收。
4. **实现和渲染。** 按 [节点实现决策](references/implementation-decisions.md) 实现并保留节点映射。Flutter 首次接入后复用 [统一截图工具](references/flutter-rendering.md)，逐页只传 Widget、画布、倍数、素材列表与输出路径。运行 `render_with_receipt.py` 包装截图命令，输出新 PNG 和收据。收据绑定契约、输入文件及截图哈希，防止拿旧结果验收新代码。
5. **运行门禁。** `visual_fidelity_gate.py` 同时接收契约、候选 PNG、对应收据。先检查完整性、文件和字体覆盖，再量化视觉误差。退出码：0＝通过声明的验收，1＝视觉不通过，2＝未验收/前置条件缺失。带排除项的通过标记为 `PASS_WITH_EXCLUSIONS`，必须向用户说明排除范围。
6. **定向修正与轮次日志。** 先修证据缺口/漏节点/字体/资源，再修父级画框、子级关系、颜色和效果。目标为含初版在内 2–3 轮，首次通过不凑轮数。同一任务固定使用一个 `--task-log`，每次用 `--round-note` 写本轮批量修改/重试原因，保留独立输出目录。计数与日志见 [高效执行](references/efficient-execution.md#轮次日志)。第三轮仍不满足交付门禁时保持未完成并切换取证或素材策略；不得因为轮数到达而交付，不降低阈值、不换日志重置轮数。连续两轮无改善时先重新定位根因。
7. **交付结果。** 按 [交付定义](references/process-gates.md#交付定义) 检查零未处置节点、v2 blocking 状态和最终并列图。满足后展示可运行页面与原稿对比，简述验收范围和排除项，再提供报告链接。运行项目适用的静态分析、交互测试和构建；视觉通过不能代替功能验证。未满足时只能交付明确标识的诊断预览。

## 特殊情况

- 只需补取文字样式时可单独运行 `preflight.py --evidence`；完整新页用编码前准备工具同时检查素材与字体。渲染前用 `preflight.py --contract` 验证字体、哈希和资源。Flutter 可用 `run_flutter.py` 合并预检、渲染、门禁及可选项目检查。新页面加 `--require-style-evidence`；旧页回归允许报告历史样式缺口，但不得称完整源证据验证通过。

- 旧版 v1 契约只可用 `--diagnostic` 测量；此模式始终返回 2，并标记 `NOT_EVALUATED`。新实现、重新实现或当前版本修复只要仍可取得快照，就必须先生成 v2 契约。禁止使用自定义逐页 runner 绕过标准预检、收据和门禁，也没有 `--allow-fail` 验收捷径。
- 缺图处理与外形验证见 [节点实现决策](references/implementation-decisions.md)。占位默认使用 `#FFE5EA` 底色、`#FF4D6D` 描边和 `#C52245` 文案，并提供“设计素材未切图”语义标签；项目已有统一缺图样式时可使用项目样式。
- 缺失素材必须逐项写入覆盖契约的排除原因与精确 `exclude_rects`，最终状态标为 `PASS_WITH_EXCLUSIONS` 并向用户列出。不得用扩大的排除区域遮住相邻布局误差；素材补齐后移除占位和排除项，重新验收。
- 用 `exclude_rects` 排除动态照片/时间等区域，填写原因并限定面积。遮罩仅影响区域像素指标，不屏蔽特征、颜色或关系检查。`blocking: false` 不是遮罩。
- 字体 cmap 检查证明文件含所需字符，不证明运行时选择了该字重；截图脚本必须加载并使用相同文件。环境字段为调用方声明，收据不具备运行时自动探测或防伪能力。
- 只检查提供的局部节点时用 `source_scope.kind: provided_nodes` 并说明范围，不能宣称整页已验证。辅助脚本不会自动替你读取 MCP 分页。

## 自检与验证范围

使用已安装 `scripts/requirements.txt` 的同一个 Python 运行 `python -m unittest discover -s <skill-dir>/tests -v`。测试覆盖取证和收据检查，以及小图标错误轮廓、阴影/下划线消失、占位变形的故障注入。真实项目验证记录见 [validation.md](references/validation.md)。不把测试夹具结果描述为所有蓝湖页面均可自动还原。
