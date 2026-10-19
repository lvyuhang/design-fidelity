# v2 视觉契约

从 `init_visual_contract.py` 生成项目草稿。`assets/visual-contract.template.json` 展示完整字段形状；它不是可直接验收的基线。

## 身份与范围

- `schema_version: 2`，`workflow_version: 1`，`status: draft | ready`；逐节点 `node_decisions` 见 [执行约束与迁移](preparation.md#执行约束与迁移29)。
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

覆盖清单必须同时包含无资源的可见叶节点和带阴影、渐变、蒙版、裁剪、模糊或透明叠层的父节点。资源 manifest 的成功数量不参与此判断。编译前 `pending`/未列出节点必须为零；不能用 whole-page region 给独立装饰或父级效果提供笼统覆盖。

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

## 小面积高显著节点与视觉效果

箭头、勾选、状态点、下划线、徽标底板等像素占比很小，整页 MAE/P95 会稀释其偏差。每个此类节点使用独立 blocking feature，配置 `profile: "small_visual"`。该配置要求单个源节点以及 center、size、edge、ink 和 mask 五类阈值，缺项返回 NOT_EVALUATED。初始化器按尺寸保守识别 shape/bitmap/symbol 小图形并强制独立检查；节点语义、分割颜色和较大装饰仍需执行者审核。

```json
{"profile":"small_visual","limits":{"max_center_delta":0.75,"max_size_delta":0.75,"max_edge_delta":0.75,"max_ink_ratio_delta":0.25,"max_mask_iou_loss":0.2}}
```

这只是阈值示例，应在查看候选结果前按参考图分辨率与渲染环境校准并冻结。`mask_iou_loss = 1 - 交集像素数/并集像素数`，在同一 ROI 的源坐标下比较颜色分割轮廓，不先对齐或膨胀掩码。0 表示轮廓相同，1 表示没有重叠；它能发现中心、尺寸和墨迹量都相同的错误路径，但受抗锯齿和颜色检测器影响。不要把包含相邻同色文字的宽 ROI 用于小图标。

阴影、发光和渐变需要在实体边缘、效果峰值、衰减中段和回到底色处取样。至少两个 blocking 采样点只能证明局部颜色，仍要保留容器边界检查并查看并列图。独立装饰节点应独立覆盖，不能假设它已包含在相邻文本或卡片特征中。

低透明数字、引号、星光和底纹等装饰即使对整页 MAE 影响很小，也必须使用局部 blocking feature。渐变至少在起点、中段和终点取样；阴影采样应覆盖实体边缘、效果峰值和衰减外沿。内外卡片底部间距、相邻模块间距等结构关系用 relation 或精确矩形特征检查。

缺图占位的源画框、圆角或圆形外形使用独立 Widget 测试或合成占位契约检查，不能与原照片做颜色分割比较。`exclude_rects` 只排除占位内部无法比较的素材像素，不排除占位周围的布局、边框、间距和相邻关系。

## 真正的排除遮罩

```json
{"exclude_rects":[{"rect":[20,80,50,50],"reason":"动态头像区域"}],"max_excluded_fraction":0.05}
```

所有区域 MAE/P95 都排除这些像素；报告列出排除比例与每个区域实际比较像素数。超过面积预算或把一个检测区域全部遮掉都会拒绝验收。特征、关系和颜色检查保持有效，避免遮罩掩盖关键图标问题。

## 字体检查

`fonts` 每项包含 `path`、`node_ids`，TTC 可加 `font_number`。对这些节点的实际源文本检查 cmap 字符覆盖；缺少字形或任何已覆盖文本节点没有对应字体时为 NOT_EVALUATED。多字重必须分别映射至正确文件。混合字体文本应由执行者拆分节点/适配规则，不以单个字体的部分覆盖假装完成。

## 修正与解释

先修坐标/环境 → 字体 → 切图及透明边距 → 叶节点缺失 → 元素几何 → 组内关系 → 颜色 → 阴影/渐变衰减。若整页指标通过但并列图仍有明显差异，将差异拆成新的叶节点或效果检查后再修，不能把“整页通过”当成停止条件。字体宽度超标应查字体与字重、行高、渲染器，不能第一时间压缩文字来迎合指标。每次新渲染必须重新生成收据，修改输入或契约后旧收据自动失效。

发现漏检时复制为新的契约修订，记录新增检查及依据，保留旧契约/旧报告。先用失败样本验证新增检查确实失败，再修复并重新渲染；不降低已有阈值。历史截图回放用 `--diagnostic`，只能报告测量结果，不能为旧截图伪造新收据或授予当前版本 PASS。

2–3 轮是效率目标，不是验收豁免。最终交付要求 coverage 无未处置节点、全部 blocking 检查通过或只有逐项披露的素材排除，并通过最终并列复查。否则结果只能标记为诊断预览。
