# 准备与契约编译

按问题定位章节；日常通过 page_session 的 prepare/compile 调用，不另写逐页脚本。

## 输入与报告

prepare_page 接收完整 source_canvas 节点 JSON、干净参考图、客户端已下载资源 manifest、字体映射。检查快照/版本、完整节点数、资源字节/尺寸/哈希，生成 page-plan.json 和 summary.json。

状态：PREPARED_FOR_REVIEW 为准备成功但未审核；NEEDS_INPUT_FIXES 按 issues 处理；NOT_PREPARED 表示身份/分页/文件等不一致。计划保留节点、布局/导出/透明墨迹画框、文本 runs、effects、review_queue；候选不是批准结果。原 JSON 保存完整，按 node_id 读详情。

implementation-brief schema 2 的 visual_style_groups 保留大小元素与父填充，按相同样式去重；每个实例仍有 rect/parent_id，有源绘制范围时含 paint_rect。geometry_ref 表示尚需读取的真实路径，不能忽略或近似。文字样式在 text_style_groups。简报库存必须与源库存一致；外描边的 paint_rect 大于 layout_rect，不能把外框尺寸当填充直径。原素材仍按 export_rect 放置。

仅支持当前 MCP schema 和 Pillow 可解码位图；SVG/其他 schema 需适配。工具不下载二进制、不补字体、不批准素材语义。raw_style 缺失不能视作没有效果；同快照批量补取缺口，不逐节点往返或每轮全量抓取。

## 字体映射

项目配置一次，以源字体名@字重为键，路径相对此映射 JSON：

```json
{"fonts":{"PingFangSC-Regular@400":{"path":"assets/fonts/regular.otf","runtime_family":"SourcePingFang"}}}
```

按每个 text run 查字符和字重，不能合并不同文件的 cmap 掩盖缺字。字重缺失时键后缀 @None，需明确映射或补证据。text_run_coverage 表示 run 拼接不全。扩子集保留已交付页字符；业务文字补齐合法字体，不悄悄 fallback。runtime_family 是声明，实际加载/字重见 Flutter 适配。

## 三种画框

- layout_rect：节点约束。
- export_rect：导出 source_size/source_point 映射的资源画框，不一定等于节点框。
- alpha_ink_rect：alpha 非零像素映射范围，不等于最终叠层的感知边缘。

导出原点只从尺寸匹配的完整画布 ddsOriginFrame 求得，记录锚点 ID。缺失、冲突或越界时报告，不猜测平移/缩放。ancestor_asset_candidate 仅提示祖先资源，须查看导出是否实际包含子内容，再决定覆盖；不得据此忽略文字与效果。

## 编译 spec

通常由 `page spec`（`scripts/draft_spec.py`）生成可编译草稿，再人工复核标为 `auto:` 的检查。手写时使用 v2 字段与已审核检查，省略生成的 status/coverage/pinned_files，另列 excluded_nodes（节点 ID→具体原因）。spec/contract 同目录，输出不得覆盖已冻结文件。编译器从 blocking 检查的 node_ids 生成 coverage，计算哈希并执行文件、字体、处置与效果义务检查；未覆盖不会自动补 whole-page 或排除。

implementation_inputs 列全影响渲染的代码、测试/harness、配置和 lockfile；assets/fonts 列实际文件。工具不推断依赖图。CONTRACT_COMPILED 仅表示声明合法，尚未视觉验收。初始化器的 detector: review_required 和 pending 需审核；字段形状查 assets/visual-contract.template.json，检查设计查 visual-contract.md。

## 批量声明

同实现或同检测策略可按明确节点 ID 分组；编译后仍是逐节点检查，不能用一张大区域稀释小图标差异。分组与显式声明不可重复，保留不同状态、样式、尺寸的差异，不用分组代替语义审核。

```json
{
  "decision_groups": {
    "labels": {"node_ids":["TEXT_A","TEXT_B"], "decision":{"mode":"native_exact","implementation":"../../lib/page.dart","symbol":"Page.labels"}}
  },
  "feature_groups": {
    "labels": {"node_ids":["TEXT_A","TEXT_B"],"label":"同色文字","padding":[1,1,1,1],"detector":{"kind":"dark","luma_max":100,"min_pixels":2},"limits":{"max_center_delta":0.75,"max_size_delta":0.75}}
  }
}
```

compile 用原稿运行所有检测器；无墨迹须先查遮挡或目标层，不能等候选截图后删检查。此自检只能发现无效分割，不能证明目标层语义正确，须看对应源 ROI。业务文字或其祖先不允许默认 render_fallback；静态装饰的例外必须说明，页面热区不构成组件实现。

## 执行约束与迁移

正式契约 schema_version: 2、workflow_version: 1。node_decisions 为每个可见节点绑定实现，例如：

