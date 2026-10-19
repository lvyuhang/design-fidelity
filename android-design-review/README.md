# 安卓设计验收台

对照蓝湖原图验收 Android 真机或模拟器画面：实时预览、截图记录、可编辑打点标注、Codex 视觉分析和验收包导出。

## 本地启动（推荐 macOS）

需要 Python 3.11+，使用真机预览时需安装 Android Platform-Tools 并配置 `adb`。设备上开启 USB 调试并允许本机。

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env.local
./start.command
```

打开 http://127.0.0.1:8769/ 。端口冲突可执行 `./start.command --port 8770`。不要直接打开 `static/index.html`。

高清视频预览还需要 scrcpy 服务端：

```sh
mkdir -p .tools
curl -fL -o .tools/scrcpy-server-v4.1 https://github.com/Genymobile/scrcpy/releases/download/v4.1/scrcpy-server-v4.1
```

每位同事独立安装依赖并关联自己的蓝湖项目。仓库不包含业务设计、APK、截图或标注。

## 蓝湖连接

配置支持设计概览、资源读取和项目分组的蓝湖 MCP stdio 服务，登录信息由该服务管理。在 `.env.local` 配置 `LANHU_MCP_LAUNCHER` 和 `LANHU_CLIENT_PYTHON`。客户端 Python 需安装 `mcp` 和 `Pillow`。通过工作台左侧「添加项目」粘贴蓝湖项目链接。

`lanhu_bridge.py` 是使用中的连接入口；`sync_project.py` 和 `fetch_reference.py` 是历史取证辅助脚本，不是启动依赖。

## 功能

- 当前视觉走查规则见 [REVIEW_RULES.md](REVIEW_RULES.md)，该文件直接进入分析提示，并参与规则版本指纹。当前按单份设计稿工作，不要求补状态稿；组件对应、状态和适配判断依据随分析结果保存，供统一复核使用。
- 左侧选择蓝湖项目和分组；过滤交互说明及非界面素材。
- 原稿与实机 / 虚拟机 / 截图对照，截图记录按设计稿隔离。
- 点击截图打点，气泡描述、锚点和气泡位置可编辑并自动保存。
- AI 分析使用本机已登录的 Codex CLI，无需把 API Key 写入源码。模型选项来自本机 Codex 缓存中支持图片输入的可见模型。
- AI 按组件生成候选，再用同一所选模型结合完整画面、截图时的密度/字体缩放等环境统一复核。业务数据、合法状态和环境差异不打点；缺乏独立样式证据的候选也不交给人工兜底。蓝色提示仅保留有具体核对动作的少量状态疑点。
- 不能仅凭图标颜色变化就断定激活状态不同：共同功能控件有明确外观差异、但缺少额外状态证据时，保留可操作的蓝色核对点。组件边界的分割线、阴影强度/扩散和模糊过渡也纳入检查；只描述可见差异，不臆测具体阴影参数或代码实现。
- 分区完成会更新图上进度，复核结束后才生成标注。全图及局部分析都经过复核；有候选时增加一次模型请求和相应耗时/额度。没有源码或业务规格时，图片不能证明隐藏业务规则；未报问题不表示全页通过。
- AI 后台任务最多 3 个并行，其余排队。任务浮层可折叠、跳转截图；结果为待确认建议，不代表全面验收通过。需要保持本机服务运行。
- 每次开始分析都会清除本记录上一轮 AI 标注和去重状态，保留手动标注，并重新调用模型。旧 AI 结果会暂存；失败或页面不匹配时恢复，服务重启也会恢复尚未提交的旧结果。正常完成后用本轮结果替换，零条结果也会清空旧 AI 标注。
- 虚拟机支持 APK 上传、不同逻辑宽度和设备屏幕模板。首次下载 Android SDK / 镜像需接受对应许可；模板不等同于厂商 ROM。
- 导出验收包含问题、原始截图及设计证据。

## 数据与配置

默认数据目录为 `.data/`；`REVIEW_DATA_DIR` 可指定其他位置。数据只在本机保存，备份时先停止服务并复制完整数据目录。macOS 客户端默认使用 `~/Library/Application Support/设计验收/data`。

常用环境变量（在 `.env.local` 中 `export`）：

| 变量 | 作用 |
| --- | --- |
| REVIEW_DATA_DIR | 验收数据目录 |
| REVIEW_PYTHON | 启动 Python 路径 |
| REVIEW_ADB | ADB 可执行文件 |
| REVIEW_ANDROID_SDK | 专用 Android SDK 目录 |
| LANHU_MCP_LAUNCHER | 蓝湖 MCP 启动脚本 |
| LANHU_CLIENT_PYTHON | 安装了 mcp 和 Pillow 的 Python |

登录、SDK、模型访问权限由每位开发者自行配置。GitHub 用于源码迭代，不会自动同步本机验收记录。

## 验证与贡献

```sh
.venv/bin/python -m unittest discover -s tests
# 安装 Node.js 后进行前端语法检查
for file in static/*.js; do node --check "$file"; done
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。推送和 Pull Request 会运行 GitHub Actions 测试。

## macOS 客户端（可选）

`macos/` 提供 WKWebView 客户端源码。浏览器版本是默认开发入口。构建脚本需要 Xcode Command Line Tools、PyInstaller、ADB 和 scrcpy 服务端。分发前需按团队要求配置签名和公证；不要把业务数据作为安装包种子发布。
