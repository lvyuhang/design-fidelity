# 独立安装验证记录

验证日期：2026-10-19。环境：macOS arm64、Python 3.12、Flutter 3.47.7，精确 Flutter revision 见 `toolchain.json`。

## 如何验证

从 Git 跟踪文件创建独立克隆，确认没有 `.venv`、Flutter 构建产物、字体或历史 `validation/`。运行项目安装入口，重新安装 Python 依赖、从本机合法来源生成六个字体文件、按锁文件安装 Flutter 依赖并重新构建 Web。

本次复用了本机已经安装的 Flutter SDK 和系统字体来源，没有在全新操作系统上验证 SDK 下载或账号授权。此范围不能描述为“无需环境即可运行”。

## 结果

| 检查 | 实测结果 |
| --- | --- |
| Flutter Web 重新构建 | 通过 |
| 离线快照和素材 SHA-256 | 通过，51 个源节点完整 |
| Flutter 生产入口回归 | 3 项通过，含“提现”标题完整性 |
| 当前实现基线与独立重渲染 | RGB MAE 0.0，阈值 0.1 |
| 接入与配置隔离测试 | 6 项通过 |
| 安卓验收台现有测试 | 80 项通过 |
| 独立 Flutter 预览 | HTTP 200，浏览器确认原稿与 Flutter 双栏显示 |
| 独立安卓验收台演示 | HTTP 200，隔离目录成功导入离线设计快照 |
| 蓝湖 MCP stdio | 握手通过，四个必需扩展接口存在 |

必需 MCP 接口：`lanhu_get_designs`、`lanhu_get_design_overview`、`lanhu_inspect_design_region`、`lanhu_export_design_assets`。

## 可独立复测的命令

```sh
python3 project.py doctor --strict
python3 project.py verify --render
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s android-design-review/tests
python3 project.py check-mcp
python3 project.py start flutter --port 8781
python3 project.py start review --demo --port 8782
```

当前实现基线复现成功，说明安装产物与冻结实现一致；MAE 0.0 不表示与蓝湖原稿零差异，也不替代新页面完整视觉验收。

## 仍需使用者接入

蓝湖项目登录、Codex AI 登录、ADB 真机授权、模拟器镜像与许可、高清视频服务端均依赖使用者环境。本轮没有复制账号凭据、已有验收记录或设备数据，也没有把这些功能标记为已完成真实连通验证。登录后应再执行带项目 URL 的 `check-mcp`、读取设计稿并完成真实设备与 AI 分析检查。
