# 编码前准备与契约编译

用固定工具消除逐页的数据转换代码。模型仍负责组件语义、设计歧义、效果与视觉检查；工具生成的候选关系不是审核结果。

## 1. 一次准备源数据

使用项目已有且安装了 `scripts/requirements.txt` 的 Python。源 JSON、干净参考图和已导出的资源 manifest 必须在客户端可读；不要把 MCP 服务端路径直接当成本地路径。

```sh
python "$SKILL_DIR/scripts/prepare_page.py" \
  --evidence evidence/region-1.json --evidence evidence/region-2.json \
  --reference evidence/reference.png --manifest evidence/assets/manifest.json \
  --font-map project-font-map.json --output evidence/prepared-r0
```

输出目录必须全新。stdout/`summary.json` 只提供数量、问题类别和路径；`page-plan.json` 保留节点 ID、源文本、样式摘要、资源哈希、画框、字体需求、效果与待审项。完整路径/矢量仍在原证据中，按节点定向读取。

- `PREPARED_FOR_REVIEW` / 退出 0：输入已准备，尚未实现、审核或视觉验收。
- `NEEDS_INPUT_FIXES` / 退出 2：按 `issues` 处理缺字、样式、字体映射、素材或坐标问题。可以继续实现不受影响的区域。
- `NOT_PREPARED` / 退出 2：版本、分页、哈希等不一致，不能混用这批证据。

工具支持当前 Lanhu MCP 的 `source_canvas` 节点与 PNG 等 Pillow 可解码导出资源。SVG 或另一种 MCP schema 需要适配，不能声称已自动支持。它不负责 MCP 传输、自动扩充字体、确定缺图裁剪形状或验证所有矢量变换。

### 字体映射

项目维护一次 JSON，键为源字体名与 run 字重。文件路径相对于该 JSON；不要因字体缺字改为通用 fallback 以取得通过。

```json
{
  "fonts": {
    "PingFangSC-Regular@400": {
      "path": "flutter_app/assets/fonts/PingFangSC-Regular.otf",
      "runtime_family": "SourcePingFang"
    },
    "PingFangSC-Semibold@600": {
      "path": "flutter_app/assets/fonts/PingFangSC-Semibold.otf",
      "runtime_family": "SourcePingFang"
    }
  }
}
```

`runtime_family` 记录预期 Flutter family，不证明实际使用。工具按每个 text run 检查字形，不把不同字重的 cmap 合并掩盖缺字。源字重为空时键后缀为 `@None`，需明确映射或补证据。源文本拼接不完整会报告 `text_run_coverage`。

原资源已烘焙文字、明确的替代字体或局部缺图需要审核后写进实现/契约；此准备工具不会自行批准例外。字体扩子集须保留历史字符，字体来源与替代限制继续按字体规则记录。

### 三种画框

- `layout_rect`：节点约束，不一定是图片应占的画框。
- `export_rect`：以导出 `source_size/source_point` 计算的原始资源画框，用于图片位置和尺寸。
- `alpha_ink_rect`：文件 alpha 非零像素范围映射到画布，用于透明边距检查；不等价于感知墨迹或最终叠层后的轮廓。

导出原点仅从尺寸匹配的完整画布 `ddsOriginFrame` 锚点求得，并记录锚点 ID。无锚点、冲突或映射越界均报告问题，不用小图标或猜测的截图位置推断。若一份证据混有画布坐标与设计文档坐标，针对异常节点补取/适配，不能统一平移修复。

`ancestor_asset_candidate` 只指出源层级上的资源父级。检查该导出图确实包含子层之后再决定整组覆盖；不能凭父子关系自动跳过文字、效果或缺图。

## 2. 编译声明式审核结果

初始化器仍用于发现节点与关系候选。审核后的 spec 使用 v2 契约字段，但省略 `status`、`coverage`、`pinned_files`，增加：

```json
{
  "excluded_nodes": {
    "SOURCE_NODE_ID": "原始头像未切图，采用源画框内的圆形占位"
  }
}
```

此处只是字段示例，完整 spec 还需要源身份、文件、画布、检查项、字体、环境等。每个 blocking check 的 `node_ids` 是检查所覆盖的真实节点；排除区域仍须独立声明准确的 `exclude_rects`。保留每个区域、feature、relation 和 color sample 的明确阈值。

```sh
python "$SKILL_DIR/scripts/compile_contract.py" \
  --spec evidence/reviewed-spec.json --output evidence/visual-contract-r0.json
```

spec 与输出必须位于同目录，输出不能已存在。编译器从检查项引用生成 coverage，从文件生成哈希，并运行既有契约、文件、字体校验。它不会给剩余节点分配 whole-page coverage，不提供默认视觉阈值，不自动排除缺图。

