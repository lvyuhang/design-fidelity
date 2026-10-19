# 接入与执行

需要减少重复命令时使用 [高效执行](efficient-execution.md) 中的 `preflight.py` 与 `run_flutter.py`。下方分步命令仍可用于调试与其他框架适配。

解压 `lanhu-design-fidelity` 文件夹到技能目录。MCP 必须实际提供 `lanhu_get_design_overview`、`lanhu_inspect_design_region`、`lanhu_export_design_assets` 或等价能力；只有旧版分析 HTML 的服务器不能直接满足此流程。不要自动改用户的 MCP 配置。

Python 推荐 3.10+。在开发项目中建立隔离环境；命令里的路径替换为实际位置。`SKILL_DIR` 表示本技能目录，不是项目中的 `scripts`。

```sh
SKILL_DIR="$HOME/.codex/skills/lanhu-design-fidelity"
python3 -m venv .venv-fidelity
.venv-fidelity/bin/python -m pip install -r "$SKILL_DIR/scripts/requirements.txt"
.venv-fidelity/bin/python "$SKILL_DIR/scripts/init_visual_contract.py" \
  --evidence .design-fidelity/page/source-01.json \
  --evidence .design-fidelity/page/source-02.json \
  --reference .design-fidelity/page/reference.png \
  --output .design-fidelity/page/visual-contract.json --name "页面名称"
```

生成 `visual-contract.json` 草稿及 `visual-contract.suggestions.json`。原有输出不覆盖。补全契约时，`pinned_files` 保存参考图、源 JSON、全部切图、字体文件的 SHA-256；`implementation_inputs` 明确列出影响截图的代码、pubspec、lockfile 和截图测试文件。新增依赖文件必须加入列表，脚本不会自动推断完整依赖图。

建议清单中的 `implementation: pending` 必须经人工分类；`vector_data_present` 只说明存在路径字段，不证明完整可绘制。`effect_candidates` 包含有子节点的容器效果，应另配颜色/区域检查，不能只审核叶节点 coverage。小型显著节点按 visual-contract.md 启用 `small_visual`。

```sh
.venv-fidelity/bin/python "$SKILL_DIR/scripts/render_with_receipt.py" \
  --contract .design-fidelity/page/visual-contract.json \
  --candidate .design-fidelity/page/r0/render.png \
  --receipt .design-fidelity/page/r0/render-receipt.json \
  --cwd flutter_app -- flutter test test/design_render_test.dart

.venv-fidelity/bin/python "$SKILL_DIR/scripts/visual_fidelity_gate.py" \
  --contract .design-fidelity/page/visual-contract.json \
  --candidate r0=.design-fidelity/page/r0/render.png \
  --receipt r0=.design-fidelity/page/r0/render-receipt.json \
  --output-dir .design-fidelity/page/r0/report
```

`--candidate`、`--receipt`、`--contract` 相对启动目录解析；渲染命令在 `--cwd` 内执行，测试输出路径需与 candidate 指向同一文件。JSON 内文件路径一律相对契约目录。截图命令不经过 shell 解释；需要管道时先写项目脚本再运行。

收据包装器要求 PNG 在本次命令中产生或重写，命令成功且输入哈希前后不变。失败时使收据失效，防止继续使用上一轮成功结果。默认命令超时 300 秒，可用 `--timeout` 调整。

正式 CI 顺序：项目检查 → 截图包装器 → 视觉门禁。逐步执行并立即处理非零退出码；不要添加 `|| true` 或诊断模式。退出码 0 可能伴随 `PASS_WITH_EXCLUSIONS`，部署要求无排除时还应检查报告的 `status == PASS`。

模板中的空值和待替换节点必须补齐。v1 升级要重新生成草稿，再迁移已审阅的检查，不直接把版本号改成 2。
