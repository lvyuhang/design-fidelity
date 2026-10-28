# design_fidelity

蓝湖（Sketch）设计数据在 Flutter 中的已验证渲染原语。所有页面共用一份实现，避免每页重新推导描边位置、阴影核、透明叠层等细节。

## 接入

把本目录复制到项目（如 `packages/design_fidelity`），在 `pubspec.yaml` 中添加：

```yaml
dependencies:
  design_fidelity:
    path: packages/design_fidelity
```

首次接入或升级 Flutter 后，在本目录执行 `flutter test`，确认 `test/primitives_test.dart` 全部通过。

## 源字段与原语的对应

| 蓝湖 raw_style | 原语 |
|---|---|
| `font` / `font.styles[]` | `sourceTextStyle` + `SourceText` / `SourceText.rich` |
| `fills[]`（color / linear gradient） | `SourceFill.color` / `SourceFill.linear` |
| `borders[]`（内边框 / 中心边框 / 外边框，`borderOptions` 端点、连接、虚线） | `SourceBorder` + `SourceBorderPosition` |
| `shadow[]`（外阴影 / 内阴影，blurRadius、spread、offset） | `SourceShadow`（外阴影自动挖空） |
| `radius` / `points` | `SourceRectShape` / `SourceOvalShape` / `SourcePathShape` |
| `opacity`（图层） | `SourceBox.opacity`（整层合成一次） |
| `blur`（blurType 3 背景模糊 / 0 高斯模糊） | `SourceBackdropBlur` / `SourceLayerBlur` |
| 已导出素材（export frame） | `SourceAsset(exportRect: …)` |
| 未切图素材 | `SourcePlaceholder` |
| 系统状态栏 / Home Indicator | `SystemChromeSlot`（只占位，不绘制） |
| 节点身份 | `sourceKey(nodeId)` / `SourceNode` |

半径到 sigma 的换算只在 `FidelityEffectMapping` 中定义。若校准证明系数需要调整，只改这一处，再重跑本包测试和受影响页面的门禁。

## 已知限制

- 渐变只支持 linear；radial/angular 由生成器标记为 unsupported。
- 自由路径的负 spread 无法精确表示，生成器会报告。
- `blendMode` 非 0 的图层不在本包处理范围内，生成器会报告。
