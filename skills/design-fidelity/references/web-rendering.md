# Web（React）接入

仅在首次接入 React 项目或修改渲染环境时读。流程、契约和门禁与 Flutter 相同，只有原语、生成文件和渲染器不同。

## 安装

```sh
python3 <skill>/scripts/install_app.py init --app .          # 有 package.json 时自动选 react
npm install
npm install -D esbuild playwright                             # 只用于还原度渲染
npx playwright install chromium
python3 <skill>/scripts/install_app.py page --app . --name order_detail
```

`init` 把 `assets/web/design-fidelity-react` 复制到 `packages/design-fidelity-react`，并在 `package.json` 加 `"@design-fidelity/react": "file:packages/design-fidelity-react"`。包以 TypeScript 源码发布：Vite / esbuild 直接使用；Next.js 需加入 `transpilePackages`。`page` 生成的配置带 `"target": "react"`，生成文件在 `src/fidelity/<page>.g.tsx`，素材在 `src/assets/design/<page>/`（由生成文件 `import`）。

## 生成的 Scene

```tsx
import { OrderDetailScene } from '../fidelity/order_detail.g';

export function OrderDetailPage({ order, onConfirm }) {
  return (
    <div style={{ height: '100dvh' }}>
      <OrderDetailScene
        overrides={{ 'AMOUNT-NODE-ID': () => <Amount value={order.amount} /> }}
        onTap={{ 'CONFIRM-NODE-ID': onConfirm }}
      />
    </div>
  );
}
```

- Scene 是整页组件：给它一个满高的父元素，不再额外处理安全区。根层按 `--df-safe-top` / `--df-safe-bottom`（默认 `env(safe-area-inset-*)`）移动；普通浏览器里没有状态栏，内容自动上移到视口顶部。移动端 Safari 需要 `<meta name="viewport" content="viewport-fit=cover">` 才会给出安全区。
- 视口比设计稿矮时主体滚动，底部按钮、底部导航固定在底部安全区之上。
- 文字用 rem，跟随浏览器字号设置；验收在 1.0 和 1.3 倍下检查。
- 每个源图层带 `data-node-id`，几何探针按它测量。override 的内容放在同一个框里。

## 原语与 lint

| 原语 | 对应 |
|---|---|
| `SourceBox` | 填充（纯色 / 线性渐变）、内中外描边、内外阴影、图层透明度 |
| `SourceText` | 绝对行高、字距、混排；`<Page>Tokens` 中的文字规格 |
| `SourceAsset` / `SourcePlaceholder` | 导出素材（含导出框）/ 缺素材占位 |
| `SourceBackdropBlur`、`SourceLayerBlur`、`SourceOpacity`、`SourceFlip`、`SourceClip` | 效果与蒙版 |

半径到 sigma 的换算与 Flutter 相同（σ = 0.5 × 半径）。页面代码由 `web_fidelity_lint.py` 检查：图标库（W001）、箭头字形（W002）、颜色字面量（W003）、手写字号行高（W004）、`box-shadow`（W005）、`blur()`/`backdrop-filter`（W006）、`border`（W007）、禁用缩放（W009）、`<img>` / `url()`（W010）、生成文件被改（W011）。例外写 `// fidelity-lint: allow Wxxx 原因`。

已知近似（生成报告 `unsupported` 中会列出）：自由路径上的外阴影用 `drop-shadow`（无扩展、不挖空），内阴影不绘制；虚线渐变描边取首个颜色；对角渐变在设计尺寸下精确。

## 渲染入口与 harness

`generate` 首次创建 `fidelity/<page>/render.tsx`（项目代码），并把 `assets/web/fidelity_render_harness.cjs` 复制到 `fidelity/<page>/support/`（工具代码，每次 generate 同步）：

```tsx
import { OrderDetailAssets, OrderDetailScene } from '../../src/fidelity/order_detail.g';
export default function Page() {
  return <OrderDetailPage order={FIXTURE_ORDER} onConfirm={() => {}} />;  // 生产页面 + 固定夹具
}
export const fidelity = { designSize: OrderDetailScene.designSize, designPadding: OrderDetailScene.designPadding,
                          scale: 4, assets: OrderDetailAssets.all, fontMap: 'fidelity/font-map.json' };
```

harness 用 esbuild 打包入口，在 Playwright Chromium 中按设计尺寸和设计安全区渲染，输出 4 倍 PNG、`.geometry.json` 与五种设备 × 两档字号的 `.variants.json`（格式与 Flutter 相同）。设计字体从磁盘按 `font-map.json` 加载，不进入打包产物。`--scene fidelity/<page>/scene.g.json` 模式检查描边、填充叠加、背景模糊、蒙版等场景义务：读取原语写出的 `data-df-*` 属性并做描边带像素探测。

字体映射的 `web` 键为上线字体：`null` 为系统字体栈（苹果设备上即苹方），写名称则使用页面 CSS 中声明的 family。

## 目标环境

契约环境 `renderer: chromium_playwright`，`renderer_version` 取 Playwright 版本。像素基线只在同一 Chromium 版本、同一字体文件下可比；升级 Playwright 后需要重新建立基线。Safari、Firefox 的模糊和文字抗锯齿可能有细微差异，上线前在目标浏览器中目视核对。
