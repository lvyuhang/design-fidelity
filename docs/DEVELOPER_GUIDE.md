# 研发使用指南

把蓝湖设计稿还原成 Flutter 页面，并自动检查还原度。本文只讲研发日常需要的部分；工具的测试、实验和维护资料在 `docs/maintainers/`，不需要读。

整体分工：**AI 编码代理（Codex、Claude Code 等）负责取设计数据、生成代码、跑检查；你负责业务逻辑、数据接入、交互，以及审核结果。**

## 一、每台电脑一次（约 10 分钟）

需要 macOS、Python 3.11+、Flutter，以及一个支持 MCP 和 Skill 的 AI 编码工具。

**1. 获取工具（只下载需要的目录）**

```sh
git clone --filter=blob:none --sparse https://github.com/lvyuhang/lanhu-flutter-fidelity.git ~/lanhu-flutter-fidelity
cd ~/lanhu-flutter-fidelity
git sparse-checkout set skills/lanhu-design-fidelity integrations
```

这样不会下载样例页面、实验数据、安卓验收台等与日常开发无关的内容。

**2. 安装依赖和蓝湖 MCP 服务**

```sh
./setup.command --profile skill
```

**3. 配置自己的蓝湖登录**

```sh
cp .env.example .env.local
# 编辑 .env.local，填入 LANHU_COOKIE=你自己的蓝湖 Cookie（不要发给别人，也不要提交）
python3 project.py check-mcp --url '任一你有权限的蓝湖项目链接'
```

能读取到项目就说明连通了。

**4. 在 AI 工具中注册蓝湖 MCP**

Codex（`~/.codex/config.toml`）：

```toml
[mcp_servers.lanhu]
command = "/bin/bash"
args = ["/Users/<你>/lanhu-flutter-fidelity/integrations/run-lanhu-mcp.sh"]
```

Claude Code：

```sh
claude mcp add lanhu -- /bin/bash ~/lanhu-flutter-fidelity/integrations/run-lanhu-mcp.sh
```

**5. 安装 Skill**

```sh
python3 skills/lanhu-design-fidelity/scripts/install_app.py skill --target ~/.codex/skills    # Codex
python3 skills/lanhu-design-fidelity/scripts/install_app.py skill --target ~/.claude/skills   # Claude Code
```

安装的副本不包含测试和维护资料。工具更新后执行 `git pull` 再重新运行这一步即可，旧版本会自动备份。

## 二、每个 App 一次

在 App 仓库根目录执行：

```sh
python3 ~/lanhu-flutter-fidelity/skills/lanhu-design-fidelity/scripts/install_app.py init --app . \
  --python ~/lanhu-flutter-fidelity/.venv/bin/python
flutter pub get
(cd packages/lanhu_fidelity && flutter test)    # 确认渲染原语在当前 Flutter 版本下正常；升级 Flutter 后再跑一次
```

它会做三件事：

- 把渲染原语包复制到 `packages/lanhu_fidelity`，并在 `pubspec.yaml` 中加入依赖；
- 创建 `fidelity/` 工作区：`fidelity/page` 命令、`font-map.json`、`.gitignore`；
- 写入本机路径到 `fidelity/.local.env`（已被忽略，不会提交）。

**配置字体**：在 `fidelity/font-map.json` 中把设计稿字体映射到 App 已声明的字体文件。不知道需要哪些键时，先跑一次 `prepare`，报告会列出缺少的 `字体名@字重`：

```json
{"fonts": {
  "PingFangSC-Regular@400":  {"path": "../assets/fonts/YourSans-Regular.otf",  "runtime_family": "YourSans"},
  "PingFangSC-Semibold@600": {"path": "../assets/fonts/YourSans-Semibold.otf", "runtime_family": "YourSans"}
}}
```

`path` 相对 `font-map.json`，`runtime_family` 要和 `pubspec.yaml` 中的 family 一致。苹方的授权通常只覆盖 Apple 平台，不要把它打进 Android 包，用法请先和法务确认。

团队里只需一人执行 `init` 并提交，其他人拉代码后在自己电脑上再执行一次 `init`，生成自己的 `.local.env`。

## 三、每个页面

**1. 创建页面工作区**

```sh
python3 ~/lanhu-flutter-fidelity/skills/lanhu-design-fidelity/scripts/install_app.py page --app . --name order_detail --title 订单详情
```

**2. 把任务交给 AI**（照此填写即可）

