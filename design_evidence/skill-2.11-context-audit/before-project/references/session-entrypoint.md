# 配置入口：一次配置，沿用证据与验收

此入口串联现有脚本，减少参数错误和模型往返，不自动生成/批准页面。使用已安装 requirements.txt 的同一个 Python。路径均相对于配置文件；`test` 与 `analyze` 相对于 Flutter app。

复制 `assets/page-session.example.json`，在当前任务证据目录填好 name、run_dir 后先 start。其余路径可在取证后填好；每次操作记录当时配置哈希。

```sh
python "$SKILL_DIR/scripts/page_session.py" --config page.json start
python "$SKILL_DIR/scripts/page_session.py" --config page.json prepare
# 审核 prepare 输出，实现页面，写 reviewed-spec.json。
python "$SKILL_DIR/scripts/page_session.py" --config page.json compile
python "$SKILL_DIR/scripts/page_session.py" --config page.json validate --note "初版：说明证据和实现范围"
# 根据失败 ROI 批量修正后重复 validate，复用 contract。
python "$SKILL_DIR/scripts/page_session.py" --config page.json validate --note "修正图文中心与底部阴影" --build
# 已查看最终原稿/实现并列图，运行项目检查，打开可运行预览后：
python "$SKILL_DIR/scripts/page_session.py" --config page.json finish --note "视觉复查结果、缺图范围、预览地址及验证结果"
```

`prepare` 合并完整源证据、资源与字体，再生成未批准的契约草稿；有输入问题时保留报告并退出 2，不自动编造补值。`compile` 调既有编译器，spec/contract 要在同目录，拒绝覆盖冻结 contract。`validate` 用既有 runner 跑预检、收据、门禁及已配置的 Dart 分析，自动分配新目录；仅最终需要时加 build。stdout 提供摘要，详细命令输出保留在日志里。

完整页面默认 `scope: page`。只检查局部节点必须明确 `provided_nodes`，否则在渲染前拒绝；局部检查不能算全页验收。`finish` 需要最近一次 validate 成功及非空复查记录。这是责任声明，不证明记录者真的看过截图，仍由执行者完成复查与预览。

`status` 刷新全程与逐轮摘要。start 不允许重置同一任务；失败事件保留。进程中断后的 lock 必须确认进程已结束才清理；保留未完成事件，不补造耗时。工具维护、SDK 安装和等待都计在 start 后墙钟里；未记录的阶段不硬分摊。配置入口无法取得模型 token，必须从实际会话使用记录补入独立实验记录，不能估算后当作实测。

既有 2.9 日志缺少冻结 policy，升级后用旧截图作 diagnostic；为检测工具校准建立明确关联的新任务。不要把校准时间、阈值调整或合成夹具成绩宣称为新页面开发提速。每次真实效率实验记录任务、模型、复杂度、素材缺口、首次/重复实现、全程起止、实现修正次数、验收改动次数、最终覆盖与视觉复查结论。