```json
{"node_decisions":{"SOURCE_ID":{"mode":"native_exact","implementation":"../../lib/page.dart","symbol":"PageWidget.header"}}}
```

implementation 必须在 implementation_inputs，symbol 是追踪声明而非静态绘制证明。mode：native_exact、original_asset、render_fallback、missing_asset_placeholder、excluded_with_reason。素材模式额外 asset，列入 assets/哈希表；回退必须是真实源渲染。排除模式填写 reason 并与 excluded coverage 一致；占位额外 shape: circle|rounded_rect|rect|source_path，仍需外形验证。

`source_decision_groups` 是工具根据冻结输入生成的候选和下一动作，不能改成批准清单。缺图合法性检查拒绝以下情况：文字、存在自身或祖先素材候选、非位图的路径已存在、原始样式未知、矢量几何字段未读取或子节点未查明。下载失败和渲染能力不足属于未解决项，不等于未切图。无素材的 bitmap 可仅替换图像内容（它的 points 可能只是裁剪轮廓）；无素材且源原始记录明确返回空几何的叶矢量才可占位。缺少字段不能自行补 null/[]；取证无法证实时保留诊断预览。候选仍须核实导出内容、父变换及完整路径语义；此检查不证明取证器或素材语义绝对正确。

excluded_with_reason 另需 exclusion:{kind:outside_canvas}，或 {kind:fully_occluded,by:源遮挡节点ID}；后者仅自动证明上层不透明轴对齐矩形覆盖的安全内区，不能证明的遮挡留待诊断。不得以复用、源稿未变或素材相同排除可见节点。复用检查模板并在当前完整截图执行，缺图仅排除该素材，叠在上方的状态底板/圆点/文字仍独立检查。因占位导致混色基底不同，增加绑定源节点的运行时几何、颜色、透明度和描边检查；它补充截图，不取代截图。

旧契约先保留，复制为新 spec，补源样式/处置后再编译；不能仅改版本号。历史图片用 diagnostic，不补造收据。预检输出 effect_obligations、implementation_decisions、unaccounted_visible_nodes，未知字段/证据仍需适配或定向补取。

### 素材画框自动校验

prepare 优先使用已验证 render_bounds；其次在 source_size 与 influence 宽高吻合时，以 ddsOriginFrame 和节点布局坐标换算导出框；最后才使用 source_point 与文档原点。导出像素宽高必须支持一致倍率（允许像素取整误差），否则输出 export_density_mismatch 并保留 unresolved。画布外映射仍报错，不能通过拉伸或改坐标绕过。输出 export_rect/export_density/alpha_ink_rect 供实现消费；prepare 成功只验证映射，不证明渲染器使用了它，仍需真实素材的局部画框检查。

## 新契约的默认检查

`compile` 为新契约写入 `dart_lint: "v1"`、`geometry_probe: "v1"` 和 `responsive_check`（默认 5 种机型与安全区、字体缩放 1.0/1.3，阻断项见[生成与组件化](codegen.md#几何与多尺寸门禁)，`text_overlap` 只报告）。关闭任何一项都要写 `*_reason`。没有这些字段的旧契约保持原行为，不受影响。

`node_decisions` 中 `exclusion: {kind: system_chrome}` 只对源中识别出的状态栏或 Home Indicator 节点有效，compile 会自动加入对应的 `exclude_shapes` 并注明原因。

## 缺源策略与授权

复制 `assets/pending-assets.example.json`，以 node_id 填入 `nodes`，每项包含 `reason` 和 `evidence:[{"path":"源证据.json","sha256":"实际文件哈希"}]`。错误字段直接报错，不视为无授权。存在 asset_id 时，已哈希证据须覆盖全部 ID 且均为 render_fallback；原始素材或未知类型不能据此占位。取得源数据后只需一次定向复查，确认仍无原始素材或路径、且已有用户占位授权，即可进入缺图决策。页面配置声明 `pending_assets`，由统一入口传递；不要在终端临时设置 `LANHU_PENDING_ASSETS`。

## 自定义渲染器

不使用 `lanhu_fidelity` 原语时，页面配置增加 `renderer_kind: "custom"`、`renderer_capabilities: "renderer-capabilities.json"`。能力文件形如 `{"supported":{"borders.gradient.linear":{"implementation":"文件:函数","test":"测试文件:用例"}}}`，按当前源效果去重登记；未知效果不能默认当作纯色或透明。accept/validate 会自动重跑 `scripts/renderer_capabilities.py`，缺少声明即阻断。每种新能力首次接入时，用实际绘制器测试正例和移除该效果的反例。

## 冻结与停止

`compile` / `accept` 只复用与当前 spec 及源文件重新计算结果完全一致的冻结契约，不覆盖旧文件；任何不一致都要建立新的实验基线。`stop` 必须在最后一次构建、诊断预览和报告之后执行；若停止后仍有产物修改，另列最后产物时间，按模型启动到最后响应统计完整实验。
