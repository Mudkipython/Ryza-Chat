# GitHub 源码预览版发布

建议标题：`Mac Local Preview 1 — Apple Silicon 本地对话与中日配音`。
建议标签：`mac-local-preview.1`。保留上游运行时版本 `1.2.23`，用预览版标签区分本分支，不冒用上游正式发布。

## 上传方式

1. 执行 `python3 scripts/export_github_release.py`。
2. 解压 `output/github-release/ryza-chat-mac-local-preview-source.zip`。其中单层 `ryza-chat-mac-local/` 下的内容即是仓库根目录；不要上传整个开发工作目录。
3. 在你的 GitHub 新仓库中上传该目录内容，或在目录中自行执行 `git init` 后提交推送。GitHub 网页不能执行 `.github/workflows/` 上传时，可使用 Git 客户端推送。
4. 如创建 Release，可附上该源码 ZIP 与旁边的 `SHA256SUMS.txt`，正文复制下面的说明。无需上传 `.app`、模型或本机存档。

导出不提交、不改远程、不推送，也不附带本地 Git 历史。文件清单与逐文件 SHA256 在包内 `SOURCE_MANIFEST.json`；ZIP 的 SHA256 在包外，便于下载核对。建议保留上游 fork 关系；若新建独立仓库，README 和许可证中的来源署名也应保留。

## 可复制的发布说明

本源码预览版基于 zeroa234/ryza-ai-revive v1.2.23，针对 Apple Silicon Mac 本地运行，参考 onion-aqua/AgentAtelierR 的部分设计独立适配。

- 本地 Qwen3.5-9B 对话与翻译、Qwen3-ASR 语音输入、Qwen3-TTS 日语配音。
- 可选 CosyVoice3 中文情感配音，按语言与普通/ASMR 模式配置音色和演绎强度。
- 保留原版主界面与独立动作，改善动作竞争。
- 流式文字、取消生成、语言校验、译文复用、长期记忆并发保护与音频校验。

建议 M4 / 24GB Mac，首次准备需下载模型和依赖。源码包不含模型、角色媒体、参考音频、密钥、个人存档或虚拟环境。不是独立安装包，未签名、公证。Windows/Android 新增功能未重新验收；音色、情感、首句等待和内存表现仍在优化。

源码检查在本地通过；实际应用已验证本地流式对话、取消和完整记录提交。GitHub Actions 提供不下载模型的源码检查，首次上传后仍应查看实际 CI 结果。

致谢：
- https://github.com/zeroa234/ryza-ai-revive — 原项目源码、界面、宿主与游戏逻辑基础。
- https://github.com/onion-aqua/AgentAtelierR — 语音、语言一致性与记忆可靠性等思路参考。

许可：保留上游 MIT 代码许可；角色素材、第三方运行时、模型和依赖各遵其自身条款，详见 ACKNOWLEDGMENTS.md。
