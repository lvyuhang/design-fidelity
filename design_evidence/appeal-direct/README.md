# MCP 首次实现案例：处罚申诉业务卡片

预览：http://127.0.0.1:8767/?case=appeal-direct

本例的直接实现已与原稿很接近。整卡 RGB MAE 为 1.5532，已有校准版为 1.5268；主要额外差异在分隔线，文字和背景填充区域的两版测量结果相同。这是单次案例结果，不能推断其他组件的平均效果，也不换算成还原度百分比。

## 先冻结，再测量

- 蓝湖固定版本：84ebb977-1081-434c-9147-12e6147c820b。
- 本轮直接调用 MCP 的 `lanhu_inspect_design_region` 和 `lanhu_export_design_assets`，读取节点、原稿预览及原始盾牌导出。
- 独立实现文件：`flutter_ui_components/lib/experiments/appeal_direct.dart`，只导入 Flutter；未导入或复制已有 AppealCard、SourceShapePainter、source_specs.g.dart。
- 常规 Flutter Stack、Text、BoxDecoration、Divider；同一 375×125 舞台及 343×116 卡片。
- 实现完成后、任何实现截图生成之前保存 `freeze.json` 与 `appeal_direct.frozen.dart`。
- 冻结后只创建展示页、测试与测量工具。组件视觉修正 0 次，编译/运行修复 0 次；测量脚本每次先校验代码 SHA-256。
- 当前会话保留此前的实现知识，已有苹方字体准备和对源属性的理解，所以这不是完全独立的盲测。初始 MCP 预览图属于输入。本例验证的是“去掉实现后的视觉迭代”效果。

冻结代码 SHA-256：`bf0107efd896a5989bf259d83d89dc036064f44a972fba45e41a8807616df103`。

## 测量

同一 Flutter 测试引擎、同密度 4× 网格、同一原稿；没有坐标拟合或缩放。两版共享同一苹方字体及原始盾牌 PNG。字体子集为新增实验页补充了字形，两版使用相同的测量时字体；文件哈希记录在 `evaluation.json`。局部范围在冻结后选定，所选区域全部报告。

| 区域 | 直接实现 MAE | 已有校准版 MAE |
| --- | ---: | ---: |
| 整张卡片 | 1.5532 | 1.5268 |
| 标题文字 | 6.5470 | 6.5470 |
| 字段与结果 | 3.4624 | 3.4624 |
| 分隔线 | 1.0842 | 0.2671 |
| 申诉按钮 | 1.7137 | 1.7121 |
| 按钮下方阴影 | 0.5467 | 0.5458 |
| 原始盾牌资源 | 0.3775 | 0.2946 |
| 背景填充 | 0.2258 | 0.2258 |

分隔线源路径两端的 y 分别为 0.2297、0.7703，首版使用水平 Divider，保留约 0.54px 的源路径纵向差别。文字误差相同，依然有字体栅格化差异。按钮及渐变误差接近；盾牌为同一原始 PNG，因此此区域不验证矢量生成能力。

首次测量发现 Flutter widget tests 默认关闭标准 BoxShadow 模糊，CustomPaint 手动阴影则不受影响，导致不公平比较。已通过测试 binding 的 `disableShadows=false` 统一两版环境后测量，未修改冻结组件。无效初测结果存放在 `invalid-measurement-shadow-disabled/`，不用于结论。

## 验证与复现

`dart analyze lib test` 无问题；24 项 Flutter 测试通过，包括实验页 375/1240px 视口、申诉回调及同密度截图。Web release 构建并进行浏览器检查。测试结果不等于视觉验收通过。

依次运行：

```sh
cd flutter_ui_components
flutter test test/appeal_direct_test.dart
cd ..
python3 tools/evaluate_appeal_direct.py
cd flutter_ui_components
flutter build web --release --no-web-resources-cdn
```

脚本需要 Pillow / numpy。`protocol.json` 保存实施规则和测试条件修正；`evaluation.json` 保存原稿、实现截图、代码和字体哈希。三版概览见 `three-way-comparison.png`。
