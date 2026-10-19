# 首次环境接入 / 底层调试

已有环境时跳过。保留完整 scripts/assets；项目用隔离 Python（推荐 3.10+）安装 requirements，不修改系统依赖。MCP 能力见 mcp-evidence.md，日常命令见 session-entrypoint.md。

```sh
python3 -m venv .venv-fidelity
.venv-fidelity/bin/python -m pip install -r "$SKILL_DIR/scripts/requirements.txt"
```

## 自定义渲染器

Flutter 用既有 runner；其他框架需真实渲染器适配，保留预检、收据、冻结基线与日志语义。底层调用：

```sh
python "$SKILL_DIR/scripts/render_with_receipt.py" \
  --contract CONTRACT --candidate OUTPUT.png --receipt RECEIPT.json \
  --cwd APP -- RENDER_COMMAND
python "$SKILL_DIR/scripts/visual_fidelity_gate.py" \
  --contract CONTRACT --candidate result=OUTPUT.png \
  --receipt result=RECEIPT.json --output-dir REPORT_DIR
```

CLI 路径相对启动目录；渲染命令在 cwd 执行，不经 shell 解释；JSON 路径相对契约目录。截图与 candidate 同文件。包装器要求新 PNG、成功退出及前后输入哈希一致；失败使旧收据失效。默认超时 300 秒，--timeout 可调。

底层门禁：0 通过（需看是否带排除），1 视觉失败，2 未验收。diagnostic 不授予验收；不以 || true 忽略失败。契约从审核 spec 编译，不能直接改版本号升级；迁移见 preparation.md。
