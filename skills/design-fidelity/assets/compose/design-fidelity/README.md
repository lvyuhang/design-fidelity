# design-fidelity (Jetpack Compose) — preview

Compose primitives used by pages generated with `generate.py --target compose`.
Same semantics as the Flutter `design_fidelity` package and `@design-fidelity/react`:
inside/center/outside borders, knocked-out shadows (sigma = 0.5 x radius), absolute
line heights with even leading, safe-area page frame, `fidelity:<node id>` test tags
and `data-df-*` semantics bindings for the scene checks.

Status: **preview**. The code is syntax-checked but has not yet been compiled and
pixel-tested on a developer machine. Before relying on it, add the module to the
app (`include(":design-fidelity")`), run the page's Robolectric render test and
compare with the design; report any mismatch so the mapping is fixed once here.

Known gaps on Compose: background blur is not drawn (Compose cannot sample content
behind a node; the generator reports it as unsupported), layer blur needs API 31+.
