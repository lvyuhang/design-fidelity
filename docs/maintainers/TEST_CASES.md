# Skill 3.0.0 测试用例

配套 [测试计划](TEST_PLAN.md)。每条用例都写明前置条件、步骤、预期结果和要保留的证据。

- **正向用例**：证明流程能走通。
- **反向用例**（标 `NEG`）：故意注入违规，证明对应关卡会拦截。在真实 Flutter 中拦不住的反向用例，比正向用例失败更严重。
- 反向用例做完后用 `git checkout -- <文件>` 或 `git stash` 还原，再执行下一条，不要把注入的改动带进后续用例。

**判定**：PASS（与预期完全一致）、FAIL（不一致，填写实际结果）、BLOCKED（前置条件不满足，写明原因）。

**通用前置条件**：

- 分支 `fidelity-codegen-primitives`；记录 `git rev-parse HEAD`。
- macOS，Flutter 版本与 `toolchain.json` 一致，Python 3.11+ 已装 `skills/design-fidelity/scripts/requirements.txt`。
- 记 `SKILL=skills/design-fidelity`；`page` 为 `python $SKILL/scripts/page_session.py --config page.json`。

---

## A. 原语包与工具

| ID | 目的 | 步骤 | 预期结果 | 证据 |
|---|---|---|---|---|
| A-01 | Python 工具回归 | `python3 -m unittest discover -s $SKILL/tests` | 全部 OK；e2e 用例在仓库内必须执行。若有 1 项跳过，只能是 Dart 语法检查且 `dart` 不在 PATH | 终端末尾 3 行 |
| A-02 | 仓库根目录回归 | `python3 -m unittest discover -s tests` | 7 项 OK，包括版本一致性和无用户名路径 | 终端输出 |
| A-03 | 原语包静态检查 | 在 `$SKILL/assets/flutter/design_fidelity` 执行 `flutter pub get && flutter analyze` | 0 error、0 warning | 终端输出 |
| A-04 | 原语行为 | 同目录执行 `flutter test --reporter expanded` | 全部通过，用例清单与下表 A-04 子项一致 | 完整输出 |
| A-05 | 半径→sigma 只有一处 | `grep -rn "0.57735\|sigma" $SKILL/assets/flutter/design_fidelity/lib` | 只在 `effects.dart` 中定义换算，其他文件只调用 `FidelityEffectMapping` | grep 输出 |
| A-06 NEG | 原语测试有辨识力 | 把 `source_box.dart` 中 `SourceBorderPosition.inside` 分支里的 `canvas.clipPath(outline);` 改为 `break;`，再跑 A-04 | `inside border stays within the fill frame` 失败 | 失败输出 |
| A-07 NEG | 挖空测试有辨识力 | 删除 `_paintOuterShadow` 中的 `canvas.clipPath(...)`，再跑 A-04 | `is knocked out under a translucent fill` 失败 | 失败输出 |
| A-08 NEG | 整层透明度测试有辨识力 | 把 `paint()` 里的 `grouped` 恒设为 `false`，再跑 A-04 | `layer opacity composites fill and border once` 失败 | 失败输出 |

A-04 必须出现并通过的用例：

| 组 | 用例 |
|---|---|
| effect mapping | one shadow/blur conversion for every page |
| border position | inside border stays within the fill frame；center border straddles the edge；outside border keeps the full fill；dash pattern breaks the stroke |
| outer shadow | is knocked out under a translucent fill；counter-example: Flutter BoxShadow tints the interior；spread grows the casting outline；offset moves the shadow；works for free paths with spread |
| inner shadow | offset inner shadow darkens the top band only；spread inner shadow forms a ring |
| fills and layer opacity | linear gradient follows normalised from/to；layer opacity composites fill and border once；radius is clamped to half the shorter side |
| text metrics | line box equals the source line height；mixed runs keep the forced strut；ambient text styles do not leak |
| assets and placeholders | asset is placed by its export frame, not squeezed；circle placeholder keeps the source outline |
| blur | background blur smooths only inside its clip；saturation matrix is identity at 1 |
| platform fonts | each platform resolves its production family；fidelity renders always use the design family |
| structure | source keys expose node geometry；system chrome reserves source height without painting |

