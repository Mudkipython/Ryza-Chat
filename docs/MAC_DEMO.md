# Apple Silicon 本地运行指南

本分支基于上游 v1.2.23，主要验收机器为 M4 MacBook Air / 24GB。没有修改原版主界面 HTML、CSS 和图标；设置页增加的本地选项由原有 JavaScript 渲染。

## 准备与构建

1. 安装 Node.js/npm、uv 和可用的网络连接。建议至少预留 25GB 空间；下载缓存与可选组件会进一步占用空间。
2. 在根目录执行 `bash scripts/prepare_mac_demo.command`，创建 Python 3.12 环境，下载固定版本的 llama.cpp、Qwen 对话/TTS/ASR 模型并恢复角色媒体。
3. 需要中文情感音色时执行 `bash scripts/prepare_cosyvoice.command`，额外创建隔离环境及下载 CosyVoice 与 S3Tokenizer。
4. 执行 `bash scripts/build_mac_demo.command`，然后 `bash scripts/start_mac_demo.command`。

准备脚本会下载上游发行包来恢复资源。源包不包含这些媒体或参考录音；也可以先用 `python3 scripts/restore_media.py /path/to/compatible.apk` 从已取得的资源恢复。固定参考片段路径和文本在 `config/ryza-voice-reference.json` 中，可按已获授权的参考材料自行调整。

主模型来源、大小、SHA256、上下文和采样参数在 `desktop/model-manifest.json`。基础准备创建 `.runtime/voice-venv`；CosyVoice 独立使用 `.runtime/cosyvoice-venv`，防止不同 MLX Audio 包冲突。GPT-SoVITS 为独立可选试验，不是基础安装所需；相关脚本保留但不默认下载、训练或启用。

## 语言与语音

- 新建配置默认为中文显示、日语配音；已有存档保留个人选择。
- 设置 → 语音合成中选择语言，并分别设置普通/ASMR 音色与强度。
- 日语推荐当前已验证的 Qwen3-TTS；中文可选择准备好的 CosyVoice 实验音色。Qwen 不承诺额外情绪控制，ASMR 选项也不保证双耳录音或真正耳语。
- 语音按钮支持原有监听方式；长按超过约 250ms 手动录音、松开转写，最多约 25 秒。默认填入输入框再手动发送。首次使用需允许麦克风权限。
- 不会在启动时自动录音。语音输入、翻译与合成可以取消，迟到结果会丢弃；取消 HTTP 不保证立即终止服务端已开始的计算。

首次识别/配音有冷启动等待，24GB 机器同时驻留多个模型时仍可能出现内存压力。中文情感和日语音色的优劣需要实际试听，ASR 回读通过不代表演绎自然。

## 对话、动作与记忆

文字逐步显示；生成期间再次点击发送或按 Escape 取消。半句与取消本轮不提交到聊天/长期记忆。明显语言不符最多进行一次纯文本修正，然后才应用状态与配音。译文可以随聊天记录复用。

自然动作保留独立手臂、躯干、腿部和随机姿势，通过轨道与过渡协调减少竞争；没有替换骨骼和动画。长期记忆使用摘要/条目与关键词检索，归纳失败保留待办，读档后旧请求失效。仍有容量上限，不是无限记忆。

## 应用、网络与数据位置

应用未签名、公证。`.app` 同级 `local-runtime` 链接指向项目 `.runtime/`，请保持目录完整；不要仅复制 `.app`。另一台 Mac 应重建环境，不复制虚拟环境。

本地服务仅监听 `127.0.0.1`，端口动态分配，关闭最后窗口或 Cmd+Q 停止子进程。模型准备完成后，本地推理不需要付费 API；自行设置外部服务时会按该服务规则处理输入与计费。

玩家存档/配置在 `~/Library/Application Support/RyzaChat/`，日志位于其 `logs/`。不要将其上传到公开仓库。`config/providers.json` 也是本地私密配置，只有 `providers.example.json` 可以分发。

## 检查与维护

- `bash scripts/test_source_release.command`：不依赖模型的源码检查。
- `node scripts/motion_regression.js`：恢复角色媒体后进行骨骼动作回归，纯源码检查不包含此项。
- `python3 scripts/audit_upstream_ui.py --packaged`：在保留上游 Git 历史和构建包时，比较原版 63 个 HTML/CSS/图标；纯源码 ZIP 没有 Git 历史时不适用。
- `python3 scripts/cleanup_mac_demo.py`：仅预览可清理资源，显式 `--apply` 才执行。
- `python3 scripts/export_github_release.py`：生成源码发布包，排除个人环境、输出、角色二进制媒体及模型。

源码检查与自动化不代替真人麦克风、长时间运行或音色试听。本版仍是本地预览版，不能据此声称其他硬件、Windows/Android 或全部情绪组合均已验证。
