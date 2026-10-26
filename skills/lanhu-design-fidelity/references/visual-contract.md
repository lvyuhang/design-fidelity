# v2 契约字段与检测

创建检查项或定位门禁误差时按章节读；完整字段形状见 assets/visual-contract.template.json。初始化器生成草稿，正式输出由 compile_contract 生成。

## 身份与覆盖

schema_version: 2、workflow_version: 1、status: ready；source_snapshot/version 与源文件一致。source_scope 完整页为 {kind: page, expected_node_count: 源总数}；局部为 {kind: provided_nodes, reason: 明确范围}。

canvas 为源逻辑尺寸，render_scale 为参考图/画布比例。reference/source_documents/assets/fonts.path 相对契约目录，列入 pinned_files。environment 声明 renderer/version/platform/locale/state/text_scale；实现处置与输入列表见 preparation.md。

coverage 对每个可见叶节点及带视觉效果父节点记录 covered + checks，或 excluded + reason。所引检查必须 blocking 且 node_ids 包含本节点；文本/资源需 feature，不能用 whole-page region 顶替。非 blocking 检查要写 reason。符号映射、coverage 存在不证明语义正确。

## 检查类型

| 类型 | 关键字段 |
|---|---|
| regions | rect 优先，否则取 node_ids 边界并集；max_mae/max_p95；至少一个 blocking |
| features | node_ids、padding、detector、limits；至少一个 blocking；必须有中心/尺寸阈值 |
| relations | 两个 features、metric: center_x/center_y/left/right/top/bottom、max_delta |
| color_samples | node_ids、anchor（默认中心）、size，或明确 rect；max_channel_delta |

relations/colors 确不适用时在 not_applicable 写原因。关系比较相对原稿的差值，不要求原稿本身居中。regions 的 node_ids 绑定覆盖，不覆盖显式 rect；检查实际 ROI/compared_pixels，防止小缺陷被整卡平均稀释。

## 特征分割

detector 支持 dark(luma_max)、light(luma_min)、color_distance(rgb/max_distance)、channel_range(red/green/blue)、gold；min_pixels 按输出物理像素。首次检查叠加图，防止相邻同色文字污染 ROI。不是 OCR，阈值须依据参考分辨率/抗锯齿校准后冻结。

常用首次参考值：max_center_delta 1、max_size_delta 1.5、关系 max_delta 0.75–1 逻辑 px；纯色通道差 4–8，整页 MAE 5–8。不是通用保证，也不能换算还原率。

小 shape/bitmap/symbol（两边≤96 或一边≤4 逻辑 px）需独立单节点 profile: small_visual，包含 max_center_delta/max_size_delta/max_edge_delta/max_ink_ratio_delta/max_mask_iou_loss；不能归错类型绕过。IoU loss=1−交集/并集，不先对齐/膨胀，能发现 bbox 相同但路径不同。低透明数字/引号/星光等独立装饰同样单独覆盖。

## 效果采样

效果义务来自源字段，不只叶节点。sample 标明 effect: {node_id,key,role}，key 如 shadow:0、fills:0:gradient。初始化器生成候选：线性渐变沿源轴 10%/50%/90%；外阴影实体边缘、偏移处、衰减外沿。三个角色独立，采样框≤4×4。检测父子间距另用 relation/几何 feature。

候选可能被子层遮挡：先看原图局部，允许沿同一渐变色带/阴影边缘平移并写 review_reason；脚本仍检查色带/衰减距离，不能改 role 重复同一点。越界、非线性或参数未知时保留待审，可用单节点局部 region + effect:{node_id,key} + review_reason；须用漏效果反例验证，说明文字不等于检测有效。

源路径完整的细描边在 4× 截图中可能仅因渲染器抗锯齿或虚线相位产生高 P95，而 1× 结果等价。此类单节点 border 局部 region 可明确写 `comparison_profile: vector_effect` 和 `review_reason`：检查器先还原最终逻辑尺寸并低通，再比较局部 MAE/P95；缺失、偏移、粗细或轮廓错误仍须由反例测试失败。不得用于文字、位图、阴影或整页区域，也不得用来掩盖真实几何偏差。

