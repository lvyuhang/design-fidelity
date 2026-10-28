# 研发使用指南

把蓝湖或 Figma 设计稿还原成 Flutter（或 React）页面，并自动检查还原度。本文只讲研发日常需要的部分；工具的测试、实验和维护资料在 `docs/maintainers/`，不需要读。

整体分工：**AI 编码代理（Codex、Claude Code 等）负责取设计数据、生成代码、跑检查；你负责业务逻辑、数据接入、交互，以及审核结果。**

## 一、每台电脑一次（约 10 分钟）

需要 macOS、Python 3.11+、Flutter，以及一个支持 MCP 和 Skill 的 AI 编码工具。

**1. 获取工具（只下载需要的目录）**

```sh
git clone --filter=blob:none --sparse https://github.com/lvyuhang/lanhu-flutter-fidelity.git ~/lanhu-flutter-fidelity
cd ~/lanhu-flutter-fidelity
git sparse-checkout set skills/design-fidelity integrations
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
python3 skills/design-fidelity/scripts/install_app.py skill --target ~/.codex/skills    # Codex
python3 skills/design-fidelity/scripts/install_app.py skill --target ~/.claude/skills   # Claude Code
```

安装的副本不包含测试和维护资料。工具更新后执行 `git pull` 再重新运行这一步即可，旧版本会自动备份。

## 二、每个 App 一次

在 App 仓库根目录执行：

```sh
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py init --app . \
  --python ~/lanhu-flutter-fidelity/.venv/bin/python
flutter pub get
(cd packages/design_fidelity && flutter test)    # 确认渲染原语在当前 Flutter 版本下正常；升级 Flutter 后再跑一次
```

它会做三件事：

- 把渲染原语包复制到 `packages/design_fidelity`，并在 `pubspec.yaml` 中加入依赖；
- 创建 `fidelity/` 工作区：`fidelity/page` 命令、`font-map.json`、`.gitignore`；
- 写入本机路径到 `fidelity/.local.env`（已被忽略，不会提交）。

**配置字体**：设计稿通常用苹方。在 App 根目录执行：

```sh
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py fonts --app .
# Android 想用自带的授权字体时加：--android NotoSansSC（需在 pubspec.yaml 中声明该 family）
```

它从本机 macOS 提取苹方到 `~/.design-fidelity/fonts/`（在 App 仓库之外），并写入 `fidelity/font-map.json`。每个字体有两种用途：

- **还原度检查**：测试时从磁盘加载苹方，和设计稿逐像素对比。字体文件**不会打进 App**；
- **上线字体**：iOS 用系统字体（本身就是苹方）；Android 默认用系统中文字体，或者用 `--android` 指定的字体。

苹方的授权通常只覆盖 Apple 平台，不要把它声明进 `pubspec.yaml`。设计稿还用了其他字体时，`prepare` 会报 `font_mapping_missing` 并列出 `字体名@字重`，按同样格式手动补到 `font-map.json`：

```json
"DINAlternate-Bold@700": {"path": "~/.design-fidelity/fonts/DINAlternate-Bold.ttf",
                          "runtime_family": "DesignDIN", "ios": null, "android": "AppNumber"}
```

`ios`、`android` 写 `null` 表示用系统字体，写名字表示用 `pubspec.yaml` 中声明的 family。还原度检查始终按设计稿字体进行；Android 换用其他字体后字宽会有细微差异，上线前建议在真机上看一遍文字较密的区域。

团队里只需一人执行 `init` 和 `fonts` 并提交，其他人拉代码后在自己电脑上再执行一次 `init` 和 `fonts`：前者生成自己的 `.local.env`，后者在自己电脑上提取苹方（已有的映射不会被覆盖）。

## 三、每个页面

**1. 创建页面工作区**

```sh
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py page --app . --name order_detail --title 订单详情
```

**2. 把任务交给 AI**（照此填写即可）

> 使用 `$design-fidelity` 把蓝湖设计 `<设计链接>` 实现为订单详情页。页面配置在 `fidelity/order_detail/page.json`，命令用 `fidelity/page order_detail <命令>`，取证结果保存到 `fidelity/order_detail/evidence/`。业务要求：订单数据来自 `OrderRepository.detail(id)`；点击"确认收货"调用 `onConfirm`；页面文件写在 `lib/pages/order_detail_page.dart`。

AI 会依次执行：`start → 取证 → prepare → generate → 组合页面 → spec → accept`。其中代码和检查由工具生成，AI 主要负责组合页面、接入数据和修复失败项。

**设计稿在 Figma 时**：不需要蓝湖 MCP 和 Cookie，改为配置自己的 Figma 个人访问令牌（Figma → Settings → Security → Generate new token，权限勾选 File content 只读）。令牌写进 App 仓库的 `fidelity/.local.env`（已被忽略，不会提交）：

```sh
echo 'FIGMA_TOKEN=figd_你的令牌' >> fidelity/.local.env
```

交给 AI 时把"蓝湖设计 `<设计链接>`"换成"Figma 画板 `<链接>`"（在 Figma 中右键画板 → Copy link，链接里要有 `node-id`）。AI 会用 `figma_evidence.py` 取证，之后的步骤完全相同。

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
| lint `L001`–`L013` | 页面代码用了会降低还原度的写法（框架图标、硬编码颜色、`BoxShadow`、`Text(` 等） | 改用 `<Page>Tokens` 和 `SourceText`、`SourceBox` 等原语；确需例外写 `// fidelity-lint: allow Lxxx 原因` |
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

