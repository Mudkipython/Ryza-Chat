# Ryza Chat · Mac Local

**English** | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

An Apple Silicon local AI preview based on [zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive), tuned for an M4 Mac with 24GB of memory. It retains the upstream main interface, independent character motions, and game saves while adding local chat, speech recognition, Chinese/Japanese speech, and reliability improvements.

**This is a source preview, not a ready-to-run installer.** Models, character media, reference audio, and personal data are not included. Initial setup requires internet access to download dependencies and models. The app is unsigned and not notarized; the new features have not been revalidated on Windows or Android.

## Local engines

| Feature | Local engine |
| --- | --- |
| Chat and Japanese dialogue translation | Qwen3.5-9B Q4_K_M / llama.cpp Metal |
| Chinese, Japanese, and English speech input | Qwen3-ASR 0.6B 4bit / MLX |
| Japanese character speech | Qwen3-TTS 1.7B Base 4bit / MLX |
| Optional expressive Chinese speech | CosyVoice3 0.5B 4bit / isolated MLX environment |
| Other options | macOS system voices; GPT-SoVITS and Kokoro as optional experiments |

Local services bind only to loopback and stop when the app exits. No paid API is required for local inference; external services can still be configured in Settings. Generated speech is not a new recording by the original actor, and voice similarity and expression remain areas for improvement.

## Quick start

You need an Apple Silicon Mac, Node.js/npm, and [uv](https://docs.astral.sh/uv/). We recommend 24GB of memory and at least 25GB of free disk space for models, environments, and installation caches.

Run these commands from the project root:

```bash
bash scripts/prepare_mac_demo.command
# Optional: expressive Chinese speech, after the base setup
bash scripts/prepare_cosyvoice.command
bash scripts/build_mac_demo.command
bash scripts/start_mac_demo.command
```

The setup script restores character media from an upstream release. Read the [resource and attribution notes](ACKNOWLEDGMENTS.md) first. You can also use `scripts/restore_media.py` with compatible resources you have already obtained. The first speech synthesis or recognition request incurs model-loading time.

The built `.app` depends on the adjacent `local-runtime` link and the project's `.runtime/` directory; do not move it on its own. Recreate the environment on another Mac. See the [Mac guide](docs/MAC_DEMO.md) (Chinese) for details.

## Changes from upstream

- Local model startup on Apple Silicon, pinned model revisions, and SHA256 verification for the main model.
- Chinese/Japanese voices, separate normal/ASMR profiles, and expression strength within the existing interface.
- Coordination across independent animation tracks, retaining random poses while reducing arm/full-body conflicts.
- Streaming text, generation cancellation, conservative language checks, translation reuse, and stale-audio disposal.
- Concurrent memory consolidation safeguards, preservation of failed pending work, save isolation, and local audio validation.

See the [AgentAtelierR adaptation notes](docs/AGENTATELIER_ADAPTATIONS.md) (Chinese) for scope and tradeoffs. The original upstream README is preserved in [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md).

## Checks and releases

```bash
bash scripts/test_source_release.command
python3 scripts/export_github_release.py
```

Source checks do not download models or replace real microphone, Metal inference, or subjective voice testing. Upload instructions and preview release notes are in the [release guide](docs/GITHUB_RELEASE.md) (Chinese).

## Credits and license

- **[zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive)**: the direct source base for the host, interface, character interactions, and game logic. The upstream MIT license and copyright notice are retained.
- **[onion-aqua/AgentAtelierR](https://github.com/onion-aqua/AgentAtelierR)**: design references for local voice configuration, expressive speech, language consistency, memory, and audio reliability. These adaptations were implemented independently.

See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) (Chinese) for additional engines, models, and resource attribution. [MIT](LICENSE) applies to the relevant project code; it does not grant the same license to all third-party characters, artwork, audio, fonts, models, or the Spine runtime.