编译 spec 可显式 auto_effect_samples:{max_channel_delta:6}，仅对已审核策略补齐；不重写已有阈值，未知效果不自动排除。检测器/效果采样须结合原图复查，不能只看整页平均值。

## 排除与字体

评分器支持 `exclude_shapes`：每项含 `shape: rect|ellipse|polygon`、`reason`，rect/ellipse 用 `rect:[x,y,w,h]`，polygon 用源画布坐标 `points:[[x,y],...]`。可选 `inset` 按逻辑像素向内收缩，保留边界计分；复杂源曲线须先按源变换离散化，不能拿矩形替代。旧 `exclude_rects` 保持兼容。

`protect_regions` 使用同一形状格式，填写前景状态点、边框等源区域与 reason；在所有排除区合并后恢复计分，避免另一个排除区再次吞掉前景。范围必须由源与冻结契约确定，不从候选截图反推。缺素材审核时同时声明排除轮廓和重叠前景，不能只填写照片矩形。max_excluded_fraction 按最终像素掩码计算；遮罩只影响 region 指标，不屏蔽 feature/relation/color；遮满检查区域拒绝。新增/修改规则时执行状态点破坏反例，普通页面无需重跑历史全套。

fonts 每项有 path、node_ids，TTC 可加 font_number；对实际文本查 cmap，多字重各自映射。混合字体需拆分/适配，不以单字体部分覆盖冒充完成。字体宽度错误先查加载/字重/行高/渲染器，不缩放文字迎合指标。

新代码/契约需新收据。发现漏检先保留旧基线、用失败样本校准新检查，再修实现；历史 diagnostic 不授予当前验收。

## scene_checks

仅当源有背景模糊、mask、跨裁剪边界叠层，或缺图节点仍有源效果时触发。brief 的 scene_requirements 按 kind 去重，instances 给出必需 ID；缺图自身效果还要求 `node_id/placeholder_effect/effect_key`。`excluded_with_reason` 仅能以可证明不可见豁免，不能以缺图、复用、源稿未变化豁免。

```json
"scene_checks": {
  "surfaces": {
    "obligations": ["NODE/backdrop", "MASK/clip", "ASSET/boundary/MASK"],
    "test_file": "app/tests/scene_probe.dart",
    "cwd": "app",
    "command": ["flutter", "test", "--no-pub", "tests/scene_probe.dart"],
    "timeout_seconds": 60,
    "assertions": "测试生产组件：源 alpha/模糊单位映射；条纹背景衰减与裁剪范围；原底片画框、叠层和轮廓"
  }
}
```

cwd 相对 **contract 所在目录**，省略为该目录；命令使用 argv 无 shell。`test_file` 相对 contract 且须在 implementation_inputs，生产源码及测试配置也须列入；源证据由 pinned_files 固定。同类 obligation 合入一个命令，默认不另增整页截图。渲染器之后执行测试，任一失败不生成成功收据；门禁要求匹配本次 contract/输入 hash 的执行结果，不能以手写 `passed` 字段通过。

这证明测试确实执行，不自动证明断言质量。新建检查时必须做相关删减反例验证（去掉 blur、改不透明、去掉叠层等）；平时复用已验证检查。合成背景检查不计作原稿整体还原度，也不取代真实局部像素检查。只有被机制测试覆盖的 backdrop/mask 可免除无辨识力的单色 effect region，其余颜色、字形、阴影等检查仍保留。

# 闭合容器几何

当颜色分割能隔离闭合容器时，feature 可使用
`"detector":{"kind":"enclosed_container","foreground":{"kind":"light","luma_min":220}}`。
它填充内部孔洞后测轮廓，避免内部文字改变质心。仅适用于闭合、与背景可分离的容器；原稿先验证分割目标，开放边界、遮挡或背景连通时不可套用。
该 feature 必须指定 `paint_region`，指向覆盖相同 node_ids 的 blocking region，继续检查描边/填充的实际像素。轮廓填充会消除描边厚度信息，不能单独验收视觉效果。内部文字保留各自检查。阈值在首次渲染前确定。

