---
name: lanhu-design-fidelity
description: Implement or repair Lanhu UI designs with original MCP assets, source-node coverage, reproducible renders and visual acceptance checks. Use for high-fidelity Lanhu design-to-code work, especially Flutter. Includes a Flutter render recipe; other frameworks need their own renderer adapter. Not for PRD-only analysis.
metadata:
  version: "2.6.0"
---

# 蓝湖高保真设计还原

交付可运行页面和可重复的视觉验收。目标是减少漏图、错字、颜色与对齐错误；规则通过只代表声明范围内的检查通过，不能换算成“还原度百分比”。

## 关键约束

- 同一轮固定 MCP `snapshot_id`、`resolved_version` 和源参考图。原始节点与资源优先于生成的 CSS。
- 保留原始资源的透明画框，另外检查可见像素中心与图文关系。禁止用整页截图替代可交互页面来通过验收。
- 契约先于修正冻结；不要降低阈值、删除失败项或扩大遮罩来获得通过。确实需要变更基线时另存契约并记录证据和原因。
- 固定逻辑画布、输出倍数、字体、渲染器和页面状态。原稿只有 2× 时不伪造 4× 信息；以真实参考分辨率比较。
- 检测颜色和几何只能覆盖已配置特征。仍需看一次最终原稿/实现并列图，发现漏检时补规则。
- 编码前按 [节点实现决策](references/implementation-decisions.md) 分类：原始资源优先；完整通用矢量按源数据绘制；缺失的定制素材保形占位；下划线等独立装饰单独实现。完整性包括变换、裁剪、曲线、填充与描边，不能用近似路径代替。
- 小图标和装饰采用 `profile: small_visual`，独立检查位置、尺寸、墨迹量及轮廓重叠。阴影/渐变检查峰值与衰减；还要审核父容器效果，叶节点清单不能覆盖所有效果。检测细节见 [视觉契约](references/visual-contract.md)。

## 执行流程

首次接入或用户要求优化耗时时，先读 [高效执行](references/efficient-execution.md)。复用工具，按页面复杂度分配时间；不设统一交付分钟数，不以时间压力降低质量门槛。

1. **检查 MCP 能力并取证。** 阅读 [mcp-evidence.md](references/mcp-evidence.md)。确认连接支持快照、节点区域检查、原始资源导出。完成分页，保存源 JSON、干净参考 PNG 和资源清单，并建立叶节点证据清单。连接名称本身不代表兼容。
2. **生成待审核契约。** 用 `scripts/init_visual_contract.py` 生成 v2 草稿与建议清单。见 [运行与接入](references/usage.md)。脚本列出源文本、资源、可见叶节点和几何相邻的关系候选；这些是建议，不自动决定业务语义。
3. **完成覆盖审核。** 阅读 [visual-contract.md](references/visual-contract.md)。逐节点选择有效 blocking 检查，或写明排除原因；配置原稿区域、可见特征、对齐关系、颜色采样、环境、文件哈希、实现输入和字体映射。审核初始化器的 `effect_candidates`，补齐父容器效果；小图标启用 `small_visual`。准备完毕再把 `status` 改为 `ready`。草稿绝不能用于验收。
4. **实现和渲染。** 先按 [节点实现决策](references/implementation-decisions.md) 选择原始资源、精确矢量、保形占位或独立效果实现，关键元素保留节点映射。Flutter 用 [flutter-rendering.md](references/flutter-rendering.md)。运行 `render_with_receipt.py` 包装项目自己的截图命令，输出新 PNG 和收据。收据绑定契约、输入文件及截图哈希，防止拿旧结果验收新代码。
5. **运行门禁。** `visual_fidelity_gate.py` 同时接收契约、候选 PNG、对应收据。先检查完整性、文件和字体覆盖，再量化视觉误差。退出码：0＝通过声明的验收，1＝视觉不通过，2＝未验收/前置条件缺失。带排除项的通过标记为 `PASS_WITH_EXCLUSIONS`，必须向用户说明排除范围。
6. **定向修正。** 先修环境/字体/资源，再修几何、关系、颜色。保留 R0 和每轮独立输出目录。默认最多 3 轮，连续 2 轮无改善时报告剩余偏差。单个素材缺失仅阻塞该素材：占位并继续完成其他元素。用户要求继续时可扩展轮数。每轮先复用已固定证据定位失败 ROI，通过局部检查后再跑完整门禁；无版本变化不重复获取整页 MCP。
7. **交付结果。** 先展示最终可运行页面与原稿对比，简述验收状态、范围、关键差异和限制。再提供报告链接。运行项目适用的静态分析、交互测试和构建；视觉通过不能代替功能验证。

## 特殊情况

- 实现前用 `preflight.py --evidence` 发现 overview 缺失的原始文字样式；节点数量齐全不等于样式取证完整。渲染前用 `preflight.py --contract` 验证字体、哈希和资源。Flutter 可用 `run_flutter.py` 合并预检、渲染、门禁及可选项目检查，避免逐页复制脚本。新页面运行时加 `--require-style-evidence`；旧页面回归允许报告历史样式缺口，但不得称完整源证据验证通过。

- 旧版 v1 契约只可用 `--diagnostic` 测量；此模式始终返回 2，并标记 `NOT_EVALUATED`。没有 `--allow-fail` 验收捷径。
- 缺图处理与外形验证见 [节点实现决策](references/implementation-decisions.md)。占位默认使用 `#FFE5EA` 底色、`#FF4D6D` 描边和 `#C52245` 文案，并提供“设计素材未切图”语义标签；项目已有统一缺图样式时可使用项目样式。
- 缺失素材必须逐项写入覆盖契约的排除原因与精确 `exclude_rects`，最终状态标为 `PASS_WITH_EXCLUSIONS` 并向用户列出。不得用扩大的排除区域遮住相邻布局误差；素材补齐后移除占位和排除项，重新验收。
- 用 `exclude_rects` 排除动态照片/时间等区域，填写原因并限定面积。遮罩仅影响区域像素指标，不屏蔽特征、颜色或关系检查。`blocking: false` 不是遮罩。
- 字体 cmap 检查证明文件含所需字符，不证明运行时选择了该字重；截图脚本必须加载并使用相同文件。环境字段为调用方声明，收据不具备运行时自动探测或防伪能力。
- 只检查提供的局部节点时用 `source_scope.kind: provided_nodes` 并说明范围，不能宣称整页已验证。辅助脚本不会自动替你读取 MCP 分页。

## 自检与验证范围

使用已安装 `scripts/requirements.txt` 的同一个 Python 运行 `python -m unittest discover -s <skill-dir>/tests -v`。测试覆盖取证和收据检查，以及小图标错误轮廓、阴影/下划线消失、占位变形的故障注入。真实项目验证记录见 [validation.md](references/validation.md)。不把测试夹具结果描述为所有蓝湖页面均可自动还原。
