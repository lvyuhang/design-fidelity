# 协作开发

1. 克隆仓库，按 README 安装本机环境；各自使用独立的数据目录和蓝湖登录。
2. 从 main 创建功能分支，修改后运行 `python -m unittest discover -s tests`。
3. 前端改动还需运行 `node --check static/app.js`（以及其他修改的 JS），并在浏览器验证。
4. 提交 Pull Request，说明问题、改动和验证结果；由另一位同事 review 后合并。

不要提交 APK、蓝湖原图、验收截图、标注数据、登录配置、SDK 或运行日志。
本项目服务仅监听本机；GitHub 用于源码协作，不提供多人共享的在线验收数据库。

## 目录

- `server.py`：HTTP 服务、设计及截图记录、任务调度。
- `static/`：工作台页面、样式和交互。
- `ai_review.py`：本机 Codex 视觉分析与输出校验。
- `capture.py` / `preview.py` / `scrcpy_stream.py`：ADB 和实时预览。
- `virtual_devices.py` / `sdk_runtime.py` / `device_catalog.py`：模拟器与设备模板。
- `lanhu_bridge.py`：蓝湖 MCP 连接。
- `tests/`：单元和服务测试，无需真实设备或 AI 账号。
- `macos/`：可选桌面客户端构建。
