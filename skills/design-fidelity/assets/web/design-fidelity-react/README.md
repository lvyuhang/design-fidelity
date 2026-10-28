# @design-fidelity/react

React primitives used by pages generated with `generate.py --target react`.
They reproduce design layers with the same semantics as the Flutter
`design_fidelity` package, so a web page is checked by the same contract.

| Primitive | Source layer |
|---|---|
| `SourceBox` | Shape layer: fills (solid / linear gradient), inside/center/outside borders, outer/inner shadows, layer opacity |
| `SourceText` | Text box with absolute line height, letter spacing, mixed runs; rem units follow the browser font-size setting |
| `SourceAsset` | Exported bitmap, optionally drawn in its export rect |
| `SourcePlaceholder` | Missing exported asset (pink, labelled) |
| `SourceBackdropBlur`, `SourceLayerBlur`, `SourceOpacity`, `SourceFlip`, `SourceClip` | Effects and masks |
| `SourceScene`, `Placed`, `SourceNode`, `dy`, `dyBottom` | Page frame: safe area, scrolling body, pinned footer, `data-node-id` |

The package ships TypeScript source. Vite and esbuild consume it directly;
for Next.js add it to `transpilePackages`.

Effect radius mapping (shared with Flutter): Gaussian sigma = 0.5 x source
blur radius. CSS `box-shadow` blur is 2 sigma, `filter: blur()` takes sigma.

Known approximations, reported by the generator: shadows on free paths use
`drop-shadow` (no spread, not knocked out); inner shadows on free paths are not
drawn; gradient borders with dashes use the first stop colour; diagonal
gradients are exact at the design size.