---

## B. 离线样例"提现-2"流水线

**前置条件**：按测试计划阶段 B 建好 `/tmp/fidelity_app` 和页面目录；`page.json` 中 `page_inputs` 指向 B-07 新建的页面文件（可先留空，B-07 再补）。

| ID | 目的 | 步骤 | 预期结果 | 证据 |
|---|---|---|---|---|
| B-01 | 计时起点 | `page start` | 生成 `run/session.json`；再次 `start` 被拒绝（不能重置计时） | 两次输出 |
| B-02 | 取证准备 | `page prepare` | `action_status: OK`，`next_action.code: GENERATE`；`page-plan.json` 的 `system_chrome` 含 statusBar 与 homeIndicator；issues 中没有 Wifi/Cellular 的 `geometry_source_unknown` | 输出、`page-plan.json` 片段 |
| B-03 | 生成首版 | `page generate` | `unsupported` 为 0，`issue_counts` 为空，`system_chrome` 为 `[statusBar, homeIndicator]`；生成 `lib/pages/withdraw_2.g.dart`、`test/withdraw_2_scene_test.g.dart`、`test/withdraw_2_test.dart`、`test/support/fidelity_render_harness.dart`，素材复制到 `assets/lanhu/withdraw_2/` | 输出、文件列表 |
| B-04 | 确定性 | 记下 `.g.dart` 的 sha256，`page generate` 再执行一次 | 哈希不变；`test/withdraw_2_test.dart` 不会被覆盖 | 两次哈希 |
| B-05 | 生成代码可编译 | 在 app 目录 `flutter analyze lib test` | 0 error | 输出 |
| B-06 | scene 义务 | `flutter test test/withdraw_2_scene_test.g.dart` | 全部通过，用例数等于 codegen 报告中 `status: bound` 的义务数 | 输出、`withdraw_2.codegen.json` 的 `scene_test` |
| B-07 | 页面组合 | 新建 `lib/pages/withdraw_page.dart`：返回 `Withdraw2Scene(onTap: {'<确认提现按钮 node_id>': onConfirm})`，把 render 测试的 `page:` 换成它；加入 `page_inputs` | `flutter analyze` 通过；lint 0 违规（`python $SKILL/scripts/dart_fidelity_lint.py --source lib --root .`） | 输出 |
| B-08 | 草拟契约 | `page spec` | `SPEC_COMPILES`，`needs_detector` 与 `unbound_obligations` 为空；`reviewed-spec.json.draft-sha256` 存在 | 输出 |
| B-09 | 编译冻结 | `page compile` | `CONTRACT_COMPILED`；契约含 `dart_lint: v1`、`geometry_probe: v1`、`responsive_check`、2 条 `system_chrome` 排除；coverage 只有 covered 和 excluded | 契约片段 |
| B-10 | 正式验收 | `page accept --note "生成首版" --build` | 执行到门禁，不出现 `NOT_EVALUATED`；产出 `render.png`、`render.png.geometry.json`、`render.png.variants.json`、`receipt.json`；收据的 `sidecars` 含两个 sidecar 的哈希 | `run/00x-accept/` 文件列表、收据片段 |
| B-11 | 运行汇总 | `page report` | 生成 `run/stage-report.md`；`blocking` 不含 `text_overlap`；每个几何失败都有节点名和偏差 | `stage-report.md` |
| B-12 | 锚定边 | 在 B-11 的几何结果中查看"修改""提现""确认提现" | 若失败，偏差描述应分别是 `right edge`、`center edge`、`center edge`，不应是 `left edge` | 报告片段 |
| B-14 | 平台适配 | 查看 `render.png.variants.json` 与 `withdraw_2.codegen.json` 的 `layout` | variants 含 iphone_se、iphone_15、iphone_15_pro_max、android_compact、android_large 各 1.0/1.3 两种；`layout.design_padding` 为 top 44 / bottom 34；确认提现按钮和文字在 `layout.footer` 中；iphone_se 变体 `scrollable: true` | 文件片段 |
| B-15 | 字体不入包 | `install_app.py fonts --app .` 后检查 `pubspec.yaml` 与 `assets/` | 苹方只在 `~/.design-fidelity/fonts/`；`pubspec.yaml` 未声明苹方；生成 token 中为 `sourceFontFamily(..., ios: SourceFonts.system ...)` | 命令输出、grep 结果 |
| B-13 | 生成首版基线 | 把 B-11 的阻断项分类、观察项、几何失败逐条填入测试计划的"生成首版基线"表，并标注初步归属 | 每个阻断项都有归属 | 填好的表 |

