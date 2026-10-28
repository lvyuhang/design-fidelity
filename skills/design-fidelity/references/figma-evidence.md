# Figma 取证

设计稿在 Figma 时查阅。取证结果与蓝湖相同（[证据格式](evidence-schema.md)），之后的 `prepare → generate → spec → accept` 不变。

## 为什么不用 Figma 的 Dev Mode MCP

官方 MCP 的 `get_design_context` 返回的是生成好的 React + Tailwind 代码和截图，没有原始的填充、描边位置、阴影参数、文字 run、矢量路径，无法生成源绑定的检查。这里改用 REST API 读取节点原始数据。官方 MCP 仍可用于浏览、查找节点。

## 令牌

每位研发使用自己的 Figma 个人访问令牌：Figma → Settings → Security → Personal access tokens → Generate new token，权限勾选 **File content: Read-only**（`file_content:read`），按团队规定设置有效期。令牌只放在以下任一位置，不提交、不发到聊天里：

- 环境变量 `FIGMA_TOKEN`；
- App 仓库的 `fidelity/.local.env`（已被 git 忽略）中加一行 `FIGMA_TOKEN=figd_...`。

## 命令

```sh
python3 "$SKILL/scripts/figma_evidence.py" \
  --url 'https://www.figma.com/design/<file-key>/<名称>?node-id=12-34' \
  --out fidelity/<page>/evidence
```

链接取画板（Frame）本身：在 Figma 中右键画板 → Copy link。输出 `source.json`、`reference.png`（4 倍）、`manifest.json`、`assets/`，以及原始响应 `figma-nodes.json`（审计用，不含图片链接和令牌）。第一次请求返回的文件版本会固定下来，后续图片请求都用同一版本，并记为 `resolved_version`。设计更新后重新取证即可；需要回到某个版本时加 `--version <版本 id>`。

## 换算规则

| Figma | 证据 |
|---|---|
| 画板坐标 | 减去画板 `absoluteBoundingBox` 原点，`coordinate_mapping.verified: true` |
| 带填充/描边/阴影的 Frame、Instance、Component | 拆成背景图层 + 无样式组；`clipsContent` 时背景图层作为蒙版裁切子节点，阴影单独放在背景下方（不被裁掉） |
| RECTANGLE / ELLIPSE / 单一路径 VECTOR | 原生形状（圆角、椭圆、单位坐标路径） |
| LINE（水平/垂直） | 按描边粗细换成填充矩形 |
| 设计师标记导出、图片填充、复合或纯描边矢量、≤64px 的纯矢量组 | 按 4 倍导出为素材，子节点由素材覆盖 |
| SOLID / GRADIENT_LINEAR | 纯色 / 线性渐变（`gradientHandlePositions` 前两点） |
| 描边 `strokeAlign` INSIDE/CENTER/OUTSIDE | `inside` / `center` / `outside`；线帽、连接、虚线照搬 |
| DROP_SHADOW / INNER_SHADOW | 外 / 内阴影，`radius` 即模糊半径（σ = 0.5 × 半径） |
| LAYER_BLUR / BACKGROUND_BLUR | 图层模糊 / 背景模糊 |
| TEXT | 文本、`characterStyleOverrides` 拆成 run（UTF-16 偏移）、`lineHeightPx`、`letterSpacing`、对齐；`WIDTH_AND_HEIGHT` 为自动宽度不换行，其余为固定宽度换行 |
| `isMask` | 蒙版，裁切后续兄弟节点 |
| 自动布局、约束 | 原样保存在节点的 `figma_layout`，供改写为 Flex/Row/Column 时参考 |

无法表达的内容写入 `source_gaps`，不静默丢弃：混合模式、径向/角向渐变、旋转、多个模糊、文字垂直居中、文字描边、大小写变换、段落间距、各边不同描边粗细、弧形椭圆等。

## 字体

文字 run 的字体名优先用 `fontPostScriptName`（如 `PingFangSC-Semibold`），字体映射键仍是 `字体名@字重`，与蓝湖相同。Figma 中使用 Google 字体或企业字体时，把对应字体文件放在 App 仓库之外，按 `prepare` 报告的 `font_mapping_missing` 补到 `font-map.json`。