## 五、iOS 与 Android 适配

生成的页面会自动处理两个平台的差异，研发不需要手写适配代码：

| 差异 | 生成页面的处理 |
|---|---|
| 状态栏高度（设计稿 44；灵动岛 iPhone 约 59；Android 约 24） | 内容按设备实际安全区上下移动，状态栏区域不绘制 |
| 底部 Home Indicator / 导航条 | 底部按钮、底部导航自动贴在底部安全区之上 |
| 屏幕高度（iPhone SE 667 到 Pro Max 932） | 矮屏时主体内容可滚动，底部按钮保持固定；高屏时中间留出空间 |
| 字体 | 按 `font-map.json` 的 `ios` / `android` 配置分别使用 |
| 无障碍字体放大 | 保留系统字体缩放，检查时覆盖 1.3 倍 |

**使用要求**：生成的 `<Page>Scene` 是整页组件，直接作为 `Scaffold` 的 `body`，**不要再包 `SafeArea`，也不要加 `AppBar`**，否则安全区会被重复计算。只把它嵌在别的页面里预览时，传 `adaptSafeArea: false`。

验收时会在 iPhone SE、iPhone 15、iPhone 15 Pro Max、Android 360×800、Android 412×915 五种屏幕下，分别按 1.0 倍和 1.3 倍字体检查：布局报错、横向越界、矮屏内容被截断且不能滚动、文字进入状态栏、底部按钮压到 Home Indicator，这些都会阻断验收。

## 六、Web（React）项目

流程与 Flutter 相同，`init` 检测到 `package.json` 会自动切到 React：

```sh
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py init --app . \
  --python ~/lanhu-flutter-fidelity/.venv/bin/python
npm install && npm install -D esbuild playwright && npx playwright install chromium
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py fonts --app .
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py page --app . --name order_detail
```

| | Flutter | React |
|---|---|---|
| 生成文件 | `lib/fidelity/<page>.g.dart` | `src/fidelity/<page>.g.tsx` |
| 素材 | `assets/design/<page>/`（写入 pubspec） | `src/assets/design/<page>/`（由生成文件 import） |
| 渲染入口 | `test/fidelity/<page>_test.dart` | `fidelity/<page>/render.tsx` |
| 渲染器 | `flutter test` | Playwright Chromium |
| lint 规则 | `L001`–`L013` | `W001`–`W011`（颜色字面量、手写字号、`box-shadow`、`border`、`<img>`、图标库等） |

页面写法：把 `<Page>Scene` 放进满高容器（如 `height: 100dvh`），用 `overrides` / `onTap` 接数据和交互，不要改 `.g.tsx`。移动端 Safari 需要 `viewport-fit=cover` 才能拿到安全区。Next.js 需要把 `@design-fidelity/react` 加入 `transpilePackages`。详细说明见 Skill 的 `references/web-rendering.md`。

提交时额外提交 `fidelity/<page>/render.tsx`、`scene.g.json` 和 `support/`；`packages/design-fidelity-react` 与 Flutter 的原语包一样随仓库提交。

## 七、原生 Android / iOS 项目（预览）

Compose 与 SwiftUI 的生成器、原语和渲染测试模板已提供，但还没有在真机工具链上验证过。接入方法与第一个页面的验证清单见 Skill 的 `references/native-rendering.md`。简要命令：

```sh
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py init --app .
python3 ~/lanhu-flutter-fidelity/skills/design-fidelity/scripts/install_app.py page --app . --name order_detail \
  --kotlin-package com.example.shop.fidelity      # Android；iOS 改为 --scheme Shop
```

背景模糊在这两个目标上不绘制，相关页面需要切图或写明排除原因。

## 八、目前的限制

- 还原度检查在 Mac 的测试渲染器上进行；iOS 真机用 Metal、Android 用 Vulkan/OpenGL 渲染，模糊、阴影和文字抗锯齿可能有细微差别，上线前建议用模拟器或真机截图核对。
- 底部按钮、底部导航是否"贴底"由生成器根据位置自动判断（见报告 `layout.footer`），判断不对时用 override 调整。
- 页面顶部导航栏会随内容一起滚动；需要固定导航栏时，在页面代码中把它拆出来放进 `Column` 顶部。
- 只支持线性渐变；旋转、径向渐变等会在生成报告中标为 unsupported，需要在页面代码中处理。

## 常见问题

- **prepare 报 `font_mapping_missing`**：按报告补全 `font-map.json`。
- **prepare 报 `missing_glyphs`**：映射的字体缺字，换成完整字体。
- **check-mcp 失败**：Cookie 过期，重新从浏览器复制。
- **契约校验报字体哈希变化**：不同 macOS 版本的苹方文件可能不同。团队统一在同一 macOS 大版本上做验收；换机器后若哈希不同，需要重新建立该页面的验收基线。
- **设计稿更新了**：重新取证，再 `prepare` 和 `generate`，页面代码不需要重写。注意设计师如果删除或重建了图层，节点 ID 会变化，`overrides` 和 `onTap` 里对应的 ID 要同步更新。
