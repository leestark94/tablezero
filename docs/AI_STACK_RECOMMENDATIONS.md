# TABLE//ZERO 추천 AI·시네마틱 기술 스택 (2026-11-21 조사 기반)

## 우선순위 / 불필요한 장식 배제

| 레이어 | 추천 | 선택 이유 | 적용 단계 |
|---|---|---|---|
| 사건 정본 서버 | Python authoritative state + JSON locked canon + DB event log | AI가 진실·증거·사건 결과를 수정 못 하도록 분리 | P0 |
| NPC LLM | 검증된 structured-output 가능한 모델, 공급자 교체 가능한 어댑터 | JSON으로 대사·행동 **제안**만 반환 | P0-P1 |
| 로컬 개발 | Ollama(성능/한국어 검증 전제), Preview 표시 | API 비용 없이 기본 루프 시험 | P0 |
| 얼굴·손·상체 | Unity Animator + Animation Rigging + authored mocap | LLM이 직접 뼈 위치를 생성하지 않고 검수된 클립 믹싱 | P1 |
| 카메라 | 프로젝트 설치판 Cinemachine Impulse/Noise | 미세 흔들림/절제된 반응 | P1 |
| 타격/소품 | Unity Rigidbody·Collider·Audio event | 책상 타격 시 실제 물체 반응 | P1 |
| 실사 렌더링 | 현 Unity 파이프라인 확인 후 HDRP 별도 검토 | HDRP alone != GTA6; 저작한 에셋과 라이팅 품질 중요 | P1-P2 |
| 키/보안 | 서버측 secrets + 유료 승인 게이트 | Unity 빌드에 API 키나 진범 정본 금지 | P0 |
| UI | 월드 정합 evidence anchor + 저밀도 비디제틱 보조 UI | 조사를 방해하지 않는 절제된 미래형 연출 | P2 |
| On-device ML | Sentis (필요 시) | 사소한 분류/인식용일 뿐 핵심 한국어 NPC LLM과 무관 | 선택 |
| 음성 | 상업용 권리가 확보된 한국어 녹음/TTS | 사람 같은 억양·자연스러운 비언어적 효과 | P1-P2 |

## 웹에서 검토한 공식 자료
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Unity Sentis 2.6: https://docs.unity.cn/Packages/com.unity.ai.inference%402.6/manual/index.html
- Unity Cinemachine Impulse: https://docs.unity.cn/Packages/com.unity.cinemachine%406.6/manual/CinemachineImpulse.html
- Unity Animation feature set: https://docs.unity.com/en-us/engine/6000.3/manual/packages-list/feature-sets/character-animation-feature
- Unity Cinematic Studio: https://docs.unity.com/en-us/engine/6000.0/manual/packages-list/cinematic-studio-feature

### 결정 금지
- 현재 Unity 프로젝트를 열어보지 않고 HDRP 전환, Unity 버전 변경, GPU VRAM 가정, 특정 모델 비용/지연 보장, 상용 에셋 라이선스 승인, LLM 모델 선정 확정 금지.
- 오픈소스 Unity 패키지의 최신 버전만 보고 프로젝트 호환성과 라이선스가 검증되었다고 보고하지 말 것.
