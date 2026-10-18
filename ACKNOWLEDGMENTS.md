# 来源、参考与致谢

## 原作基础

感谢 **zeroa234** 的 [ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive)。本分支直接基于上游 v1.2.23（提交 `45e75ad6f6f0eb7952676b1bf24a674256082941`），保留其主界面、角色交互、游戏逻辑和跨平台宿主，并添加 Apple Silicon 本地运行适配。原 MIT 许可证及版权声明完整保留在根目录 `LICENSE`，不将原作成果标作本分支独立原创。

## 设计参考

感谢 **onion-aqua** 的 [AgentAtelierR](https://github.com/onion-aqua/AgentAtelierR)。本分支参考其本地语音、音色/模式配置、情绪引导、语言一致性、记忆处理与音频可靠性的设计思路，针对 JavaScript/Electron/MLX 独立实现。此致谢不表示两项目存在合作、官方关联或互相背书；不将其整个仓库代码重新许可为本项目 MIT。具体取舍见 `docs/AGENTATELIER_ADAPTATIONS.md`。

## 推理与语音生态

依赖由用户准备时另外取得，仍适用各自许可证与模型条款：

- [llama.cpp](https://github.com/ggml-org/llama.cpp)、[Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) 与 [Unsloth GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)。
- [MLX](https://github.com/ml-explore/mlx)、[MLX Audio](https://github.com/Blaizzy/mlx-audio)、[MLX Audio Plus](https://github.com/DePasqualeOrg/mlx-audio-plus)。
- [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)、[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) 及 mlx-community 对应量化转换。
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice)、[Fun-CosyVoice3](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)、[MLX 量化版本](https://huggingface.co/mlx-community/Fun-CosyVoice3-0.5B-2512-4bit) 与 [S3TokenizerV3](https://huggingface.co/mlx-community/S3TokenizerV3)。
- 可选 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)、Kokoro 及其相关依赖。
- [Electron](https://github.com/electron/electron) 与代码中保留声明的其他依赖。

源码包不包含这些模型权重、推理二进制或 Python 环境。固定版本见 `desktop/model-manifest.json`、准备脚本及相应 requirements 文件；未声称所列版本是最新版本。

## 角色与第三方资源

莱莎角色、相关作品名称、美术、原录音及其他第三方素材的权利属于各自权利人；本分支不是官方产品。源码包不包含恢复得到的角色图片、骨骼、音频、字体或模型参考音频。准备脚本仅提供本地资源恢复流程，不授予素材再分发或商业使用权。

仓库中的 Spine 运行时代码保留其自带许可声明，使用与分发应遵循相应条款。根目录 MIT 许可证不覆盖第三方材料自身的限制。上传你自己的样音、角色资源或权重前，应分别确认相应授权。
