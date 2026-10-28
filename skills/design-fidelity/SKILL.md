---
name: design-fidelity
description: Implement and verify Lanhu designs as maintainable Flutter or React UI with deterministic codegen, verified rendering primitives and reproducible visual, geometry and multi-size gates.
metadata:
  version: "3.0.0"
  maturity: "candidate"
---

# 蓝湖到 Flutter / React

3.0.0 候选版：规则改由工具执行。尚未经独立模型在未调优页面验证，不标记为成熟。

默认只读本文件与[执行入口](references/session-entrypoint.md)。按命令返回的 `next_action` 推进，不手写本可由工具生成的内容。

目标由页面配置的 `target` 决定：`flutter`（默认，`*.g.dart`）或 `react`（`*.g.tsx`，见 [Web 接入](references/web-rendering.md)）。两者共用同一份证据、场景模型、契约和门禁。

## 分工

| 工具负责（确定性） | 你负责（语义） |
|---|---|
| 取证、素材导出框、字体覆盖（`prepare`） | 复核 issues，补取缺失证据 |
| 首版页面：token、原语、素材、遮罩、模糊、`sourceKey`（`generate`） | 用 `overrides` 组件化重复项、接动态数据；用 `onTap` 接交互 |
| 状态栏 / Home Indicator 识别为系统 chrome，只占位不绘制 | 把生成的绝对布局按需改写为 Row/Column |
| 可编译契约：检测器、关系、效果区域、scene 测试（`spec`） | 复核标为 auto 的检测器与阈值，首轮渲染前定稿 |
| 门禁：像素、节点几何、多尺寸、lint、收据（`accept`） | 按失败信息修代码，不改阈值、不扩大排除 |

## 硬约束（工具会拦截）

1. **不手改生成文件**：`*.g.dart` / `*.g.tsx` 与其 codegen 报告哈希不符即失败。要改行为就在页面代码里用 `overrides` / `onTap`，或重新 `generate`。
2. **只用原语和 token 绘制**：页面代码中的颜色字面量、`TextStyle(`、`BoxShadow`、`Border`、`ImageFilter.blur`、`Icons.*`、箭头字形、`Image.asset`、`FittedBox`、`TextScaler.noScaling` 都会被 `dart_fidelity_lint` 拦截（React 页面由 `web_fidelity_lint` 检查颜色字面量、手写字号、`box-shadow`、`border`、`blur()`、`<img>`、图标库等）。确需例外时写 `// fidelity-lint: allow Lxxx 原因`（React 为 `Wxxx`），报告会披露。
3. **缺素材只换内容**：没有原始导出时，生成器用同外形的 `SourcePlaceholder` 并保留描边、阴影、透明度和模糊。不仿画、不截图回填；单项源渲染回退须用户授权并写入 `pending_assets`。
4. **验收只认统一入口**：`accept` / `validate` 产生收据，手动截图只作诊断。阈值和排除范围在首轮渲染前冻结；系统 chrome 与缺图排除会自动标为 `PASS_WITH_EXCLUSIONS`。
5. **成本如实记录**：从 `start` 到 `finish`/`stop` 全部计时，失败重试也计入。目标 2–3 轮；未取得 token 数据就留空。

## 遇到问题再展开

| 需要 | 读取 |
|---|---|
| 生成的 Scene、overrides、改写布局、lint 规则、几何/多尺寸门禁 | [生成与组件化](references/codegen.md) |
| MCP 分页、版本或下载 | [取证](references/mcp-evidence.md) |
| 证据字段、编写或排查取证适配器 | [证据格式](references/evidence-schema.md) |
| 素材、裁剪、复合行、透明叠层、缺图 | [节点决策](references/implementation-decisions.md) |
| 字体、契约字段、检测器 | [准备](references/preparation.md) / [契约](references/visual-contract.md) |
| 首次接入 Flutter 或原语包 | [Flutter 接入](references/flutter-rendering.md) |
| 首次接入 React 或浏览器渲染 | [Web 接入](references/web-rendering.md) |
| 连续失败或成本异常 | [定位](references/process-gates.md) / [效率](references/efficient-execution.md) |
