# 提现-2：离线接入验证样例

`source.json` 为固定蓝湖 MCP 快照的51个原始节点，`reference.png` 是同版本原稿；`assets/` 为经过 SHA256 校验的三个原始切图。账号凭据不在样例中。

`baseline-production.png` 是本机修复标题裁切后、使用正式 ComponentLab Theme 的 Flutter 测试引擎输出。它用于检查新安装是否复现现有实现，不是新机器的独立视觉验收，也不是 Android 真机截图。当前样例仍有字体/插画几何等视觉差异，不能从与实现基线一致推出与设计稿完全一致。

执行 `python3 project.py verify --render` 会核对所有样例字节和节点数量、运行生产入口的三项测试，再比较冻结的实现基线。结果写入忽略的 `.local/verification/`。原稿与可交互 Flutter 页面可通过 `python3 project.py start flutter` 并列查看。

首次冻结的复现阈值为 RGB MAE 0.10（0—255），仅适用于 toolchain.json 固定的 macOS arm64/Flutter 环境。不得为使新安装通过而修改基线或阈值；不兼容环境应单独记录。
