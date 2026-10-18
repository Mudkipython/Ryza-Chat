# Ryza Chat · Mac Local

[English](README.md) | **简体中文** | [日本語](README_ja.md) | [한국어](README_ko.md)

基于 [zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive) 的 Apple Silicon 本地 AI 试玩分支，面向 M4 / 24GB Mac 调整。保留原版主界面、角色独立动作与游戏存档，增加本地对话、语音输入、中日配音和可靠性改进。

**这是源码预览版，不是免安装应用。** 模型、角色媒体、参考音频和个人数据不随源码分发；首次准备需要联网下载依赖与模型。尚未签名、公证，Windows/Android 新增功能未重新验收。

## 当前方案

| 功能 | 本地引擎 |
| --- | --- |
| 对话、日语台词翻译 | Qwen3.5-9B Q4_K_M / llama.cpp Metal |
| 中文、日语、英语语音输入 | Qwen3-ASR 0.6B 4bit / MLX |
| 日语角色配音 | Qwen3-TTS 1.7B Base 4bit / MLX |
| 可选中文情感配音 | CosyVoice3 0.5B 4bit / 独立 MLX 环境 |
| 其他备用 | macOS 系统声音；GPT-SoVITS、Kokoro 为可选实验组件 |

本地服务仅监听回环地址，随应用退出，不需要付费 API。设置中仍可自行连接外部服务。生成语音不是原演员重新录制；音色和情绪效果仍有改进空间。

## 快速开始

需要 Apple Silicon Mac、Node.js/npm、[uv](https://docs.astral.sh/uv/)，建议 24GB 内存，并预留至少 25GB 磁盘空间供模型、环境和安装缓存使用。

在项目根目录依次运行：

```bash
bash scripts/prepare_mac_demo.command
# 可选：中文情感配音，基础准备完成后运行
bash scripts/prepare_cosyvoice.command
bash scripts/build_mac_demo.command
bash scripts/start_mac_demo.command
```

准备脚本从上游发行包恢复角色媒体。请先阅读[资源与致谢](ACKNOWLEDGMENTS.md)；也可使用 `scripts/restore_media.py` 从你已取得的兼容资源恢复。首次配音/识别存在模型冷启动。

构建后的 `.app` 依赖同级 `local-runtime` 链接及项目 `.runtime/`，不能单独搬走。另一台 Mac 应重新准备环境。详细说明见 [Mac 使用指南](docs/MAC_DEMO.md)。

## 相比上游的主要修改

- Apple Silicon 本地模型启动、固定模型修订与主模型 SHA256 校验。
- 原版布局下配置中日音色、普通/ASMR 模式与演绎强度。
- 独立动作轨道协调，保留随机姿势，减少手臂与全身动作竞争。
- 流式文字、取消生成、保守的语言校验、译文复用及迟到音频丢弃。
- 长期记忆并发、归纳失败保留、存档切换隔离与本地音频校验。

参考项目的适配范围见 [AgentAtelierR 适配清单](docs/AGENTATELIER_ADAPTATIONS.md)。上游 README 原文保存在 [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md)。

## 验证与发布

```bash
bash scripts/test_source_release.command
python3 scripts/export_github_release.py
```

源码检查不下载模型，也不代替真实麦克风、Metal 推理和主观音色测试。上传步骤与预览版发布说明见 [发布指南](docs/GITHUB_RELEASE.md)。

## 致谢与许可

- **[zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive)**：本项目直接基于其源码、宿主、界面、角色交互与游戏逻辑修改；保留上游 MIT 许可证和版权声明。
- **[onion-aqua/AgentAtelierR](https://github.com/onion-aqua/AgentAtelierR)**：本地语音配置、情绪演绎、语言一致性、记忆与音频可靠性等思路参考；相关适配独立实现。

更多引擎、模型和资源归属见 [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)。[MIT](LICENSE) 适用于相应项目代码，不代表第三方角色、美术、音频、字体、模型或 Spine 运行时全部获得相同许可。
