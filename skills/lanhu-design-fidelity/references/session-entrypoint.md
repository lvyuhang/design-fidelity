# 日常操作

首次接入：复制 `assets/page-session.example.json` 为页面配置（路径相对配置文件），把 `assets/flutter/lanhu_fidelity` 作为 path 依赖加入项目（见 [Flutter 接入](flutter-rendering.md)）。

```sh
# SKILL_DIR 为技能目录；python 为装好 scripts/requirements.txt 的项目环境。
page() { python "$SKILL_DIR/scripts/page_session.py" --config page.json "$@"; }
page start                       # 选页、取证之前开始计时
page prepare                     # 固定快照、素材导出框、字体覆盖
page generate                    # 生成 <page>.g.dart、scene 测试、首次生成 render 测试
page phase --phase implementation
# 页面代码组合 <Page>Scene：overrides 替换需组件化/动态的组，onTap 接交互
page spec                        # 生成可编译的 reviewed-spec.json
page phase --phase validation
page accept --note "初版" --build
# 有失败：按报告批量修代码后 page validate；通过即可交付
page phase --phase preview
page finish --note "复查结论、排除项、预览地址"
```

## 每步的产物与下一步

- **prepare**：`NEEDS_INPUT_FIXES` 时按 issues 批量补证据、字体或素材后重跑，不要开始猜图形。状态栏和 Home Indicator 不会再因缺路径而阻断。
- **generate**：报告 `<page>.codegen.json` 列出每个节点的处置、`unsupported`、`issues` 和系统 chrome。`unsupported` 中的项（如旋转、非线性渐变、自由路径负 spread）需要在页面代码里用 override 处理，或说明为何可接受。生成文件不可手改。
- **页面代码**：在 `page_inputs` 中登记的文件里组合 Scene。只用原语和 `<Page>Tokens`，lint 会在渲染前拦截违规。render 测试是项目代码，首次生成后由你维护：把 `page:` 换成组合后的页面，`appBuilder:` 换成生产根节点。
- **spec**：`SPEC_COMPILES` 后复核 `review_reason` 以 `auto:` 开头的检测器、局部效果区域和默认阈值，确认后即冻结。`SPEC_NEEDS_REVIEW` 时按 `compile_error`、`needs_detector`、`unbound_obligations` 处理。已手动修改过的 spec 不会被覆盖。
- **accept / validate**：依次执行 compile、lint 与 preflight、渲染与 scene 测试、像素门禁、节点几何门禁、多尺寸检查，最后构建。失败信息会直接指出节点和偏差（例如 `top +2.00px`、`line box height +4.00px`）。修完代码、契约没变时用 `validate`。
- **finish**：要求最近一次验证成功、收据有效，并附非空复查记录。未通过时用 `stop --note` 记录原因，它不授予验收。

## 门禁结果的处理

| 结果 | 处理 |
|---|---|
| lint 失败 | 改用对应原语或 token，不加无理由的 allow |
| 节点几何失败 | 按 delta 修布局；文字的 line box 偏差先查字体、字重、行高 |
| 像素 / 特征失败、几何通过 | 查效果参数、素材、字形渲染；不改阈值 |
| 多尺寸 `exceptions` / `horizontal_overflow` | 改为弹性布局（Row/Column、Flexible），见 [生成与组件化](codegen.md) |
| `NOT_EVALUATED` | 先修报告指出的输入、契约或环境问题，不要盲调 UI |
| 连续两轮无改善 | 换定位方法，见 [定位](process-gates.md) |

只运行当前页面的检查。历史案例和 Skill 全套测试只在维护检测器或升级 SDK/字体/渲染器时运行。

## 其他命令

- `page inspect --view components|issues|assets|text|visual|scenes|effects`、`--component NODE_ID`、`--node NODE_ID --pointer /raw_style`：按需查证据，组件包完整返回；超出 `--limit` 时返回定位信息并标 `complete_packet:false`，不会悄悄截断。重复读取同一内容只回传提示，上下文丢失时加 `--refresh`。
- `page status [--verbose]`：查看进度、轮次与阶段耗时。
- `page report`：从运行产物生成阻断项、观察项、逐节点几何偏差、lint 例外、排除与耗时汇总（`run/stage-report.md`），测试记录以它为准。
- `page stop --note "原因"`：结束未通过的实验，固定耗时并记录 `STOPPED_NOT_ACCEPTED`。

缺图占位授权、自定义渲染器能力声明和冻结契约复用的细则见 [准备](preparation.md#缺源策略与授权)。
