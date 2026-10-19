# 聚星阁：设计稿到 Flutter 的组件还原验证

## 从干净克隆启动

首次接入请阅读 [安装与运行说明](docs/GETTING_STARTED.md)。提供 Python 3.11+、冻结的 Flutter 3.47.7 以及本机可使用的字体后：

```sh
./setup.command --profile all --flutter-sdk /path/to/flutter
python3 project.py doctor --strict
python3 project.py verify --render
python3 project.py start flutter
```

无需登录即可运行打包的“提现-2”离线对比案例。使用 `python3 project.py start review --demo` 可启动带同一设计快照的安卓验收台。真实蓝湖/设备/AI功能分别需要使用者自己的连接与授权。此处的安装复现检查不替代设计还原度验收。

## 仓库范围与当前版本（2026-10-19）

本仓库保存 Flutter 还原实验、蓝湖取证与测量工具、Sketch 插件、安卓验收台源码，以及 `skills/lanhu-design-fidelity/` 的 Skill 2.18.6 快照。下文保留历次实验记录，历史结论不代表当前页面已通过完整视觉验收。

- `flutter_ui_components/`：Flutter 组件、页面、原始图形资源及测试；最新案例为 `?case=withdraw-2-skill2186`。
- `skills/lanhu-design-fidelity/`：与本次实际使用版本同步的可安装 Skill。
- `tools/`、`design_evidence/`：取证/比较脚本与源节点元数据。
- `android-design-review/`：安卓设计验收台的源码快照；本地该目录有独立 Git 仓库，父仓库上传不包含其嵌套 `.git` 和历史。
- `sketch-layerpilot/`：Sketch 插件源码。

本机虚拟环境、构建产物、APK、设备数据、历史截图、导出包和 `validation/` 实验工作目录不纳入仓库；不会删除本地这些文件。Cookie、API 密钥及 `.env.local` 也不上传。

字体需由接入者自行提供有权使用的文件，`flutter_ui_components/assets/fonts/` 不入库。运行前核对 `pubspec.yaml` 中实际字体文件及每个字重的字符覆盖；安装依赖后按该子项目的 README 启动。需要历史参考截图时，按固定蓝湖版本重新取得源图。

最新案例的标题裁切已修复，增加了复用正式 `ComponentLab` Theme 的截图入口和标题单行回归测试。此修复不代表其他历史案例已重新验收。

本工程用于验证蓝湖设计数据转为 Flutter 组件的还原能力。当前包含七类组件、八个固定状态样本：图文动态卡片、性别选择（未选 / 女生选中）、带嵌套回复的评论、清除缓存弹窗、首页五项底部导航、处罚申诉业务卡片、登录按钮及协议未勾选态。

## 当前预览

本机静态预览：http://127.0.0.1:8767/ 。每块源稿/实现表面固定为 375 Flutter 逻辑像素宽，浏览器放大缩小不改变组件布局参数。可切换仅 Flutter、左右对照、透明叠加。同一页先展示动态卡片、性别两态及评论，再保留弹窗、导航、申诉及登录；每组可独立点击查看回调，全部支持左右对照与透明叠加。弹窗展示高 280，导航高 98，业务卡片高 125，登录局部高 395。

文本、形状、描边、阴影、渐变均由 Flutter 实现；登录图标、导航首页图标、业务卡片盾牌使用经哈希校验的原始切图。导航中有完整数据的图标从原始贝塞尔路径生成。消息图标外轮廓缺少路径，近似实现已单独标注。完整源稿仅参与对照视图；新增组件有明确标注的局部媒体回退：照片（含已烘焙的图片计数角标）、头像、警示条淡红盾牌来自 4× 预览裁切，不能作为独立还原证据。其余文字、状态标签、卡片与操作图形由原生组件或原始图标实现。

## 自动化视觉门禁

完整页面实验已加入源节点驱动的视觉契约与 CI 级检测器。`tools/visual_fidelity_gate.py` 从保存的蓝湖 MCP 节点自动取得检测区域，比较可见像素边界、中心、尺寸、组内中心线、颜色采样及区域 MAE/P95；失败时返回非零退出码。它能识别透明留白切图导致的“布局框居中、可见主体未对齐”，也能阻断字体缺字、文字裁切和局部误差被整页均值掩盖的问题。

工作流、阈值原则与命令见 `design_evidence/visual-fidelity-workflow.md`；当前页面契约见 `design_evidence/full-page-models/visual-contract.json`，报告输出在 `design_evidence/full-page-models/visual-gate/`。

## MCP 直接实现实验

新增独立案例：http://127.0.0.1:8767/?case=appeal-direct 。组件首页也有入口。

