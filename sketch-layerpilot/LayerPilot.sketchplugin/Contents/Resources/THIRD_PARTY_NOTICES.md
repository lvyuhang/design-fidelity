# 第三方代码与改动说明

上游项目：[Ashung/Automate-Sketch](https://github.com/Ashung/Automate-Sketch)

固定提交：[4cc9ccf72052dc39f976ffdbc7aca3df2ada5738](https://github.com/Ashung/Automate-Sketch/tree/4cc9ccf72052dc39f976ffdbc7aca3df2ada5738)。版权：Copyright (c) 2022 Ashung Hung。许可：MIT，完整文本随源码与插件包一并提供。

| 上游文件（相对其 Contents/Sketch） | 本项目使用方式 |
| --- | --- |
| `Export/Quick_Export.js` | 提取 `nameParts` 和 `formatNameUnderLine` 到 `lib/upstream.js`，调整相等比较与模块导出。`core.filename` 在其上增加非法字符清理、长度限制及完整图层 ID，实际参与每次文件导出。 |
| `Layer/Remove_Empty_Groups.js` | 参考空组判断、子层遍历和删除计数流程；在 `engine.organize` 重写为后序遍历与公开 DOM 操作，增加样式、Frame、蒙版、布局及导出设置保护。不是原生代码直接移植。 |
| `Arrange/Order_Layers_by_Position_XY.js` | 研究参考。旧排序逻辑未放入运行时；新算法只交换互不重叠的相邻层，保留绘制顺序。 |
| `Slice/Auto_Slice.js` | 0.2.0 复用“资源组内放置 Slice、叶子资源与 Slice 一起包组、仅导出组内容”的处理方式；通过公开 `new Slice` 构造器创建，单层资源使用上游的 `MSSliceLayer.sliceLayerFromLayer` 计算含旋转和效果的范围，并沿用 `exportOptions().setLayerOptions(2)` 设置。新增资源关联、去重、尺寸与倍率更新。未移植上游统计和本地导出流程。 |

0.5.0 的多级整理、按钮底色/图标碎片规则、固定 SVG 画布、内存渲染对比及 TIFF 像素读取为本项目实现。未引入模型或在线服务。

0.4.0 的通用背景包围、重复行检测、互为最近邻配对、名称提取及快照复用均为本项目新增代码。Sketch-Mate 仅作为功能调研参考，未复制其代码。

空间分组、图标图片规则识别、裁剪保护、中文窗口和回归测试为本项目新增代码。并非把整个上游插件改名，也不将新增能力归属于上游。

`vendor/automate-sketch/provenance.json` 记录原路径、固定提交与 Git blob SHA-1。原文件仅供溯源，不会被插件加载，其中原有的统计调用也不会执行。发行包只包含本项目运行时文件、许可和本说明。

API 依据：[Sketch JavaScript API](https://developer.sketch.com/reference/api/) 与 [插件 manifest](https://developer.sketch.com/plugins/plugin-manifest)。本机 2026.1.1 的撤销历史标题兼容层使用有存在性检测的 `historyMaker`；没有该接口时仍由 Sketch 默认的命令历史处理。
