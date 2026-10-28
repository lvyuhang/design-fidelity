# 完整仓库安装（维护者 / 安卓验收台）

> 只在 App 中还原页面的研发同学请看 [研发使用指南](DEVELOPER_GUIDE.md)，不需要本文的完整安装。

## 运行前

需要 Git、Python 3.11+、Flutter 3.47.7（精确 revision 见 `toolchain.json`）。Flutter SDK 安装见 [官方安装说明](https://docs.flutter.dev/install/manual)。这是本次已验证环境；其他系统尚未做同品质验证。

macOS 的苹方和 Arial Unicode 字体由脚本从本机已有合法来源准备，绝不上传字体或从同事机器复制授权文件。缺少字体时，安装会明确停止并提示文件名；可用 `--font-dir /path/to/fonts` 提供 `pubspec.yaml` 所需文件，或指定 `--pingfang`、`--arial-unicode`。不做静默字体替换。

## 第一次安装和预览

```sh
git clone <本仓库地址> lanhu-flutter-fidelity
cd lanhu-flutter-fidelity
./setup.command --profile all --with-mcp --flutter-sdk /path/to/flutter
python3 project.py doctor --strict
python3 project.py verify --render
python3 project.py start flutter
```

默认预览为 http://127.0.0.1:8767/?case=withdraw-2-skill2186 ，左侧原稿、右侧真实 Flutter Web，逻辑宽375。不需要蓝湖账号即可查看离线样例。端口被占用时加 `--port 8781`；脚本不会停止原服务。

如果 Python 不在 PATH：

```sh
DESIGN_FIDELITY_PYTHON=/path/to/python3.12 ./setup.command --profile all --flutter-sdk /path/to/flutter
```

只需要 Flutter 时使用 `--profile flutter`；只需要安卓验收台使用 `--profile review`。所有依赖装入当前仓库 `.venv`，不复用其他项目虚拟环境。

## 安卓验收台

```sh
python3 project.py start review --demo --port 8782
```

`--demo` 仅导入打包的设计快照，使用独立 `.local/review-demo` 数据目录，没有任何人的验收记录。可在界面导入自己的截图验证对比和标注。常规工作使用 `python3 project.py start review`，数据默认写入 `.local/review-data`；显式 `REVIEW_DATA_DIR` 优先。

## 蓝湖、设备与 AI

1. `cp .env.example .env.local`，填入自己的 `LANHU_COOKIE`，以及需要时的 `REVIEW_ADB`、`REVIEW_DATA_DIR`。已用 `--with-mcp` 安装时启动器自动配置，只有使用外部服务才需填写 `LANHU_MCP_LAUNCHER`。设置值不会上传。
2. `--with-mcp` 安装 `integrations/lanhu-mcp/` 中打包的扩展版服务源码（MIT许可及上游出处随源码保留）。其 `.env`、Cookie、缓存及浏览器资料没有打包。可在根目录 `.env.local` 中配置自己的 `LANHU_COOKIE`，默认启动器读取本仓库环境；也可配置外部 `LANHU_MCP_LAUNCHER`。先执行 `python3 project.py check-mcp`，实际确认 stdio 与扩展接口；再用 `python3 project.py check-mcp --url '你的蓝湖项目链接'` 验证登录后项目读取。不要把 Cookie 发到对话或提交 Git。
3. 在验收台粘贴蓝湖项目链接，实际取回画板才算连通。`doctor` 的“已配置”不表示已验证登录。
4. 真机需 ADB、USB调试和用户本人授权；高清视频另需 scrcpy-server，详见子项目 README。首次模拟器镜像安装与许可由使用者确认，不随基本安装自动下载。
5. AI 使用本机 Codex CLI 与使用者自己的登录。`codex login` 后执行真实分析再确认，不复制已有机器的 Codex 登录文件。

## 安装 Skill

仓库内 `skills/design-fidelity` 为 3.0.0 候选版。在 Codex 里使用前，复制到自己的 `$CODEX_HOME/skills/design-fidelity`；目标已存在时先比较版本、保留备份。源码更新不会自动覆盖个人 Skill。

在要接入的 Flutter 项目中：

```sh
cp -R skills/design-fidelity/assets/flutter/design_fidelity <app>/packages/
# pubspec.yaml: dependencies: design_fidelity: {path: packages/design_fidelity}
(cd <app>/packages/design_fidelity && flutter pub get && flutter test)
```

之后按 Skill 的 `references/session-entrypoint.md` 执行 `start → prepare → generate → spec → accept`。

## 更新与验证

MCP 安装使用 `constraints-mcp.txt` 冻结本次验证过的依赖版本。每次安装另将实际解析结果存于本机 `.local/python-resolved.txt`。安装验证范围及结果见 [验证记录](maintainers/INSTALL_VERIFICATION.md)。

更新源码后，重新运行 setup 安装缺失依赖；`project.py start flutter --build` 重新构建。`verify --render` 比较的是打包实现基线，不能代替新设计页面的 Skill 验收。离线样例和代码的测试结果不代表蓝湖、设备、模型已连通。

历史实验在旧 README 的下半部保留。`validation/`、历史构建和个人数据不属于首次接入依赖；个别历史研究脚本仍引用旧工件，不属于此入口的支持范围。