处罚申诉卡片先独立实现、冻结代码，再与原稿和已有校准版比较；冻结后视觉修正 0 次。单次实验的整卡 MAE 为 1.5532，校准版 1.5268，主要额外差异为分隔线；两版文字和背景填充指标相同。当前会话含历史知识，不是严格盲测；输入包括 MCP 首次返回的原稿预览。

详见 `design_evidence/appeal-direct/README.md`、`protocol.json`、`freeze.json` 和 `evaluation.json`。直接组件位于 `flutter_ui_components/lib/experiments/appeal_direct.dart`；对照页支持三版并排、原稿叠加、局部放大。测量工具已统一启用标准 BoxShadow 模糊，避免 Flutter 测试默认禁用阴影造成错误比较。

性别选择案例：[实验 02](http://127.0.0.1:8767/?case=gender-direct)，覆盖未选择与女生选中两个状态，现在提供蓝湖原稿、GPT-5.6 Sol high 独立首版、GPT-6 首版和此前校准版四列对比。5.6 Sol 在隔离任务中没有读取现有实现或测量结果，冻结后视觉修正 0 次；共同可验证区 MAE 为 3.3351 / 2.6923，GPT-6 首版为 0.6417 / 0.7193。主要差异来自半透明卡片内的标准阴影染色、文字宽度溢出与简化背景光晕；5.6 Sol 的女生选中原始图标和角标定位反而非常准确。盾牌内部布尔填充仍作为资源缺口统一处理。模型对比证据见 `design_evidence/gender-sol56/README.md`，原实验记录见 `design_evidence/gender-direct/README.md`。

多组件案例：[实验 03](http://127.0.0.1:8767/?case=model-comparison)，把图文动态卡片、评论、弹窗、底部导航、处罚申诉、登录协议和性别选择放在同一页，可切换三版对照、仅 5.6、仅此前 GPT-6、原稿/5.6 叠加和原稿/GPT-6 叠加。新增六类 5.6 Sol high 组件均在隔离任务中完成并在首次渲染前冻结，视觉修正 0 次。完整指标、冻结哈希、资源限制和总览图见 `design_evidence/components-sol56/README.md`。

## 固定的设计依据

- 蓝湖项目：3be04117-73d6-43db-955e-528423563e93
- 画板：登录-普通登录，a4eadc40-fbd6-4aa6-a490-5fa2139ac958
- 版本：18f1a6ed-585a-4b77-801b-7a9d5e726810
- 快照：ed07411fb68b9878b1395ab190b98915
- 原始坐标画板：375 × 812。列表缩略尺寸 187.5 × 406、4× 导出密度不参与布局换算。
- `design_evidence/login-source.json` 保存完整节点属性；`component-map.json` 将组件映射到容器、文本、图标 ID。
- `flutter_ui_components/assets/lanhu/install-receipt.json` 保留原图尺寸、透明度、SHA-256 和安装映射；五份原始资源已逐个校验。

## 新增三类样本的来源

| Flutter 组件 | 蓝湖画板 / 固定版本 | 源组件几何 |
| --- | --- | --- |
| `CacheClearDialog` | 清除缓存 / f11338b7-d535-4cb0-9843-10f3e481df91 | (23,267)，330 × 228，圆角 24 |
| `JuxingBottomNavigation` | 首页备份 2 / 32aa246d-8d21-40b3-ba5c-32e8d532bdc6 | (14,735)，347 × 56，圆角 28 |
| `AppealCard` | 登录受限-1 / 84ebb977-1081-434c-9147-12e6147c820b | (16,352)，343 × 116，圆角 18 |

对应 `design_evidence/{modal,nav,appeal}-source.json` 保存完整样式与节点，`expanded-component-map.json` 保存组件边界、原始资源和已知缺口。`expanded-resources.json` 记录原始 4× 对照图的两个无缩放分块及导出包 URI，`fetch_expanded.py` 读取 MCP 二进制资源并校验、安装到客户端。分块仅用于避免预览接口 1400px 上限缩小图像，两片拼接后仍为真实 1500px 宽。

组件代码位于 `flutter_ui_components/lib/components/expanded_components.dart`，公共绘制器在 `source_primitives.dart`。`source_specs.g.dart` 由 `generate_source_specs.py` 从固定源数据生成，保留 node ID。背景舞台只是对照夹具，可复用组件自身分别为 330、347、343px 宽。

新增发现：源数据 `font.align` 将原生 `NSTextAlignment=2` 标成了 `right`，但原始枚举 2 代表居中。当前按原始枚举还原，不盲从派生 CSS。切图中已经包含的 5% 盾牌透明度不会再次乘算。

## 这轮确认和修正的问题

1. 原示例未建立组件和具体源节点的对应关系，且把 375px 移动组件拉满了浏览器。当前预览和组件几何分别固定。
2. #EEDCC4 描边、#D89B47 阴影本来就存在于设计数据。此前把阴影色推广成实心按钮主题色，属于属性用途错配，并非颜色无法提取。
3. 同一半透明色必须连同背景一起还原：当前背景含横向渐变、两个带透明度的径向光晕及模糊。
4. Material 默认文字样式可能继承字距，造成协议换行偏差。样本明确设置 inherit=false、letterSpacing=0、字重、字号和行高。
5. 普通 Flutter BoxShadow 的内部会透过 85% 不透明填充，产生额外染色。当前绘制器对外阴影做内部挖空，再绘制填充和内描边。
6. 切图的透明边距与矢量几何包围盒不同。图标按经核验的 4× 导出画框显示，保留透明像素，避免把图形缩小到紧包围盒。
7. 字体名不能代替实际加载。本机已从系统安装的苹方提取 400 Regular / 500 Medium / 600 Semibold 字体子集供本地预览，记录在 font-receipt.json。字体文件不入 Git；脚本需要目标机器有对应字体。

## 校验结果及边界

`dart analyze lib test` 无问题；49 项 Flutter 测试通过，覆盖 375/1240px 视口下八个样本的固定宽度、源尺寸与位置、独立点击回调、评论 @momo 富文本颜色、受控性别状态、三个模型对比页及 4× 渲染图生成。Web release 构建成功。浏览器已检查全部组件切换、三版对照、单列模式、两种叠加模式、评论回复回调和性别双状态，浏览器错误与警告日志为空。测试通过只表明几何及行为检查通过，不代表视觉完全一致。

像素比较由 `tools/compare_renders.py` 复现，使用相同坐标、未经缩放的 4× PNG：

| 区域 | RGB 平均绝对误差，0–255 | 每像素最大通道误差 P95 |
| --- | ---: | ---: |
| 四按钮及背景局部 | 0.7300 | 2 |
| 协议及背景局部 | 2.2866 | 12 |
| 按钮内部无文字填充采样区 | 0.0572 | 1 |

四个按钮的文字可见像素边界相差最多 1 个 4× 像素，即 0.25 个源画板像素。这是阈值下的字形边界测量，不等于排版框错位。当前仍存在字体抗锯齿、渐变取整、模糊内核差异；协议区域需继续做文字轮廓诊断。

新增组件由 `tools/compare_expanded.py` 比较。为了避免大背景稀释误差，同时记录组件和局部：

| 原始 4× 区域 | RGB 平均绝对误差，0–255 | 最大通道误差 P95 |
| --- | ---: | ---: |
| 弹窗面板 330 × 228 | 0.9009 | 1 |
| 导航条 347 × 56 | 1.1685 | 2 |
| 业务卡片 343 × 116 | 1.5268 | 2 |
| 弹窗标题文字区域 | 5.0594 | 44 |
| 业务卡片标题文字区域 | 6.5470 | 59 |
| 消息图标局部（含近似外轮廓） | 9.4906 | 66 |

弹窗和卡片标题的深色像素边界在阈值 140 下最多相差 1 个 4× 像素（0.25 逻辑像素），文字边缘仍存在可测的渲染差异。完整坐标、图像 SHA-256 和局部指标见 `expanded-validation.json`；组合对照图为 `expanded-source-vs-flutter.png`，红色差异图为 `diff-{modal,nav,appeal}-4x.png`。

本轮尚未解决：

- 消息图标的布尔外轮廓节点 `FEEAA557-72F1-4878-A6F3-D7D6366A776F`：直接检查原始源 JSON 后确认 `layers=[]`，无 points、image 或 ddsImage；其外轮廓为明确标注的近似描绘，表情内部路径则来自原稿。需要设计侧补导出该图标或提供完整矢量源，才可消除这一数据缺口。
- 首页照片节点有裁切几何却没有暴露原图资源地址。没有用整卡截图代替组件，也没有编造照片。现已实现原生 `FeedCard`，默认 181.5 × 318；预览照片及头像使用有标注的裁切素材。照片内图片数量角标已烘焙，当前预览不重复叠加，也不声称其已独立验证。调用方传入干净照片时可通过 `imageCount` 使用原生角标。`preview-media-manifest.json` 记录所有回退素材。
- 导航毛玻璃只验证了浅色空状态背景，尚未验证叠在照片上的效果；其他导航选中态、弹窗关闭后流程、申诉处理中等状态也未验证。

这些指标是诊断数据，不是还原度百分比。没有约定视觉验收阈值，也没有把可运行或测试通过当作视觉完全一致。像素结果来自本机 Flutter 测试引擎；Web release 另做浏览器视觉检查，不能把两种渲染器的数据混为一谈。

当前没有证据覆盖按钮按下/禁用态或协议选中态。协议样本保持未勾选，只用于检验原稿默认状态，不会代替用户接受任何协议。

## 本次截图对应的三组新增组件

代码：`flutter_ui_components/lib/components/social_components.dart`。

| 组件 / 状态 | 固定蓝湖版本 | 布局依据 |
| --- | --- | --- |
| FeedCard | 7f08adcf-1e12-4e41-b19b-47641f116d9a | 首页 (4,99)，181.5 × 318；375px 舞台居中展示，不拉伸 |
| GenderSelection / 未选 | 9121ae6b-b534-4070-aa1b-5085a2406781 | 选项 134 × 164、圆角 22，圆形图标 64 × 64 |
| GenderSelection / 女生选中 | 6c06f0c3-cc7b-4d0c-8617-04693fdbb877 | 填充 #FFF9EC，边框 #DDAA5A；警示条 307 × 36 |
| CommentPanel | ae9eabab-b45e-4ae3-a910-bd2f49703c3d | (0,350) 起 375 × 374；正文 14 / 20，一级头像 30，二级头像 24 |

`design_evidence/{feed,gender_none,gender_female,comments}-source.json` 是节点证据；`requested-resources.json` 记录无缩放分块和原始导出包；`fetch_requested.py` 安装 9 个原始图标。固定样本的性别选择是受控组件：点击输出 male/female 回调，分别保留两张有原稿的状态方便对照；没有把未知男生选中态、回复展开后的内容等当成已验证设计。

本次修正了两项跨组件提取问题：父组的水平镜像需要向子路径传播（评论回复气泡）；混色文字需要读取全部 text_runs，而且使用颜色 value 字段（原始数值 r/g/b/a 全为 0，却在 value 内记录真实颜色）。评论中的 @momo 保留 #BC914A；作者标签加载 500 Medium 字重。

独立资源限制经过源 JSON、DDS 及同照片详情页交叉检查：照片与头像均只有裁切几何，没有下载地址。当前使用预览裁切媒体，保留在独立 `assets/fixtures/` 目录；照片自带的角标不能改数后冒充原生结果。警示条淡红盾牌同样存在布尔子路径缺失，作为局部图像回退。三类回退区域全部从比较中剔除（热图以蓝色表示）；不能用与原稿相同的图片像素证明组件还原。

`tools/compare_requested.py` 生成 `requested-validation.json`、各区域热图和 `requested-source-vs-flutter.png`。局部 RGB MAE（0–255）：动态卡标题 4.7858；性别未选卡 0.4115 / 0.3930；女生选中卡 0.2678；性别标题 3.7792；评论标题 6.7284。数值反映局部差异，尤其文字抗锯齿；不转换成“还原度百分比”，也不将大面积背景平均值作为通过依据。

重取素材的顺序：`fetch_requested.py` → `prepare_requested_media.py` → `generate_source_specs.py` → `prepare_fonts.py` → `flutter test` → `compare_requested.py` → Web 构建。所有图像工具均读取已保存的证据，比较不进行坐标拟合或缩放。

## 复现

Flutter SDK 已安装于 `/Users/tan/development/flutter-arm64/flutter`，此轮使用 Flutter 3.47.7 / Dart 3.13.5。

```sh
# 在本项目根目录，使用装有 fonttools 的 Python；本机工具已放在 .tools/fonttools。
PYTHONPATH=.tools/fonttools python3 tools/prepare_fonts.py
cd flutter_ui_components
flutter pub get
dart analyze lib test
flutter test --reporter expanded --timeout 45s
flutter build web --release --no-web-resources-cdn
cd ..
# 此脚本需要 Pillow 与 numpy。
python3 tools/compare_renders.py
python3 tools/compare_expanded.py
python3 tools/compare_requested.py
python3 -m http.server 8767 --bind 127.0.0.1 --directory flutter_ui_components/build/web
```

本机 Python 依赖运行时：`/Users/tan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`（含 Pillow、numpy）。

Flutter analyze 在本机中文路径下触发了分析协议 JSON 截断，改用同一 SDK 的 `dart analyze lib test`，已通过。截图测试把真实图片解码、原生截图和文件 I/O 放进 runAsync，以避免测试虚拟时钟挂起。

新增源数据后，先运行 `python3 tools/generate_source_specs.py`，再格式化 Dart 并运行 `tools/prepare_fonts.py` 更新本地字形子集。

## 后续沿用的验证顺序

固定源版本 → 获取干净原图与原始节点 → 按可见内容选定组件边界 → 导出并校验资源 → 显式处理字体与透明合成 → 375px 实现 → 同密度渲染 → 分区域比较 → 记录无法确认的状态和差异。新增组件必须先有对应画板/节点证据。
