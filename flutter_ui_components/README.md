# 聚星阁 Flutter 组件还原样本

当前覆盖七类组件、八个固定状态。运行后在一个页面查看固定 375px 的组件、蓝湖原稿与透明叠加；另有处罚申诉、性别选择和全组件模型对比实验。

主要组件：`lib/components/`；对照页：`lib/main.dart`；冻结实验组件：`lib/experiments/`。

本机预览：`http://127.0.0.1:8767/`；实验入口：`?case=appeal-direct`、`?case=gender-direct`、`?case=model-comparison`。全组件页可在蓝湖原稿、GPT-5.6 Sol high 冻结首版和此前 GPT-6 已核对实现之间切换与叠加。

完整的源版本、组件节点映射、验证数值、复现步骤和未覆盖范围见上一级目录 README.md 与 design_evidence/。

```sh
flutter pub get
dart analyze lib test
flutter test --reporter expanded --timeout 45s
flutter run -d web-server --web-hostname 127.0.0.1 --web-port 8766
```

需先运行上一级 tools/prepare_fonts.py 生成本机字体子集。
