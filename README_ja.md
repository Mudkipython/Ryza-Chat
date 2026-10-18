# Ryza Chat · Mac Local

[English](README.md) | [简体中文](README_zh.md) | **日本語** | [한국어](README_ko.md)

[zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive) を基に、M4・メモリ24GBのMac向けに調整した、Apple Silicon用ローカルAIプレビューです。上流版のメイン画面、部位ごとの独立したモーション、ゲームのセーブ機能を維持しながら、ローカル対話、音声認識、中国語・日本語の音声合成と安定性の改善を追加しています。

**本リリースはソースコードのプレビュー版であり、そのまま起動できるインストーラーではありません。** モデル、キャラクター素材、参照音声、個人データは同梱していません。初回セットアップでは依存パッケージとモデルのダウンロードにインターネット接続が必要です。アプリは未署名・未公証で、追加機能のWindows・Androidでの再検証は行っていません。

## ローカルエンジン

| 機能 | ローカルエンジン |
| --- | --- |
| 対話・日本語セリフへの翻訳 | Qwen3.5-9B Q4_K_M / llama.cpp Metal |
| 中国語・日本語・英語の音声入力 | Qwen3-ASR 0.6B 4bit / MLX |
| 日本語キャラクター音声 | Qwen3-TTS 1.7B Base 4bit / MLX |
| 中国語の感情表現付き音声（任意） | CosyVoice3 0.5B 4bit / 独立したMLX環境 |
| その他の選択肢 | macOSシステム音声。GPT-SoVITSとKokoroは任意の実験用コンポーネント |

ローカルサービスはループバックアドレスのみで待ち受け、アプリ終了時に停止します。ローカル推論に有料APIは不要です。設定から外部サービスを接続することもできます。合成音声はオリジナル声優による新規収録ではなく、声の類似度や感情表現には改善の余地があります。

## クイックスタート

Apple Silicon搭載Mac、Node.js/npm、[uv](https://docs.astral.sh/uv/) が必要です。メモリ24GBを推奨し、モデル、環境、インストール用キャッシュのために少なくとも25GBの空き容量を確保してください。

プロジェクトのルートで順に実行します。

```bash
bash scripts/prepare_mac_demo.command
# 任意：中国語の感情表現付き音声。基本セットアップ後に実行
bash scripts/prepare_cosyvoice.command
bash scripts/build_mac_demo.command
bash scripts/start_mac_demo.command
```

セットアップスクリプトは上流版のリリースからキャラクター素材を復元します。先に[素材とクレジットに関する説明](ACKNOWLEDGMENTS.md)（中国語）をご確認ください。取得済みの互換リソースから `scripts/restore_media.py` で復元することもできます。初回の音声合成・認識にはモデル読み込みの待ち時間があります。

ビルドされた `.app` は、同じディレクトリにある `local-runtime` リンクとプロジェクトの `.runtime/` に依存します。`.app` だけを移動しないでください。別のMacでは環境を再構築してください。詳細は[Mac利用ガイド](docs/MAC_DEMO.md)（中国語）をご覧ください。

## 上流版からの主な変更

- Apple Siliconでのローカルモデル起動、モデルのリビジョン固定、メインモデルのSHA256検証。
- 既存画面での中国語・日本語音声、通常・ASMR別の音声設定、感情表現の強度調整。
- ランダムなポーズを維持しながら独立アニメーショントラックを調整し、腕と全身モーションの競合を低減。
- テキストのストリーミング表示、生成のキャンセル、保守的な言語チェック、翻訳の再利用、遅れて届いた不要な音声の破棄。
- 長期記憶の並行処理対策、要約失敗時の保留データ保持、セーブ間の分離、ローカル音声の検証。

適用範囲と判断理由は[AgentAtelierRの設計を参考にした改善一覧](docs/AGENTATELIER_ADAPTATIONS.md)（中国語）をご覧ください。上流版READMEの原文は [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md) に保存しています。

## 検証とリリース

```bash
bash scripts/test_source_release.command
python3 scripts/export_github_release.py
```

ソースコードのチェックではモデルをダウンロードしません。実際のマイク、Metal推論、音声の主観評価を代替するものではありません。アップロード手順とプレビュー版のリリース説明は[公開ガイド](docs/GITHUB_RELEASE.md)（中国語）にあります。

## 謝辞とライセンス

- **[zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive)**：本プロジェクトの直接の基盤です。ホスト、画面、キャラクターとの対話、ゲームロジックを基に変更しています。上流版のMITライセンスと著作権表示を保持しています。
- **[onion-aqua/AgentAtelierR](https://github.com/onion-aqua/AgentAtelierR)**：ローカル音声設定、感情表現、言語の一貫性、記憶処理、音声の安定性に関する設計を参考にしています。対応する機能は独立して実装しました。

その他のエンジン、モデル、素材の帰属は [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)（中国語）をご覧ください。[MIT](LICENSE) は対象となるプロジェクトコードに適用されます。第三者のキャラクター、美術、音声、フォント、モデル、Spineランタイムすべてに同じ許諾を与えるものではありません。