输出 `CONTRACT_COMPILED` 仅说明输入与覆盖声明合法。运行门禁并查看最终并列图后才能报告视觉结果。修改实现时复用冻结契约；发现源证据错误时保留旧基线，说明证据后另建修订，不能每轮重新编译以掩盖输入变化。

## 3. 如何量化收益

分别记录准备脚本时间、模型处理待审问题的时间和整页端到端时间。旧页回放只能证明兼容与回归，不能证明新页实现时间下降。

重点观察是否消除了逐页契约构建代码、首次渲染后的缺字、图标画框误用及字体/图片加载遗漏。独立新页实验保持模型、推理强度、证据质量和验收要求可比，记录仍需人工的异常；不要将脚本的毫秒级运行时间表述为页面生成时间。

## 执行约束与迁移（2.9）

正式 v2 契约还需 `workflow_version: 1` 和 `node_decisions`。旧契约不会自动获得新版验收；先复制为新 spec，保留冻结基线，补取源样式及处置映射，再编译。历史图片继续用 `--diagnostic`，退出 2。新要求同时由编译器、预检和独立门禁执行，绕过 runner 也不能略过。

```json
{
  "workflow_version": 1,
  "node_decisions": {
    "SOURCE_NODE_ID": {
      "mode": "native_exact",
      "implementation": "../../lib/page.dart",
      "symbol": "PageWidget.header"
    }
  }
}
```

- `implementation` 必须属于 `implementation_inputs`，`symbol` 记录实现位置；脚本检查映射完整性，不静态证明该符号实际绘制了这个节点。
- mode 支持 `native_exact`、`original_asset`、`render_fallback`、`missing_asset_placeholder`、`excluded_with_reason`。`original_asset` / `render_fallback` 素材模式需额外 `asset`，且文件列在 `assets` 和哈希表中。工具不负责生成 render fallback；必须确认 MCP 提供真实源渲染资源。
- 排除模式必须与 coverage 的 excluded 一致，填写 reason；缺图占位还需声明 `shape: circle | rounded_rect | rect | source_path`。这不替代占位外形测试。
- 当前工作流强制检查文字样式和非文字 raw_style。只有 bounds、ddsOriginFrame 或删减摘要的节点记为未知，需定向 inspect；不会视为“没有阴影”。原始 JSON 必须完整保存；脚本不能证明外部服务没有截断字段。缺口按同一快照批量 inspect/分页补齐并缓存，不逐节点调用、不每轮重复取证；未变化部分复用哈希校验。
- 小尺寸 shape/bitmap/symbol（两边不大于 96，或一边不大于 4 逻辑 px）要求单节点 `small_visual` feature。不能改挂到整页 region。该启发式偏保守，复杂照片分割仍需审核；不可用错误类别绕过。

初始化器自动生成：pending 处置清单、缺证据清单、小图形检查骨架、已支持效果的颜色采样和待审列表。小图形的 detector 保持 `review_required`，必须依据原图选择；草稿始终不可验收。采样阈值默认 6，仅供首次审核，冻结后不得迎合候选图修改。

效果采样带 `effect: {node_id, key, role}`，key 从源字段产生，例如 `shadow:0`、`fills:0:gradient`。线性渐变检查源轴 10%/50%/90%，外阴影检查实体边缘、偏移处和衰减外沿；三个采样必须独立且位于源参数推导的位置，最大采样框 4×4。缺任何一项、指向其他节点、扩大采样框或三个角色复用同一点都会拒绝验收。

这些位置是**候选点，不保证没有被子层遮挡**。首次审核需查看原图局部，确认采样确实落在可见效果上。候选点被子层遮挡时，可在同一渐变色带上或沿阴影边缘平移采样框，并在该 sample 填写 `review_reason` 记录原图中可见位置。脚本验证仍处于同一色带/衰减距离，不能只改 role 名称来重复测同一点。若越界、源梯度非线性、方向/模糊参数未知，则保留待审，使用单节点局部 region 并填写 `effect: {node_id, key}` 与 `review_reason`；局部 region 不自动覆盖相邻节点。局部 region 的有效性需用漏效果的失败样本验证，不能仅凭 review_reason 认为效果已被证明。

编译阶段也支持显式 `auto_effect_samples: {max_channel_delta: 6}`，按同一规则补齐采样。仅用于已审核该采样策略的节点；优先审核初始化器生成的草稿。已有相同源效果/角色不会重复生成，阈值不被重写。不支持的效果保留待审，不会自动排除。

预检报告追加 `effect_obligations`、`implementation_decisions` 和 `unaccounted_visible_nodes`，runner 保留 `PASS_WITH_EXCLUSIONS`。自动通过仍只是声明范围内的检查结果；旧 diagnostic、前置条件失败不能当成交付通过。
