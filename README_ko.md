# Ryza Chat · Mac Local

[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | **한국어**

[zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive)를 기반으로 M4·메모리 24GB Mac에 맞춰 조정한 Apple Silicon용 로컬 AI 프리뷰입니다. 원본 프로젝트의 메인 화면, 신체 부위별 독립 모션, 게임 저장 기능을 유지하면서 로컬 대화, 음성 인식, 중국어·일본어 음성 합성과 안정성 개선을 추가했습니다.

**이 버전은 소스 코드 프리뷰이며, 바로 실행할 수 있는 설치 프로그램이 아닙니다.** 모델, 캐릭터 리소스, 참조 음성, 개인 데이터는 포함하지 않습니다. 처음 설정할 때 의존성과 모델을 다운로드하려면 인터넷 연결이 필요합니다. 앱은 서명 및 Apple 공증을 받지 않았으며, 추가 기능은 Windows와 Android에서 다시 검증하지 않았습니다.

## 로컬 엔진

| 기능 | 로컬 엔진 |
| --- | --- |
| 대화 및 일본어 대사 번역 | Qwen3.5-9B Q4_K_M / llama.cpp Metal |
| 중국어·일본어·영어 음성 입력 | Qwen3-ASR 0.6B 4bit / MLX |
| 일본어 캐릭터 음성 | Qwen3-TTS 1.7B Base 4bit / MLX |
| 감정 표현이 있는 중국어 음성(선택) | CosyVoice3 0.5B 4bit / 별도 MLX 환경 |
| 기타 선택 사항 | macOS 시스템 음성. GPT-SoVITS와 Kokoro는 선택적 실험 구성 요소 |

로컬 서비스는 루프백 주소에서만 연결을 받으며 앱 종료 시 함께 종료됩니다. 로컬 추론에는 유료 API가 필요하지 않습니다. 설정에서 외부 서비스에 연결할 수도 있습니다. 생성된 음성은 원작 성우가 새로 녹음한 것이 아니며, 음색 유사도와 감정 표현은 계속 개선 중입니다.

## 빠른 시작

Apple Silicon Mac, Node.js/npm, [uv](https://docs.astral.sh/uv/)가 필요합니다. 메모리 24GB를 권장하며, 모델·실행 환경·설치 캐시를 위해 최소 25GB의 여유 공간을 확보하세요.

프로젝트 루트에서 다음 명령을 순서대로 실행하세요.

```bash
bash scripts/prepare_mac_demo.command
# 선택: 기본 설정을 마친 후 중국어 감정 음성 설치
bash scripts/prepare_cosyvoice.command
bash scripts/build_mac_demo.command
bash scripts/start_mac_demo.command
```

설정 스크립트는 원본 프로젝트의 릴리스에서 캐릭터 리소스를 복원합니다. 먼저 [리소스 및 출처 안내](ACKNOWLEDGMENTS.md)(중국어)를 확인하세요. 이미 확보한 호환 리소스에서 `scripts/restore_media.py`로 복원할 수도 있습니다. 첫 음성 합성이나 인식 요청에는 모델 로딩 시간이 필요합니다.

빌드된 `.app`은 같은 디렉터리의 `local-runtime` 링크와 프로젝트의 `.runtime/`에 의존하므로 앱만 따로 옮기지 마세요. 다른 Mac에서는 실행 환경을 새로 구성해야 합니다. 자세한 내용은 [Mac 사용 안내](docs/MAC_DEMO.md)(중국어)를 참고하세요.

## 원본 대비 주요 변경 사항

- Apple Silicon에서 로컬 모델 실행, 모델 리비전 고정, 주 모델 SHA256 검증.
- 기존 화면에서 중국어·일본어 음색, 일반/ASMR별 음성 프로필, 감정 표현 강도 설정.
- 무작위 포즈를 유지하면서 독립 애니메이션 트랙을 조정해 팔 모션과 전신 모션의 충돌 완화.
- 텍스트 스트리밍, 생성 취소, 보수적인 언어 검사, 번역 재사용, 늦게 도착한 불필요한 음성 폐기.
- 장기 기억의 동시 처리 보호, 요약 실패 시 대기 데이터 유지, 저장 슬롯 간 격리, 로컬 오디오 검증.

적용 범위와 판단 근거는 [AgentAtelierR 참고 사항](docs/AGENTATELIER_ADAPTATIONS.md)(중국어)에 정리했습니다. 원본 README는 [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md)에 보존했습니다.

## 검증 및 릴리스

```bash
bash scripts/test_source_release.command
python3 scripts/export_github_release.py
```

소스 검사는 모델을 다운로드하지 않으며, 실제 마이크·Metal 추론·주관적인 음성 평가를 대신하지 않습니다. 업로드 절차와 프리뷰 릴리스 설명은 [릴리스 안내](docs/GITHUB_RELEASE.md)(중국어)를 참고하세요.

## 감사의 말 및 라이선스

- **[zeroa234/ryza-ai-revive](https://github.com/zeroa234/ryza-ai-revive)**: 이 프로젝트의 직접적인 기반입니다. 호스트, 인터페이스, 캐릭터 상호작용, 게임 로직을 바탕으로 수정했으며 원본의 MIT 라이선스와 저작권 고지를 유지합니다.
- **[onion-aqua/AgentAtelierR](https://github.com/onion-aqua/AgentAtelierR)**: 로컬 음성 설정, 감정 표현, 언어 일관성, 기억 처리, 오디오 안정성에 관한 설계를 참고했습니다. 해당 기능은 독립적으로 구현했습니다.

다른 엔진·모델·리소스의 출처는 [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)(중국어)에 있습니다. [MIT](LICENSE)는 해당 프로젝트 코드에 적용되며, 타사 캐릭터·그림·음성·폰트·모델·Spine 런타임 모두에 같은 라이선스를 부여하는 것은 아닙니다.
