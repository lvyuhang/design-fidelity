# 设计证据格式（规范）

编写或排查取证适配器时查阅。所有设计源（蓝湖 MCP、Figma REST 等）都先转换成这一种 JSON，`prepare` 之后的场景模型、契约和门禁只读它，不读源工具的原始格式。校验：

```sh
python3 scripts/evidence_schema.py evidence/*.json      # 同一次查询的分页、同一设计的多个区域一起传
```

`prepare` 会自动执行同样的校验：`error` 进入 `issues` 阻断，`warning` 记录在 `evidence_schema_warnings`。

## 文档级字段

| 字段 | 要求 |
|---|---|
| `source` | 可选，`lanhu` / `figma`，仅用于报告 |
| `snapshot_id`、`resolved_version` | 必填。固定的源版本（蓝湖快照、Figma 文件 `version`）。不得编造；源改版后另建基线 |
| `coordinate_space` | 固定 `source_canvas`：所有坐标都是画板内的设计单位（iOS pt / CSS px） |
| `coordinate_mapping.verified` | 必须为 `true`：源坐标到画板坐标的换算已经核实（Figma 为减去画板绝对坐标） |
| `canvas` | `{width, height}`，画板尺寸 |
| `nodes` | 节点列表，见下 |
| `total_nodes` 或 `total` | 源声明的节点总数；分页合并后的唯一节点数必须等于它 |
| `ancestors` | 可选。分区域取证时，范围外的祖先节点（只需 `node_id`、`bounds`） |
| `assets` | 可导出素材：`asset_id`、`node_id`、`kind`（`exported_asset` / `render_fallback`）、`render_bounds`、`source_point`、`source_size` |
| `font_requirements` | 可选，`[{family, weights, node_count}]` |

参考图（画板整图）和素材清单（`manifest.json`：`snapshot_id`、`resolved_version`、每个素材的 `relative_path`、`bytes`、`sha256`、`actual_pixel_size`）随证据一起保存。参考图宽高必须与 `canvas` 同比例。

## 节点

| 字段 | 要求 |
|---|---|
| `node_id` | 稳定字符串 ID，跨取证不变。生成代码里的 `sourceKey`、`data-node-id` 用它 |
| `parent_id` | 父节点 ID；画板根节点为 `null` |
| `source_order` | 兄弟节点中的绘制顺序，0 在最底层 |
| `node_type` | `artboard-group`、`layer-group`、`symbol`、`shape`、`text`、`bitmap` |
| `name` | 图层名 |
| `bounds` | `{x, y, width, height}`，画板坐标，**不含**阴影、描边外扩（布局框） |
| `source_visible` / `effective_source_visible` | 隐藏图层为 `false`（含祖先隐藏） |
| `text` | 文字内容；非文字节点为 `null` |
| `text_spec` | 文字节点必填，见下 |
| `raw_style` | 样式对象，见下；没有样式时为 `{}` |
| `asset_ids` | 该节点可导出的素材 ID |

## raw_style 词汇

词汇沿用 Sketch 的字段名，这是最早接入的源；其他源的适配器负责换算成这些字段。

**图层**：`opacity` 0–100 百分比；`rotation` 角度（生成器不应用，会报 unsupported）；`isFlippedHorizontal`、`isFlippedVertical`；`hasClippingMask`（该节点是后续兄弟的蒙版）；`blendMode` 0 为正常。

**形状**：
- `points`：单位坐标（0–1，相对 `bounds`）的路径点 `{point, curveFrom, curveTo, hasCurveFrom, hasCurveTo, cornerRadius}`。矩形为四个角点 `(0,0) (1,0) (1,1) (0,1)`，椭圆为四个带曲线的边中点；
- `radius`：`[r]` 或 `[tl, tr, br, bl]`，没有 `points` 时使用；
- `isClosed`、`windingRule`（1 = even-odd）。

**填充** `fills[]`：`{isEnabled, type: 'color' | 'gradient', color, opacity 0–1, gradient}`。
- `color`：`'#RRGGBB[AA]'`、`'rgba(r,g,b,a)'` 或 `{value: '...'}`；
- `gradient`：`{type: 'linear', from: {x,y}, to: {x,y}, colorStops: [{position 0–1, color}]}`，`from`/`to` 为单位坐标。径向、角向渐变写 `gradientType` 非 0，生成器会报 unsupported；
- 图片填充写 `fillType` 非 0，并把节点作为素材导出。

**描边** `borders[]`：与填充相同的颜色字段，加 `thickness` 和 `position`（`inside` / `center` / `outside`，或 `内边框` / `中心边框` / `外边框`）。线帽、连接、虚线写在 `borderOptions: {lineCapStyle 0 butt | 1 round | 2 square, lineJoinStyle 0 miter | 1 round | 2 bevel, dashPattern: [...]}`。

**阴影** `shadow[]`（外）和 `innerShadow[]`（内）：`{isEnabled, color, offsetX, offsetY, blurRadius, spread}`。`blurRadius` 是 Sketch 语义的模糊半径；渲染时 σ = 0.5 × blurRadius。

**模糊** `blur`：`{isEnabled, radius, blurType: 0 图层模糊 | 3 背景模糊, saturation}`，σ = 0.5 × radius。

**文字**：`font.textAlignment` 为 NSTextAlignment 码（0 左、1 右、2 居中、3 两端）；`textBehaviour` 0 为自动宽度（不换行），非 0 为固定宽度（换行）。

## text_spec

```json
{"base_style": {"font_family": "PingFangSC-Regular", "font_size": 14, "font_weight": 400,
                "line_height": 20, "letter_spacing": 0, "color": "#333333"},
 "text_runs": [{"text": "¥", "font_size": 12}, {"text": "128.00"}]}
```

- 每个 run 继承 `base_style`，只写不同的字段；
- 所有 run 的 `text` 拼起来必须等于节点 `text`；
- `font_family` 用源字体名（PostScript 名或族名），`font_weight` 100–900 或名称；字体映射键为 `字体名@字重`；
- `line_height` 为绝对行高（设计单位），自动行高写 `null`（生成器会提示目视核对）；
- `decoration_line`：`underline` / `line-through`。

## 适配器的责任

- 完整取回所有节点（分页、区域合并），不能只取可见区域；
- 坐标换算到画板坐标并标记 `verified`；
- 样式完整换算；源有但这里没有对应字段的效果，在文档的 `source_gaps` 中列出 `{code, node_id, message}`，不要静默丢弃；
- 素材按原始格式导出并写入清单哈希；不能导出时标 `render_fallback`；
- 不在证据中保存 Cookie、令牌或带鉴权的 URL。
