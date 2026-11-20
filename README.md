# TABLE//ZERO — V11 FINAL CREATIVE + CODE HANDOFF

**2026-11-21 기준 / Unity 실제 실행·실사 에셋 미검증 / CASE 001 스토리 진실 보존**

이 패키지는 사용자가 확정한 두 심문·현장 이미지와 기존 V0.3~V10 설계·코드에 대한 **개발 인계/회귀 테스트 패키지**다. **완성 게임·Unity 프로젝트 전체·게임용 실사 캐릭터/소품/환경 모델 ZIP은 아니다.** 사용자 PC 또는 Codex의 실제 Unity/Git 소스를 직접 수정한 결과도 아니다. Claude Code는 원본과 이 자료를 안전하게 병합하고 **실제 실행**으로 품질을 증명해야 한다

## 최우선 읽을 파일
1. `docs/CLAUDE_CODE_V11_FINAL_MASTER_DIRECTIVE.txt` — Claude Code 실행 지시문 (ZIP 밖에 동일 TXT 제공)
2. `docs/V11_CREATIVE_VISION_AND_QUALITY_LOCK.md` — 사용자 이미지 목표와 퇴보 방지
3. `docs/UIUX_SCENE_FIRST_PREMIUM_SYSTEM.md` — 1인칭·심문·TABLE INDEX UI/UX
4. `docs/INTERACTION_EVERY_PROP_AND_ROOM.md` — 사물/서랍/화장실 상호작용
5. `docs/AI_SUSPECT_INTERROGATION_AND_VOICE.md` — 실제 AI·타이핑·STT·시간 규칙
6. `docs/CASE001_FULL_STORY_AND_ENDINGS.md` — 사건 전체/심문/결말
7. `docs/WEB_RESEARCH_TECH_ASSETS_LEGAL.md` — 기술, 라이선스, 한국 절차 확인 자료
8. `reference/CASE001_CANON_LOCKED.json` — 비공개 서버의 사건 진실 정본

## 포함된 자료
- 사용자 제공 승인 이미지 2개: `references_images/*.png`, 1672×941
- V10에서 인계한 서버/Unity/UI Toolkit/테스트/기존 82개 연출·대본·스토리 자료
- **새 140개** `data/room302_interaction_manifest.json`: 개별 사물/동작/관찰/승인 필요 상태 명세
- **새 55개** `data/v11_signature_cinematic_beats.json`: 연기·소품·소리·카메라 연결 비트(기존 수십개 연출과 중복 정리 필요)
- 새 Python 구현: `server/prop_world.py`, `server/interview_service.py`, `server/speech_adapter.py`, `server/v11_cinematic_gate.py`, `server/api.py` V11 라우트와 `tactics.py` 시간 비용
- 새 Unity C# 구성요소: `TZInspectableProp`, `TZPropFocusController`, `TZVoiceQuestionCapture`, `TZVoiceInterviewBridge`, `TZPropCoverageAudit`
- `preview/V11_FINAL_ART_AND_INTERACTION_REVIEW.html`: 사용자 이미지와 140개 상호작용 명세를 보는 로컬 클릭형 레퍼런스 뷰어 (실제 Unity·AI 시뮬레이션 아님)
- `tests/*`: 기존 V10 회귀 테스트와 V11 계약 테스트

## 실제 실행할 수 있는 명령
```
cd TABLE_ZERO_V11_FINAL_HANDOFF
python -m unittest discover -s tests -v
python tools/v11_smoke_demo.py
python tools/generate_room_catalog.py
python tools/generate_signature_beats.py
```
위 명령은 Python 계약/참조 로직을 검증한다. `v11_smoke_demo.py`의 AI는 정확하게 `SCRIPTED_PREVIEW_NOT_AI`로 표시하며 실제 LLM 테스트 결과가 아니다

### 개발 서버 (localhost only, 유료 API는 기본 비활성)
```
# TABLEZERO_LOCAL_DEV_TOKEN: 24자 이상, 현지 테스트에서만 환경변수로 주입
# TABLEZERO_AI_PROVIDER: preview(기본) 또는 ollama 또는 openai
# TABLEZERO_OLLAMA_MODEL: 설치된 로컬 모델명
# TABLEZERO_STT_PROVIDER: disabled(기본) 또는 local 또는 openai
# openai 활성화는 OPENAI_API_KEY와 TABLEZERO_ALLOW_PAID_API=I_APPROVE_PAID_API_CALLS 설정이 있는 경우만
python -m server.api
```

새 HTTP 경로 (개발 연결 테스트용, 프로덕션 인증·영속화·서버 시점 검증 미완):
- `POST /v1/interview/start` → 해당 인물 면담과 집중시간 리소스 준비
- `POST /v1/interview/ask-v11` → typed/suggested/voice 실제 LLM 응답을 검증한 경우에만 차감
- `POST /v1/speech/transcribe` → 실제 WAV audio/wav 16-bit mono 16/24/48kHz → 선택된 STT → 확인할 텍스트 반환 (요청 승인/모델 설치 전 이용 불가)

**주의:** 원본 `POST /v1/interview/ask`도 동일한 시간 계약에 맞게 연결하는 개발용 하위호환을 유지. 출시용은 별도 인증, Rate Limit, 원격 공격/프롬프트 인젝션 방어, 세션 저장/복구, 이벤트 트랜잭션, 모델 모니터링이 필요

## 어떤 게 아직 실제로 없는가
- 사용자의 두 이미지와 동일 수준의 실제 3D Unity 빌라/욕실/손/용의자/서랍 프리팹
- 방 내부 140개 실제 모델, 리깅, 소리, 실제 물리 상호작용 완료 확인
- Unity Editor 및 Build 실행 기록, 빌드 FPS, Unity C# 컴파일 검증
- 실 AI 모델 API 호출/30턴 한국어 대화 테스트 및 실제 마이크 STT 엔드투엔드 검증
- 55개 연출 영상/오디오/접촉/물리 실행 검증, 실제 아트 승인
- Steam 전체 출시/인증/라이선스 심사

이것들이 없으면 **상업용 완성**으로 표시하지 마라

## 다음 우선순위
1. 실제 Git/Unity 프로젝트 조사→브랜치/백업
2. 렌더·씬·UI 버전/코드 차이 확인→V11 시스템 병합
3. 이서연 실제 3D 심문, 손/컵/자료/카메라 접촉 동기화의 한 장면 합격
4. 302호 실제 서랍/욕실/주방의 고품질 상호작용 시퀀스 합격
5. 실제 LLM+텍스트/마이크 심문과 세계 이벤트 재조사 연결
6. 전체 CASE 001 결말 실사 연출과 연속 빌드 QA

패키지 파일 수, 자동테스트 실제 성공 횟수 및 제한 사항: `qa/V11_VERIFICATION_REPORT.txt`
