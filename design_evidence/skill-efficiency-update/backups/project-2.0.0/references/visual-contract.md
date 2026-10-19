# v2 视觉契约

从 `init_visual_contract.py` 生成项目草稿。`assets/visual-contract.template.json` 展示完整字段形状；它不是可直接验收的基线。

## 身份与范围

- `schema_version: 2`，`status: draft | ready`。
- `source_snapshot`、`source_version` 必须与全部源文档一致。
- `source_scope`：完整画板用 `{"kind":"page","expected_node_count":100}`；节点数与 MCP `total_nodes` 对照。只取部分节点用 `{"kind":"provided_nodes","reason":"只验收登录协议模块"}`，通过也会标记排除范围。
- `canvas` 是源逻辑宽高；`render_scale` 由参考图尺寸除以画布尺寸得到。不要强行固定 4×。
- `reference`、`source_documents`、`assets`、`fonts[].path` 为相对路径，全部必须列入 `pinned_files` 哈希表。
- `implementation_inputs` 列出代码、布局依赖、配置、lockfile、截图脚本；`environment` 必须有 renderer、renderer_version、platform、locale、state、text_scale。

## 覆盖清单

脚本列出可见文本、带资源 ID 的节点和有尺寸的叶节点。每个节点需要以下之一：

```json
{"status":"covered","checks":["features.title"]}
```

```json
{"status":"excluded","checks":[],"reason":"此字形已烘焙在 hero 切图中，由 hero 特征检查；不作为运行时文字"}
```

被引用检查必须存在、是 blocking，且 `node_ids` 含该节点。文本/资源节点必须由 feature 覆盖，不能用整页 MAE 替代。排除项会在报告中列出并影响总体状态。人工仍需确认语义重点；逐节点覆盖不代表检测器一定选对了可见主体。

## 检查类型

- `regions`：节点边界并集或 `rect`；RGB MAE/P95。至少一个 blocking 区域。
- `features`：`node_ids` + `padding` + `detector` + `limits`。至少一个 blocking 特征；每个特征必须有中心与尺寸阈值。
- `relations`：两个不同 feature 的原稿相对位置与实现相对位置之差，支持 center_x、center_y、left、right、top、bottom。原稿的差值不一定为 0。
- `color_samples`：节点内部 anchor（默认中心）与 size，或明确 rect。

relations/color_samples 确实不适用时，在 `not_applicable` 中写原因；不可静默留空。所有非 blocking 检查也必须有 reason，都会进入排除列表。

## 检测器与阈值

支持 dark（RGB 均值上限 luma_max）、light（均值下限 luma_min）、color_distance（rgb 和 max_distance）、channel_range（red/green/blue 范围）、gold（暖金色启发式）。这些是颜色分割，不是 OCR 或语义识别。相邻同色文字进入 ROI 会污染结果，首次必须看叠加图确认。

| 检查 | 首次校准参考值，非通用保证 |
| --- | ---: |
| 可见中心偏差 | 1 逻辑 px |
| 可见宽高偏差 | 1.5 逻辑 px |
| 图文中心线关系偏差 | 0.75–1 逻辑 px |
| 纯色 RGB 最大通道偏差 | 4–8 |
| 整页 MAE | 5–8 |

`min_pixels` 是输出图片的物理像素数，改变 DPR 时需重新审阅。MAE 范围 0–255，不能转写为还原率。先在目标环境校准字体与抗锯齿，随后冻结阈值。

## 真正的排除遮罩

```json
{"exclude_rects":[{"rect":[20,80,50,50],"reason":"动态头像区域"}],"max_excluded_fraction":0.05}
```

所有区域 MAE/P95 都排除这些像素；报告列出排除比例与每个区域实际比较像素数。超过面积预算或把一个检测区域全部遮掉都会拒绝验收。特征、关系和颜色检查保持有效，避免遮罩掩盖关键图标问题。

## 字体检查

`fonts` 每项包含 `path`、`node_ids`，TTC 可加 `font_number`。对这些节点的实际源文本检查 cmap 字符覆盖；缺少字形或任何已覆盖文本节点没有对应字体时为 NOT_EVALUATED。多字重必须分别映射至正确文件。混合字体文本应由执行者拆分节点/适配规则，不以单个字体的部分覆盖假装完成。

## 修正与解释

先修坐标/环境 → 字体 → 切图及透明边距 → 元素几何 → 组内关系 → 颜色和阴影。字体宽度超标应查字体与字重、行高、渲染器，不能第一时间压缩文字来迎合指标。每次新渲染必须重新生成收据，修改输入或契约后旧收据自动失效。
