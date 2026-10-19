# 蓝湖 MCP 取证协议

## 调用顺序

1. 设计 ID 未知时调用 `lanhu_get_designs`，按精确名称或用户指向的画板选择 `design_id`。
2. 调用 `lanhu_get_design_overview`，传入 `design_id` 和 URL 中的版本。只有用户明确要求当前最新稿时才传 `version_id: "latest"`。
3. 保存返回的 `snapshot_id`、`resolved_version`、画布、坐标映射、参考图和节点索引。后续不得重新获取一个新快照后继续沿用旧证据。
4. 调用 `lanhu_inspect_design_region`：
   - 首选稳定 `node_ids`；需要发现节点时才使用源画布 `region`。
   - 分页读取所有与实现有关的节点，不要因为一次返回被截断就开始编码。
   - 保存原始 JSON；视觉契约从其中的 `nodes`、`ancestors` 和 `bounds` 解析 ROI。
5. 从区域检查结果中按视觉证据选择 asset ID，调用 `lanhu_export_design_assets`。优先 `format_preference: "original"`；需要 SVG 时明确请求并记录回退。
6. 读取导出 bundle 并安装到客户端项目。服务端缓存路径不能当作本地资源路径。

## 建议证据目录

```text
.design-fidelity/<design-slug>/
├── source-overview.json
├── source-region-01.json
├── source-region-02.json
├── reference-4x.png
├── assets/
├── asset-manifest.json
├── visual-contract.json
├── candidate-4x.png
└── visual-gate/
```

目录名可以调整，但原始证据与派生产物必须可区分。不要覆盖旧快照；源版本改变时创建新基线。

## 实现前检查

- `coordinate_space` 是 `source_canvas`，且 `coordinate_mapping.verified` 为 true。
- 参考图宽高与逻辑画布具有一致的缩放比。例如 375×812 对应 1500×3248，DPR 为 4。
- 分页结果中的 `snapshot_id` 和 `resolved_version` 完全一致。
- 关键节点存在 `bounds`；文本节点保留字体家族、字号、字重、行高、颜色和对齐方式。
- 资源导出无 partial failure，像素尺寸满足目标 DPR，并保存哈希或 MCP 资源清单。
- 图层名称只是标签，不用名称猜测组件语义。结构由节点关系、样式和视觉证据共同判断。

素材导出成功率不能代替节点覆盖。为每个可见清单节点记录实现处置；文本、无 `asset_id` 的位图/矢量、低透明装饰和带效果父节点同样必须进入清单。存在未处置节点时不进入完整页面编码。

overview、旧缓存或节点摘要只适合定位。以下高风险节点必须保存定向 inspect 返回的 `raw_style`、祖先和视觉裁剪：渐变、阴影、模糊、蒙版、裁剪、透明叠层、特殊字体、无 `asset_id` 位图、复杂矢量以及带视觉效果的父节点。证据文件没有这些字段时先补取，不以参考截图估算源参数。

为每个可见叶节点建立证据清单，至少记录：`node_id`、`bounds`、父级裁剪和层级、节点类型、`asset_id` 与导出结果、填充/描边、矢量路径或归一化点、线宽与端点/连接样式、透明度，以及阴影/模糊/渐变等效果字段。节点没有 `asset_id` 时继续检查其矢量与效果数据，不能直接归类为缺图或凭截图重绘。

区域分页完成后，将源节点数量与实际取回数量对照。参考图中可见但清单中没有对应叶节点时，优先检查分页遗漏、父节点烘焙内容、蒙版、低透明度效果和独立装饰层；不要在代码里补一个“看起来相似”的元素掩盖取证缺口。

## 证据与实现的边界

- MCP 节点给出源画框；参考图给出实际栅格效果。两者都需要保留。
- DDS 或生成 CSS 是布局建议，不是权威值。它和原始节点冲突时使用原始节点，并用参考图验证。
- CSS、截图识别或节点摘要可能省略阴影衰减、细下划线、蒙版和小型矢量。实现这些视觉时回到原始节点效果、层级和参考图像素，不根据组件语义自行补画。
- 动态照片、视频帧或远程内容无法固定时，固定测试夹具或在契约 exclude_rects 中登记区域、原因和面积预算；其周围的边框、间距、文字和图标仍需检测。
- 无直接资源的复杂节点先尝试源节点 `render_fallback`。仍不可取得时，定制位图、特殊装饰字体或不完整矢量按源画框占位并登记排除；任何情况都不能静默省略可见节点。
- 旧证据若只含 bounds/text，可用于历史诊断，不能作为新实现的完整输入。只要固定快照仍可 inspect，就在编码前补齐目标区域的原始样式，并升级为 v2 契约。


## 能力检查与导出资源

调用前确认工具清单实际包含快照、区域节点和原始资源导出能力；服务器名称可以不同，按能力适配。只具备旧版 HTML 分析时报告缺失能力，不伪造 snapshot_id。

导出 bundle_resource 通过客户端当前可用的 MCP 资源读取/下载方式取得，再按 manifest 安装；不同服务端版本的 URI 和封装可能不同，不硬编码服务端缓存路径。核对下载字节的 SHA-256 和尺寸后，把资源路径写入 assets、哈希写入 pinned_files。凭据、Cookie、带鉴权参数的 URL 不进入分发 Skill 或代码仓库。

完整页：根据源 total_nodes 完成分页后，source_scope.expected_node_count 对照该值。局部节点：记录 provided_nodes 范围和原因。初始化器列出的覆盖清单只来自已提供 JSON，无法发现未取回的源节点。
