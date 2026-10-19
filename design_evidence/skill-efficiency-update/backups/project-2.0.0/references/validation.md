# v2 验证记录与边界

验证日期：2026-10-12。此文件记录本次实际运行，不是对未来页面效果的保证。

## 已执行

- 31 项独立 Python 行为测试，随包可重跑。测试数据、参考图和测试字体均为合成，不依赖当前项目、Cookie、商业字体或其他开发者的本机路径。
- 新建独立 Flutter 项目，Flutter 3.47.7，375×812 逻辑画布，2× 输出。项目未复用原组件代码。测试画面为带透明留白图标、几何标题块、CTA 和背景的合成夹具，不是蓝湖真实业务页面。
- 同一契约先渲染图标下移 4px 的版本：整页 MAE 仅 0.0893，但元素位置和组内对齐关系均失败，门禁返回 1。修正偏移并重新渲染，MAE 0、失败项 0、门禁返回 0。证明不会仅凭低整页误差放行。
- 独立 Flutter 项目通过截图测试和 `dart analyze lib test`。`flutter analyze` 的 LSP 在本机中文工作路径下出现 JSON 截断异常，因此用 Dart 分析器完成同范围检查；未以异常退出声称分析通过。
- 使用现有平台介绍页两份原始 MCP JSON 和参考图生成草稿：82 个待审核节点、7 组几何相邻关系候选。它们仍需审核，不等同于 82 个已通过检查。
- 性别模块局部参考图被拒绝匹配 375×812 全页画布，避免把局部截图拉伸为整页参考。
- 旧 R2 页面用 v1 契约在诊断模式下重测，两模型各有 8 项文字差异；总体标记 NOT_EVALUATED，不更新阈值、不把旧实现宣称为 v2 合格基线。
- Skill 官方结构检查使用真实 PyYAML 执行，不依赖模拟 YAML 解析器。

## 未验证的范围

- 本轮没有从在线蓝湖重新选一张未知完整业务页并完成全新实现。取证兼容性验证使用现有保存的真实 MCP 返回。
- 没有证明任意模型、任意渲染器或任意设计复杂度都会达到同样效果。
- 字体检查覆盖 cmap，不覆盖复杂脚本塑形、fallback 选择或运行时实际字重；仍需截图验证。
- 收据防止常见旧文件和输入漂移，不是可信执行证明。环境字段来自调用方，输入清单由执行者负责完整性。
- 特征分割依赖颜色与 ROI，需要首次视觉核对；像素指标不验证业务语义、交互逻辑或可访问性。

## 回归命令

在已安装依赖的 Python 环境中执行：

```sh
python -m unittest discover -s /path/to/lanhu-design-fidelity/tests -v
```

业务项目应另保存自己的成功和失败样本。更新 SDK、字体、契约或渲染器时，重跑相应样本；不要只用原稿对原稿自比较作为有效性证明。


## 随包 Flutter 接入夹具

复制 `assets/flutter-smoke/` 到临时开发目录，执行 `flutter pub get`。将 contract.json 的 environment 改为实际 Flutter/engine 版本，再按 usage.md 用包装器调用：

```sh
flutter test --no-pub --dart-define=OFFSET=4 --dart-define=OUTPUT=r0/render.png test/render_test.dart
flutter test --no-pub --dart-define=OFFSET=0 --dart-define=OUTPUT=r1/render.png test/render_test.dart
```

分别生成 r0、r1 收据并运行门禁，预期先 FAIL 后 PASS。模板内 source.json 明确标注为合成数据；不得当作真实 MCP 返回用于业务还原宣传。
