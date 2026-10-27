# Skill 3.0.0 测试说明与评估标准

本文说明如何验证 `fidelity-codegen-primitives` 分支（Skill 3.0.0 候选），以及什么结果可以把它从候选版升为成熟版。阈值和判定规则必须在开始阶段 C、D 之前冻结，测试过程中不得修改；中途改了 Skill，就另起版本号重新计数。

## 0. 已验证与未验证

| 范围 | 状态 |
|---|---|
| Python 工具：codegen、lint、几何/多尺寸门禁、spec 草拟、系统 chrome（251 项单测） | 已在 Linux 云环境通过 |
| 离线样例"提现-2"从快照走到冻结契约（`test_pipeline_e2e.py`） | 已通过，无需手工编辑 |
| 生成的 Dart 文件 | 只通过语法检查 |
| `lanhu_fidelity` 原语包、harness、scene 测试、render 测试 | **未编译、未运行**（云环境无法安装 Flutter） |
| 真实渲染、像素门禁、模型端到端 | **未执行** |

所以第一步必须在装有 `toolchain.json` 固定版本 Flutter（3.47.7）的 macOS 上完成阶段 A、B。

## 阶段 A：原语包（约 5 分钟）

```sh
git fetch origin fidelity-codegen-primitives && git checkout fidelity-codegen-primitives
python3 -m unittest discover -s skills/lanhu-design-fidelity/tests      # 预期 251 项 OK（e2e 在仓库内运行）
python3 -m unittest discover -s tests                                   # 预期 7 项 OK
cd skills/lanhu-design-fidelity/assets/flutter/lanhu_fidelity
flutter pub get && flutter analyze && flutter test
```

**通过标准**：`flutter analyze` 无 error；`primitives_test.dart` 全部通过，其中反例用例（BoxShadow 会染色内部、去掉模糊后条纹不变等）也必须按预期断言。

**失败时的处理**：

| 现象 | 处理 |
|---|---|
| 编译错误 | 修 Dart 代码；不要改测试来迁就 |
| 阴影衰减或模糊用例失败 | 只调整 `lib/src/effects.dart` 中 `LanhuEffectMapping` 的系数，记录调整前后数值和依据 |
| 描边位置、挖空、opacity 合成用例失败 | 属于原语实现缺陷，修 `source_box.dart`；这些用例是语义断言，不能放宽 |

## 阶段 B：离线样例真实渲染（约 15 分钟）

目的是验证生成代码、scene 测试、render 测试和门禁能在真实 Flutter 中串起来，不涉及模型。

1. 准备字体：`PYTHONPATH=.tools/fonttools python3 tools/prepare_fonts.py`（生成到 `flutter_ui_components/assets/fonts/`）。
2. 新建验证应用并接入原语包：

   ```sh
   flutter create --empty /tmp/fidelity_app
   mkdir -p /tmp/fidelity_app/packages /tmp/fidelity_app/assets/fonts
   cp -R skills/lanhu-design-fidelity/assets/flutter/lanhu_fidelity /tmp/fidelity_app/packages/
   cp flutter_ui_components/assets/fonts/PingFangSC-{Regular,Medium,Semibold}.otf /tmp/fidelity_app/assets/fonts/
   ```

   在 `/tmp/fidelity_app/pubspec.yaml` 中加入 `lanhu_fidelity: {path: packages/lanhu_fidelity}`、`assets: [assets/lanhu/withdraw_2/]`，以及 family `SourcePingFang`（400/500/600 三个字重，写法同 `flutter_ui_components/pubspec.yaml`）。

3. 准备页面目录：复制 `examples/withdraw-2/` 的 `source.json`、`reference.png`、`asset-manifest.json`、`assets/`，新建 `font-map.json`：

   ```json
   {"fonts": {
     "PingFangSC-Regular@400": {"path": "/tmp/fidelity_app/assets/fonts/PingFangSC-Regular.otf", "runtime_family": "SourcePingFang"},
     "PingFangSC-Semibold@600": {"path": "/tmp/fidelity_app/assets/fonts/PingFangSC-Semibold.otf", "runtime_family": "SourcePingFang"},
     ".AppleSystemUIFont@400": {"path": "/tmp/fidelity_app/assets/fonts/PingFangSC-Regular.otf", "runtime_family": "SourcePingFang"}
   }}
   ```

   页面配置 `page.json` 以 `skills/lanhu-design-fidelity/assets/page-session.example.json` 为模板：`app` 指向 `/tmp/fidelity_app`，`generated` 为 `lib/pages/withdraw_2.g.dart`，`class_name` 为 `Withdraw2`，`test` 为 `test/withdraw_2_test.dart`，删除 `pending_assets` 和 `page_inputs`。

4. 运行：`page start → prepare → generate → spec → accept --build`（命令见 Skill 的 `references/session-entrypoint.md`）。prepare 若报缺字形，用 `tools/prepare_fonts.py` 扩充字符或改用完整字体后重跑。

**通过标准**：

| 检查 | 期望 |
|---|---|
| prepare | `PREPARED_FOR_REVIEW`，状态栏和 Home Indicator 不产生 issue |
| generate | `unsupported` 为 0，scene 义务全部 bound |
| `flutter test test/withdraw_2_scene_test.g.dart` | 全部通过 |
| accept | 执行到门禁，不出现 `NOT_EVALUATED`；生成 `render.png.geometry.json` 和 `render.png.variants.json` |
| 门禁结果 | 记录即可，不要求通过。生成首版的失败项就是阶段 C 要观察的"首轮质量" |