---

## N. 关卡反向用例（在 B 的应用上执行）

每条做完立即还原。除特别说明，"重跑"都指 `page validate`（契约未变）或 `page accept`（需要重新编译）。

| ID | 注入的违规 | 预期拦截点 | 预期结果 |
|---|---|---|---|
| N-01 | 在 `withdraw_2.g.dart` 末尾加一行注释 | lint L011 | preflight 失败，错误含 `generated_file_edited`；不进入渲染 |
| N-02 | 页面文件中加 `Icon(Icons.chevron_right)` | lint L001 | preflight 失败，指出文件和行号 |
| N-03 | 页面文件中加 `const Color(0xFF000000)` | lint L003 | 同上 |
| N-04 | override 一个节点为 `DecoratedBox(decoration: BoxDecoration(boxShadow: [BoxShadow(blurRadius: 4)]))` | lint L005 | 同上 |
| N-05 | 页面文件中加 `FittedBox(child: ...)`，并在上一行写 `// fidelity-lint: allow L009`（不写原因） | lint | 失败，提示例外必须写原因 |
| N-06 | 同 N-05，但写上原因 | lint | 通过；`page report` 的 `lint.suppressed` 列出这条例外和原因 |
| N-07 | override 卡片节点 `68382E29-…` 为 `SourceBox(fills: [...])`（去掉内描边） | scene 测试 | 渲染阶段 scene 检查失败，指出该节点的 stroke 绑定 |
| N-08 | override 标签"提现金额"为 `Padding(padding: EdgeInsets.only(top: 3), child: <原 SourceText>)` | 几何门禁（按文字段落测量） | 门禁 FAIL；该节点几何失败含 `top +3.00px` |
| N-09 | 首次 accept 后把 `reviewed-spec.json` 中任一 `max_mae` 调大，再 `page accept` | 冻结契约 | 编译拒绝：`Frozen contract differs from current spec or inputs` |
| N-10 | 首次 accept 后手工修改 `render.png.geometry.json` 中一个数值，单独运行 `visual_fidelity_gate.py`（带 `--receipt`） | 收据绑定 | `NOT_EVALUATED`，提示 sidecar 未绑定到收据 |
| N-11 | 修改 `reviewed-spec.json` 后执行 `page spec` | 草稿保护 | 被拒绝，不覆盖已人工修改的 spec |
| N-12 | 把 `Withdraw2Scene` 的某个文字 override 成带 `TextScaler.noScaling` 的组件 | lint L010 | preflight 失败 |
| N-13 | 页面文件中写一段 `Text('超长文案超长文案超长文案超长文案超长文案超长文案超长文案', softWrap: false)` 并放在 Row 中撑出屏幕 | lint L013 先拦；加有原因的例外后由多尺寸检查拦截 | 先 lint 失败；加例外后门禁 FAIL，`responsive` 报 `horizontal_overflow` 或 `exceptions` |
| N-14 | 删除 render 测试中的 `captureResponsiveVariants(...)` 调用 | 多尺寸门禁 | 门禁 FAIL，提示缺少 `render.png.variants.json` |
| N-15 | 在 render 测试的 `appBuilder` 中用 `SafeArea` 包住页面 | 多尺寸门禁 | 门禁 FAIL，报 `under_status_bar` 或几何偏移（安全区被重复扣除） |
| N-16 | render 测试中给 `captureResponsiveVariants` 传 `devices: [fidelityDefaultDevices.first]` | 机型覆盖 | 门禁 FAIL，`missing` 列出未渲染的机型 |
| N-17 | 去掉 render 测试中 `captureFidelityPage` 的 `padding:` 参数 | 节点几何 | 几何失败，节点整体 `top -44.00px` |

