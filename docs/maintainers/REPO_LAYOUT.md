# 仓库拆分与大文件建议

当前仓库约 95MB，其中 `flutter_ui_components/`（约 58MB，主要是参考图与实验素材）和 `design_evidence/`（约 32MB，853 个文件）占绝大部分。Skill、工具、实验证据和两个独立工具（安卓验收台、Sketch 插件）共用一个历史，导致克隆慢、版本号容易不一致。以下是建议，本分支没有执行任何移动或删除。

## 建议拆分

| 仓库 | 内容 | 版本 |
|---|---|---|
| `lanhu-flutter-fidelity` | `skills/lanhu-design-fidelity`（含 `lanhu_fidelity` 原语包）、`integrations/lanhu-mcp`、`examples/withdraw-2` | 跟随 Skill 版本（当前 3.0.0） |
| `lanhu-flutter-fidelity-lab` | `flutter_ui_components/`、`design_evidence/`、`tools/`、`validation/` | 实验记录，不发布 |
| `android-design-review` | 安卓验收台（本地已有独立 Git 历史） | 独立 |
| `sketch-layerpilot` | Sketch 插件 | 独立 |

拆分时用 `git filter-repo --path <dir>` 保留各目录历史；Skill 仓库只依赖 `examples/withdraw-2` 作为端到端回归样例。

## 大文件

- 参考图和实验渲染图改用 Git LFS（`*.png` 位于 `flutter_ui_components/assets/reference/`、`design_evidence/**`），或作为 release 附件按哈希下载。
- `design_evidence/backup-*` 中的重复快照（同一 region JSON 出现在多个备份目录）可按内容哈希去重，只保留被 README 引用的版本。

## 版本一致性

Skill 版本只在 `skills/lanhu-design-fidelity/SKILL.md` 的 `metadata.version` 中定义；`toolchain.json`、README 和 GETTING_STARTED 引用它。`tests/test_onboarding.py` 已检查关键入口不含特定用户名路径。
