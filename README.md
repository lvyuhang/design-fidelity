# Lanhu → Flutter Fidelity

把蓝湖（Lanhu）或 Figma 设计稿还原为可维护的 Flutter 或 React 页面，并用可复现的门禁衡量还原度。面向 AI 编码代理（Codex、Claude Code 等），也可以由人直接使用。

| 设计源 | 取证 | | 目标 | 生成 | 渲染与门禁 |
|---|---|---|---|---|---|
| 蓝湖 | MCP | | Flutter（iOS / Android） | `.g.dart` + `design_fidelity` 包 | `flutter test` |
| Figma | REST（个人访问令牌） | | React（Web） | `.g.tsx` + `@design-fidelity/react` | Playwright Chromium |

两种设计源都转换成同一份证据格式，两种目标共用同一个场景模型、验收契约和门禁。原生 Android（Compose）与 iOS（SwiftUI）在规划中。

核心思路：**能确定的事交给工具，只把语义判断留给模型。** 视觉参数直接从设计源数据生成代码，并用经过验证的渲染原语绘制；质量由像素、节点几何和多尺寸三类门禁判定，不依赖"看起来差不多"。

## 特性

- **确定性代码生成**：从设计源节点直接生成首版，包含颜色与文字 token、导出素材、遮罩、模糊、渐变和稳定的节点 key。同一输入总是生成相同的输出。
- **已验证的渲染原语**（`design_fidelity` Dart 包与 `@design-fidelity/react`，语义一致）：内/中/外描边、不染色的外阴影与内阴影、整层透明度、背景模糊、按导出框放置素材、缺图占位。每个机制都有正反例像素测试。
- **系统 chrome 识别**：设计稿中的状态栏和 Home Indicator 只占位、不绘制，在门禁中按源坐标排除并如实披露。
- **自动验收契约**：检测器、对齐关系、效果区域和 scene 测试自动生成，契约无需手写即可编译。
- **多层门禁**：Dart / Web lint（拦截框架图标、硬编码颜色、裸阴影等）→ scene 测试 → 区域像素与特征 → 逐节点几何 → iPhone/Android 五种屏幕与安全区、1.3 倍字体检查。每次渲染都有收据，阈值冻结后不能修改。
- **可追溯的运行报告**：完整记录耗时与轮次，阻断项和观察项分开统计。

## 工作流

```text
start → prepare → generate → (组合页面) → spec → accept → finish
```

| 步骤 | 做什么 | 产物 |
|---|---|---|
| `prepare` | 固定设计快照，校验素材导出框和字体覆盖 | `page-plan.json` |
| `generate` | 生成页面首版和 scene 测试 | `<page>.g.dart` / `.g.tsx`、scene 检查、render 入口 |
| 组合页面 | 用 `overrides` 组件化并接入动态数据，用 `onTap` 接交互；不改生成文件 | 你的页面代码 |
| `spec` | 草拟可编译的验收契约 | `reviewed-spec.json` |
| `accept` | lint → 渲染 → 门禁 → 构建 | 收据、门禁报告 |
| `report` | 汇总阻断项、观察项和逐节点偏差 | `stage-report.md` |

```dart
// 页面代码只组合生成的 Scene，不手写坐标。
Widget build(BuildContext context) => CheckoutScene(
      overrides: {'<账号文字节点>': (_) => SourceText(account, style: CheckoutTokens.t14w400h20cFF22242A)},
      onTap: {'<确认按钮节点>': onConfirm},
    );
```

## 研发同学：从这里开始

**请阅读 [研发使用指南](docs/DEVELOPER_GUIDE.md)。** 只需下载 Skill 和 MCP 两个目录，按指南完成一次性配置后，每个页面的工作就是"建页面目录 → 交给 AI → 审核结果 → 提交"。

```sh
git clone --filter=blob:none --sparse https://github.com/lvyuhang/lanhu-flutter-fidelity.git ~/lanhu-flutter-fidelity
cd ~/lanhu-flutter-fidelity && git sparse-checkout set skills/design-fidelity integrations
./setup.command --profile skill                       # Skill 依赖 + 蓝湖 MCP
python3 skills/design-fidelity/scripts/install_app.py skill --target ~/.codex/skills
python3 skills/design-fidelity/scripts/install_app.py init --app /path/to/your_app \
  --python ~/lanhu-flutter-fidelity/.venv/bin/python
```

`skills/design-fidelity/` 是可安装的 Skill（当前 3.0.0 候选版），AI 代理会按 `SKILL.md` 推进流程，并根据每条命令返回的 `next_action` 决定下一步。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `skills/design-fidelity/` | Skill：脚本（取证、生成、契约、门禁）、参考文档、`design_fidelity` 原语包、render harness |
| `integrations/lanhu-mcp/` | 扩展版蓝湖 MCP 服务（MIT，保留上游出处） |
| `examples/withdraw-2/` | 离线样例：固定的设计快照、原稿与已校验素材 |
| `android-design-review/` | 安卓设计验收台：真机或模拟器截图与设计稿对照、标注、AI 分析 |
| `sketch-layerpilot/` | Sketch 插件：图层整理与切图辅助 |
| `flutter_ui_components/`、`design_evidence/`、`tools/`、`validation/` | 方法研发阶段的实验页面、取证数据与复核记录 |
| `docs/DEVELOPER_GUIDE.md` | 研发使用指南 |
| `docs/maintainers/` | 维护者资料：测试计划与用例、验证方法、测量口径、仓库布局、历史实验 |

## 维护者

维护 Skill 或工具链时才需要完整克隆，安装方法见 [完整仓库安装](docs/GETTING_STARTED.md)。

```sh
python3 -m unittest discover -s skills/design-fidelity/tests
python3 -m unittest discover -s tests
(cd skills/design-fidelity/assets/flutter/design_fidelity && flutter test)
```

验证方法与升级标准见 [测试计划](docs/maintainers/TEST_PLAN.md) 和 [测试用例](docs/maintainers/TEST_CASES.md)。3.0.0 已通过原语包和离线样例流水线验证，还没有经过独立模型在未调优页面上的泛化验证，因此仍是候选版。

## 已知限制

- 目前只支持蓝湖（Sketch 来源）数据和 Flutter；其他框架需要实现自定义渲染器能力声明。
- 生成的布局是带响应式锚定的绝对定位；会随数据变化的区域需要用 override 改写成 Row/Column。
- 只支持线性渐变；径向/角度渐变、旋转、自由路径的负 spread 会在生成报告中标为 unsupported。
- Widget test 渲染与真机、Web 渲染器之间存在字形差异，像素基线不能跨渲染器混用。
- 还原度在 Mac 测试渲染器上检查；iOS（Metal）与 Android（Vulkan/OpenGL）真机的模糊、阴影、抗锯齿可能有细微差别，上线前建议真机核对。

## 相关文档

- [研发使用指南](docs/DEVELOPER_GUIDE.md)
- [完整仓库安装（维护者 / 安卓验收台）](docs/GETTING_STARTED.md)
- [维护者资料](docs/maintainers/)

凭据、Cookie、设备数据和本机构建产物都不会入库。字体需要使用者自行提供有合法使用权的文件。
