# 日常操作

复用项目 Python（已装 scripts/requirements.txt）、页面配置和截图 harness。首次复制 assets/page-session.example.json：路径相对配置文件；test/analyze 相对 app。先填 name/run_dir 开始计时，其余路径随取证补齐；完整页 scope 为 page。

```sh
# SKILL_DIR 为技能目录；python 为项目已有环境。
page() { python "$SKILL_DIR/scripts/page_session.py" --config page.json "$@"; }
page start
page prepare
page inspect --view components
page inspect --component NODE_ID
# 整页一次读取用 --component all；扁平兄弟图层重复 --component ID 多选。
# 原始几何或异常再查：page inspect --node NODE_ID --pointer /raw_style
page phase --phase implementation
# 并列检查原稿，按组件实施；全部可见节点仍须覆盖。
# 实施页面并填写 reviewed-spec.json。
page phase --phase validation
page accept --note "初版" --build
# 有失败才批量修正并重复 validate；通过即可交付，无需凑轮数。
page phase --phase preview
# 真实并列复查与预览完成后：
page finish --note "复查结论、排除项、预览地址"
```

- 取证：定位设计后固定快照，完整分页并保存原始样式/祖先、参考图、资源及 manifest。同版本不重复全量拉取。
- prepare：固定源图与完整取证。组件包汇集文字、布局、素材、父框、效果及 scene_requirements；先处理裁剪/背景依赖再填内容，不默认批准候选。
- component：按源层级选择，自动补祖先、背景重叠及遮罩/跨边界依赖候选。它不猜业务分组；扁平图层须多选，unselected_page_inventory 未归零不能声称覆盖整页。组件完整返回，不按 8000 字符拆分。需要防护时显式 --limit；超限只给定位与大小并标 complete_packet:false，应细分源组或提高限额，不能当成已读取。
- 压缩解读：node_aliases 将短 ID 映射回源 ID（查询同时支持两者，短 ID 仅限当前 prepare，新快照重读目录）；视觉 style = visual_style_defaults 合并 overrides；素材 path = asset_base_dir / path_relative。仅合并重复表达，不舍入坐标，不删除小效果。geometry_refs 仍须查原始路径；mixed_text_runs 保留混排文字绑定。包有源文件哈希，准备后源数据变化须重新 prepare。
- inspect 旧的 text/visual/assets/scenes/effects/issues/nodes 视图用于定点排查，默认 8000 字符，可 --limit 2000–24000。大项用返回的 file/pointer 展开；续读 --cursor N --sha256 HASH，拒绝混读版本。inspections.jsonl 记录回传字符数，不冒充 token 或视觉轮次。不要为避开超限而把原始 JSON 整包回灌。
- compile：decision_groups/feature_groups 展开后仍逐节点检测，字段见 preparation.md。无墨迹检测器与业务 UI 裁图在冻结前拦截；spec/contract 同目录，省略 coverage/status/pinned_files；修代码无需重编。
- accept：首次统一执行 compile→真实截图与 scene_checks/收据→门禁→静态检查→最终构建，Flutter 固定 `--no-pub`。scene_checks 自动执行并绑定当前代码，缺失或失败不签发成功收据。不重复解析依赖、构建或截图；修代码后契约未变才用 validate，同类失败一次修完。
- finish：要求最近验证成功、收据仍有效及非空复查记录，执行者负责实际检查和预览。
- preview 同样检查成功验收与当前代码收据；未通过只能标 diagnostic_preview。未验收旧页不可作为性能/质量相当的基线。复用旧检查仍须随本次渲染执行，不另造仅验增量却声称整页通过的脚本。
- 日常运行当前页面的源数据自检与真实渲染检查；仅新增/修改检测器、或 SDK/字体/渲染器变化影响检测时，运行相关反例回归。历史案例、Skill 全套测试不随每张页面重读/重跑。

start 固定 Python 供子命令复用。phase 只在阶段切换调用，可标 infrastructure；墙钟含编辑/等待，不是模型计算时间。普通页面不扩建通用工具。

同文件哈希、pointer、游标的重复 inspect 默认只回传已读取提示；上下文丢失时用 --refresh，源文件变化自动重新读取。已读取不代表已复核。分页控制单次峰值，不承诺减少累计 token；避免为分页而逐段全量搬运无关数据。

stdout 回传全任务轮次、阶段时间和失败摘要；完整输出在 session/各轮报告。run.json 汇总跨基线轮次，改名 task-run 不能归零。status 查进展，调试才 --verbose；token 未采集记 null。start 不可重置，中断锁先确认进程结束。--build 在门禁通过后执行，不为构建重复渲染。

## 按工具结果继续（2.18.6）

命令提供 `next_action` 时，先完成它所指阶段；它导航现有流程，不批准候选或推断根因。inspect 返回组件证据后，按候选逐项核实并实现。缺报告先读取报告，不凭成功退出码宣告交付。组件包的 `source_decision_groups` 按同类来源批量给出待办，保留全部实例；路径必须展开核实，工具不替代语义审核。

- `NEEDS_INPUT_FIXES`：批量补取 issues 指向的证据/字体/资源，再 prepare；不要开始猜图形。
- `PREPARED_FOR_REVIEW`：inspect 组件及依赖，确认画框、效果和来源后实现；不是已验收。
- `MISSING_SOURCE_NOT_ESTABLISHED`：按 node_id 和 next_action 查源；不能用一句缺图理由消除矛盾，不能手动补空 points。
- `NOT_EVALUATED`：先修报告指出的输入、契约或环境问题；没有有效视觉分数时，不盲调 UI。
- 真实视觉 `FAIL`：对源信息→转换→组件消费→检测器逐层定位，同一原因批量修复后 validate；参数证据不变则不重取整页。保留阈值和排除范围。连续无改善时换定位方法；2–3 轮是目标，不是成功标准。
- 验收成功后复查并列渲染再 finish。执行失败、未收敛或缺资料时保留诊断状态及具体剩余项。模型实验沿用冻结的轮数上限，不擅自切换模型。

## 自定义绘制器的效果覆盖

页面配置增加 `renderer_kind: "custom"`、`renderer_capabilities: "renderer-capabilities.json"`。实现前运行 `scripts/renderer_capabilities.py --evidence <源分页> --capabilities <能力文件> --output <报告>`（多页重复 evidence）。accept/validate 自动重跑，缺少能力文件或未处理效果即阻断；标准 Widget 页面不强制该适配器检查。

能力文件：`{"supported":{"borders.gradient.linear":{"implementation":"文件:函数","test":"测试文件:用例"}}}`。按当前源效果去重登记，不写页面特例；未知效果不可默认当纯色/透明。此检查核对声明，不执行测试，也不替代视觉收据。原素材自带的效果需记录烘焙边界，避免重复叠加透明度。

每种新绘制能力首次接入时，用实际绘制器测试正例及移除该效果的反例；小控件分别测背景/描边的非文字像素与整体合成。固定输入、阈值及测试区域后再修实现；整页均值容易稀释细描边，局部诊断仍不能冒充整页通过。历史原始输出保留，修复后的耗时不回填旧基准。
