# 性别选择：MCP 首次实现实验

预览：[性别选择实验](http://127.0.0.1:8767/?case=gender-direct)。现已扩展为四版模型对比：蓝湖原稿、GPT-5.6 Sol high 独立首版、GPT-6 首版和此前校准版。可切换未选择 / 女生选中、四版并排、两种透明叠加和局部放大；每个组件表面固定 375 × 350。5.6 Sol 的隔离实验协议与结果见相邻 `gender-sol56/README.md`。

本例首次实现已经接近原稿。共同可验证区的直接版与已有校准版误差接近，没有依据宣称一版明显更好。右侧淡色盾牌仍缺内部布尔填充；校准版使用该区域的原稿裁切，其低误差不能证明独立绘制成功。

| 状态 / RGB MAE，0–255 | 直接实现 | 已有校准版 |
| --- | ---: | ---: |
| 未选择，共同可验证区 | 0.6417 | 0.6480 |
| 女生选中，共同可验证区 | 0.7193 | 0.7277 |
| 女生选中，全画布含资源缺口 | 0.7210 | 0.7212 |
| 女生选中，缺失填充区（仅诊断） | 0.8989 | 0.0463 |
| 两态，未选卡片内部填充 | 0.2280 | 0.2280 |
| 女生选中，警示文字 | 5.3422 | 5.3422 |

MAE 越低越接近，不能换算成还原度百分比。大面积背景会稀释平均误差，文字、圆角、阴影和图标的局部数据均保留在 `evaluation.json` 和页面。卡片周边 ROI 包含背景，选中态下其底端也含警示条上沿；这些数据用于局部诊断，不是独立材质或字形的评分。

## 实验规则

本轮重新调用 `lanhu_inspect_design_region` 获取两个固定快照的清晰原稿预览、原始节点、文字规格和图标 ID；调用 `lanhu_export_design_assets` 导出五份原始图标，逐一验证已有本地文件 SHA-256 相同。没有补查蓝湖底层 API。

独立的 `lib/experiments/gender_direct.dart` 只依赖 Flutter 和这些原始切图，没有导入、复制已有 `GenderSelection`、`LoginBackground`、`sourceLayer` 或校准绘制器。本轮冻结前未读取这些实现；冻结后才导入已有组件作为对照。首次实现前已记录 `protocol.json`，Dart 格式化完成后复制到 `gender_direct.frozen.dart` 并生成 `freeze.json`。随后才首次渲染、测量和查看实现结果。视觉修正 0 次，编译 / 运行阻塞修复 0 次。

**实验并非严格盲测。** 当前会话已经知道上一轮还原经验，原始字体也已准备好。本次在初稿中预先按源外阴影语义裁除透明卡片内部，并沿用已知的背景 blur radius/2 映射经验。没有刻意复现已知错误来放大直接版和校准版差距。初始输入允许 MCP 返回的原稿图，因此也不是仅 JSON 输入实验。能够说明的是“具备这些准备和经验时，无实现后视觉迭代的单次结果”，不能说明零经验接入或总体自动化成功率。

## 资源缺口

选中态盾牌节点 `5E2B6430-3BE7-47B1-9D0E-86167542ECE2` 没有 points 或导出资产。直接版仅按源贝塞尔控制点绘制已有外框与勾，省略该缺失填充，未用图片裁切补齐。

已有校准版该区域使用 `assets/fixtures/warning-shield.png` 原稿裁切。共同可验证区域与警示条指标，对两版统一排除舞台坐标 `(295,299,37,34)`；全画布和缺口诊断仍保留该区域，避免掩盖可见缺失。五个主要图标均有原始切图；其低误差说明素材正确使用，不能据此评价矢量重建能力。

## 数据与复现

- `none-input.json` / `female-input.json`：本轮完整 MCP 返回值，包含固定快照、源节点和参考资源 URI。
- `none-export.json` / `female-export.json`、`asset-verification.json`：导出元数据与本地原图映射。
- `protocol.json` / `freeze.json` / `gender_direct.frozen.dart`：首次渲染前冻结的规则、输入和代码；评估脚本校验冻结代码、输入、参考图与原图哈希。
- `evaluation.json`：原生 4× 测试渲染结果和评估时的字体哈希。对照使用同版本、同区域的已保存 1500 × 1400 原稿，由此前 MCP 资源分块拼合，无缩放；源资源映射见上级 `requested-resources.json`。
- `none-three-way.png` / `female-three-way.png`：三版总览；`*-heat-4x.png`：4× 绝对差异热图，红色亮度放大四倍，仅用于可视化。
- `verification.json`、测试 / 分析 / 构建日志、`browser-experiment.png`：交付验证证据。

未修改冻结组件即可复现：

```sh
cd flutter_ui_components
flutter test test/gender_direct_test.dart --reporter expanded --timeout 45s
cd ..
python3 tools/evaluate_gender_direct.py
cd flutter_ui_components
flutter build web --release --no-web-resources-cdn
```

Python 需要 Pillow / numpy。测量从首次运行即用 `disableShadows=false` 为两个组件开启真实阴影模糊。字体子集可由根目录 `tools/prepare_fonts.py` 更新，新页面文字引入的字形补充不会改写组件；评估时记录实际字体文件哈希。比较不做坐标拟合或重采样。

34 项 Flutter 测试通过，包含两种视口宽度、两个状态同步切换、两种模型回调、叠加模式和六张 4× 首版/校准渲染；`dart analyze lib test` 无问题，Web release 构建成功。浏览器已检查两个状态、模型对比、透明滑块和局部放大。Web 渲染与测试引擎指标分别记录，测试通过不代表像素完全一致。