---

## C. 同页对照（冻结后执行）

**前置条件**：阈值已冻结并记录 Skill 提交哈希；页面 design `f19101d7-5cdc-4c36-959e-71926bb3ce2f`；模型与推理强度同 2.19.5 基线（gpt-5.6-sol，high）；独立上下文。

| ID | 目的 | 步骤 | 预期结果 / 记录 |
|---|---|---|---|
| C-01 | 冻结条件 | 记录 Skill 提交、模型、推理强度、Flutter 版本、字体文件哈希 | 与基线实验条件逐项对齐，差异写明 |
| C-02 | 独立实现 | 只给模型：冻结的 Skill、项目说明、设计入口。不提供历史实现、修复提示或旧日志 | 从模型启动到最后响应完整计时；最多 3 个正式轮次 |
| C-03 | 结果导出 | 结束后 `page report`；采集会话实测 token | 填写测试计划的结果记录模板，缺失值记 null |
| C-04 | 对照 | 与基线比较：正式验收轮次（基线 0）、终态（基线 STOPPED_NOT_ACCEPTED）、墙钟（1012.8 秒）、非缓存输入（238,662）、顶层工具调用（129） | 逐项给出差值；只作回归对照，不作泛化结论 |
| C-05 | 规则遵守 | 检查是否有手改生成文件、无原因例外、仿画图标、修改阈值 | 全部为 0 |

模型任务说明（逐字使用，不追加提示）：

> 使用 `$design-fidelity` 把蓝湖设计 `<设计链接>` 实现为 Flutter 页面，写入 `<app>` 并通过正式验收。按 Skill 的执行入口操作，最多 3 个正式验收轮次；不能通过时用 `page stop` 记录原因。

---

## D. 泛化验证（每个项目一组）

**选页要求**：3 个项目都没有参与过 Skill 调优；合起来至少覆盖列表或卡片流、表单或输入、浮层或导航；效果上至少覆盖背景模糊、渐变、遮罩、阴影中的三种；至少一页含缺素材的照片或头像。

| ID | 目的 | 步骤 | 预期结果 / 记录 |
|---|---|---|---|
| D-x-01 | 选页登记 | 记录项目、页面、design_id、快照、包含的布局与效果类型、已知缺素材 | 登记在测试开始前完成，不得事后挑页 |
| D-x-02 | 独立实现 | 同 C-02 | 同 C-02 |
| D-x-03 | 门禁终态 | `page report` | 质量必须项：PASS 或 PASS_WITH_EXCLUSIONS；几何 0 失败；无 `exceptions`、`horizontal_overflow` |
| D-x-04 | 排除合理性 | 检查契约 `exclude_shapes` 与 coverage | 只有系统 chrome 和经确认的缺图；面积不超过预算 |
| D-x-05 | 规则遵守 | 同 C-05 | 全部为 0 |
| D-x-06 | 独立复核 | 未参与实现的人对照原稿检查整页与关键细节（文字、图标、描边、阴影、缺图披露） | 无阻断性残余差异；有差异时逐项列出 |
| D-x-07 | 效率 | 记录墙钟、轮次、各轮改善量、token、工具调用、模型手写行数 | 计入中位数统计 |
| D-x-08 | 失败归属 | 对每个未通过项按测试计划的"失败归属"归类 | 每项有归属和后续动作 |

其中 x 为项目编号 1–3。

---

## 汇总与判定

| 组 | 通过条件 |
|---|---|
| A | A-01 至 A-08 全部 PASS |
| B | B-01 至 B-12、B-14、B-15 全部 PASS；B-13 完成填写（首版门禁不要求通过） |
| N | N-01 至 N-17 全部 PASS。任一反向用例未被拦截，都要先修复对应关卡，再进入 C、D |
| C | C-01 至 C-05 完成记录 |
| D | 至少 2/3 的项目 D-x-03 至 D-x-06 全部满足；效率中位数达标或有瓶颈分析 |

A、B、N 全部通过才能开始 C、D。A、B、N、D 全部满足后，才能把 Skill 升为成熟版。