阶段 B 失败通常是接入问题（字体声明、asset 路径、import），修正后记录在本文末尾的问题清单中，再进入阶段 C。

## 阶段 C：同页对照（与 2.19.5 基线比较）

使用 2.19.5 独立重跑的同一页面（design `f19101d7-5cdc-4c36-959e-71926bb3ce2f`，快照 `2369ff10…`），条件与 `validation/retest-2195-sol56/experiment.md` 保持一致：同一模型与推理强度、独立上下文、不提供历史实现、最多 3 个正式轮次、从模型启动到最后响应完整计时、token 只用实测值。

这是回归对照，不是泛化证据。基线结果为：正式验收 0 轮、STOPPED_NOT_ACCEPTED、1012.8 秒、非缓存输入 238,662、缓存输入 18,942,848、输出 52,936、顶层工具调用 129。

## 阶段 D：泛化验证（决定是否升为成熟版）

按 `skills/lanhu-design-fidelity/references/validation.md` 执行：至少 3 个未参与调优的业务项目，各选 1 页，覆盖不同的布局（列表、表单、卡片流）和效果（模糊、渐变、遮罩、阴影）。实现者使用独立上下文，只拿到冻结的 Skill、项目说明和设计入口；由未参与实现的复核者对照原稿检查完整页与关键细节。失败样本和未完成样本一律保留。

## 评估标准

每页记录下表全部字段，缺失的实测值记 null，不估算。

### 质量（必须项）

| 指标 | 来源 | 合格线 |
|---|---|---|
| 门禁终态 | `run.json` | `PASS` 或 `PASS_WITH_EXCLUSIONS` |
| 排除项 | 契约 `exclude_shapes`、coverage | 只允许系统 chrome 和经确认的缺图；排除面积 ≤ 契约预算 |
| 节点几何 | 门禁 `geometry` | 最终 0 失败 |
| 多尺寸 | 门禁 `responsive` | 无 `exceptions` 与 `horizontal_overflow`；`text_overlap` 数量单独记录 |
| 独立复核 | 复核记录 | 无阻断性残余差异 |

### 规则遵守（必须项）

| 指标 | 合格线 |
|---|---|
| 手改生成文件（L011） | 0 |
| 未写原因的 lint 例外 | 0；有原因的例外全部列出，由复核者判断是否合理 |
| 仿画图标、框架图标、截图回填 | 0 |
| 修改阈值或扩大排除以换取通过 | 0（对照 spec 首轮渲染前后的哈希） |

### 效率（与基线比较）

| 指标 | 记录方式 | 目标 |
|---|---|---|
| 端到端墙钟 | 模型启动到最后响应 | 中位数 ≤ 15 分钟（长期目标 10 分钟） |
| 正式轮次 | `task-run.json` | ≤ 3；记录首轮、末轮与每轮改善量 |
| 非缓存输入 token | 会话实测 | 中位数 ≤ 基线的 50%（≤ 119,000） |
| 输出 token、顶层工具调用 | 会话实测 | 记录，与基线对比 |
| 模型手写代码量 | 页面文件与 override 的行数 | 记录；用来观察生成器承担的比例 |

### 生产可用性（观察项，不作为本轮门槛）

- 1.3 倍字体下的 `text_overlap` 数量，以及改写为 Row/Column 的区域数。
- override 是否把重复项抽成了组件、是否接了动态数据和交互。

### 升级判定

满足以下全部条件，才把 Skill 标为成熟：

1. 阶段 A、B 通过。
2. 阶段 D 中至少 2/3 的页面在 3 轮内满足全部质量必须项和规则必须项，且失败页的原因已按下文归属并有修复计划。
3. 效率指标中位数达到目标，或未达标但有明确瓶颈分析。
4. 任何 Skill 修改都没有发生在冻结测试批次的中途。

只有阶段 C 改善不足以升级；同一页面反复调优后的通过率不能代表跨项目能力。

## 失败归属

| 现象 | 归属 | 处理 |
|---|---|---|
| prepare 缺字段或解析异常 | MCP / 取证适配 | 修 `integrations/lanhu-mcp` 或 prepare |
| 生成器标为 unsupported，或生成代码与源参数不符 | 生成器 | 修 `generate_flutter.py`，并加最小合成反例 |
| 原语像素行为与原稿不符 | 原语包 | 修原语或 `LanhuEffectMapping`，并加正反例测试 |
| 门禁漏检或误报 | 门禁 | 先保留旧基线，用失败样本校准检查，再修实现 |
| 模型违反规则但 lint 未拦截 | lint | 新增规则及对应反例 |
| 模型语义错误（分组、交互、数据） | 模型或 Skill 说明 | 记录具体案例；只有跨页面可复现的问题才改 Skill |
| 项目字体、画布、资源约定不同 | 项目配置 | 写入页面配置，不扩充 Skill 默认规则 |

## 结果记录模板

| 字段 | 值 |
|---|---|
| 页面 / design_id / 快照 | |
| Skill 提交 / 模型 / 推理强度 | |
| 门禁终态 / 排除项 | |
| 几何失败（首轮 → 末轮） | |
| 像素与特征失败（首轮 → 末轮） | |
| 多尺寸：exceptions / overflow / text_overlap | |
| lint 例外（含原因） / L011 | |
| 正式轮次 / 端到端墙钟 | |
| 非缓存输入 / 缓存输入 / 输出 token | |
| 顶层工具调用 | |
| 模型手写行数 / override 数量 | |
| 独立复核结论 | |
| 失败归属与后续 | |

## 问题清单

（阶段 A、B 中发现的接入问题记在这里，附修复提交。）