> 使用 `$lanhu-design-fidelity` 把蓝湖设计 `<设计链接>` 实现为订单详情页。页面配置在 `fidelity/order_detail/page.json`，命令用 `fidelity/page order_detail <命令>`，取证结果保存到 `fidelity/order_detail/evidence/`。业务要求：订单数据来自 `OrderRepository.detail(id)`；点击"确认收货"调用 `onConfirm`；页面文件写在 `lib/pages/order_detail_page.dart`。

AI 会依次执行：`start → 取证 → prepare → generate → 组合页面 → spec → accept`。其中代码和检查由工具生成，AI 主要负责组合页面、接入数据和修复失败项。

**3. 你需要审核的四件事**

| 何时 | 看什么 | 要点 |
|---|---|---|
| `generate` 之后 | `lib/fidelity/<page>.codegen.json` 里的 `unsupported` 和 `issues` | 缺素材的节点会显示"设计素材未切图"占位，找设计补切图 |
| 页面代码 | `lib/pages/<page>_page.dart` | 只组合生成的 `<Page>Scene`：`overrides` 换成业务组件和动态数据，`onTap` 接交互；**不要改 `.g.dart`** |
| `spec` 之后 | `fidelity/<page>/reviewed-spec.json` 中标 `auto:` 的检查 | 一般不用改；阈值一旦开始验收就冻结，不能为了通过去调大 |
| `accept` 之后 | `fidelity/page <page> report` 生成的 `run/stage-report.md` | 阻断项要清零；观察项（如大字体下的文字重叠）酌情处理 |

**4. 常见失败怎么处理**

| 报告里看到 | 含义 | 处理 |
|---|---|---|
| lint `L001`–`L013` | 页面代码用了会降低还原度的写法（框架图标、硬编码颜色、`BoxShadow`、`Text(` 等） | 改用 `<Page>Tokens` 和 `SourceText`、`SourceBox` 等原语；确需例外写 `// lanhu-lint: allow Lxxx 原因` |
| `L011` | 生成文件被改过 | 撤销改动，在页面代码里用 override 实现 |
| 几何失败 `top +2.00px` 等 | 某个节点偏了 | 按偏差修布局；文字行高偏差先查字体映射 |
| `horizontal_overflow` / `exceptions` | 窄屏或大字体下越界、报错 | 把该区域改成 Row/Column + Flexible，或允许换行 |
| 像素或特征失败 | 颜色、阴影、素材不一致 | 对照报告里的区域检查，不要调阈值 |

**5. 完成**：门禁通过后执行 `fidelity/page <page> finish --note "复查结论"`，然后提交代码。

### 提交哪些文件

| 提交 | 不提交 |
|---|---|
| `lib/fidelity/<page>.g.dart` 和 `<page>.codegen.json` | `fidelity/<page>/run/`（每次运行的截图和报告） |
| `test/fidelity/` 下的测试 | `fidelity/.local.env` |
| `assets/lanhu/<page>/` | `.env.local`、Cookie |
| `fidelity/<page>/` 下的 `page.json`、`evidence/`、`reviewed-spec.json`、`visual-contract.json` | |
| 你的页面代码 | |

`fidelity/.gitignore` 已经配置好。

## 四、不用 AI 时

所有步骤都可以手动执行：`fidelity/page <page> start|prepare|generate|spec|accept|report|finish`。取证这一步需要调用蓝湖 MCP，手动操作比较繁琐，建议交给 AI。

## 五、目前的限制

- **安全区**：生成页面按设计稿画布摆放（状态栏按 44 计算）。灵动岛 iPhone 和 Android 的状态栏高度不同，顶部可能重叠或留白。适配完成前，请在页面代码中按 `MediaQuery.paddingOf(context).top - 44` 调整顶部。
- **屏幕高度**：生成页面固定为设计稿高度。iPhone SE 等矮屏上，需要把主体内容放进 `SingleChildScrollView`。
- **多尺寸检查**目前只覆盖 360 和 414 宽；还原度检查在 Mac 的测试渲染器上进行，真机效果建议再用模拟器或真机截图核对。
- 只支持线性渐变；旋转、径向渐变等会在生成报告中标为 unsupported，需要在页面代码中处理。

## 常见问题

- **prepare 报 `font_mapping_missing`**：按报告补全 `font-map.json`。
- **prepare 报 `missing_glyphs`**：映射的字体缺字，换成完整字体。
- **check-mcp 失败**：Cookie 过期，重新从浏览器复制。
- **设计稿更新了**：重新取证，再 `prepare` 和 `generate`，页面代码不需要重写。注意设计师如果删除或重建了图层，节点 ID 会变化，`overrides` 和 `onTap` 里对应的 ID 要同步更新。
