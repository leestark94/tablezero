# TABLE//ZERO — V21.1 FULL STORY + GAMEFLOW + UI/UX + COMMON AI FINAL HANDOFF

**최종 작업용 통합 설계 패키지**. 이 파일은 단독 게임이 아니라 기존 Unity 6 프로젝트에 붙이는 *개발 명세/사건 데이터/UX 시안/검수 계획*이다.

## 0. 이번에 실제로 하나로 묶은 내용
- CASE 001 4인의 악연과 사건 진실: V21 진범 박현수(s3), 강도현의 팔 접촉·휴대전화 파손·책임서 전송, 이서연의 개인 자금 사용·사진 유리로 생긴 손 상처, 피해자의 정정서·마지막 업무 기록, 박현수와의 치명상 21:57. 27개 사건 사실과 13개 본편 장면 + V21 추가 5개 심문·후일담 장면.
- CASE 002 이후에도 재사용할 **공통 AI 심문 엔진**: 인격/기억/회피/거짓말/진술변경/상대 형사 관찰/역심문/자기보호, 마이크·텍스트 동일 의미 경로.
- 기존 208 소품 ID 전수 보존, 18 주요 조사 그룹/19개 증거/22 조건부 이벤트, 180수사분 비용 모델.
- **게임의 화면/흐름 전체**: Boot→Menu→배정 시네마틱→피해자 초동 보고→복도→302호→수사본부→AI심문·기록·포렌식→재수사→최종보고→결말. 입력/비용/텍스트/오류/저장/접근성 포함.
- **클릭 가능한 HTML UX 시안**(실제 AI/Unity 미연결), 실제 UI 문구 112개, QA 체크 129건, 정본·데이터 레퍼런스 정적 검사 도구.

## 1. Claude Code 필수 읽기 순서
1. **`01_CLAUDE_CODE_ULTIMATE_PROMPT.md`를 최우선으로 읽고 집행.** 하단 `O. V21.1 추가 명령`까지 읽을 것.
2. **`01_CANON/CASE001_V21_TRUTH.json`** — 사건 과거의 유일한 정본. 구버전 V16 `s2=이서연` 범인 정답은 런타임 로드 금지.
3. `02_DRAMA/CHARACTER_BIBLES.md`, `DRAMA_SCENES.md` — 인물·정황·대사의 작가 정본.
4. `03_AI/INTERROGATION_CORE_ENGINE.md`, `CASE001_PERSONA_RESPONSE_RULES.md` — 모든 사건 공통 엔진과 CASE 001 전용 인격·기억.
5. `04_EVIDENCE/EVIDENCE_CHAIN_AND_REPORT.json` — 19개 검증 가능한 증거와 입증 보고서.
6. `05_PROPS/ORIGINAL_208_MANIFEST.csv`, `PROP_208_V21_CLASSIFICATION.csv`, `18_HOTSPOT_GROUPS.json` — 208 원본 ID 유지와 18개 핵심 조사 묶음.
7. `06_EVENTS/CONDITIONAL_SURPRISE_EVENTS.json` — 조건부 이벤트 22종.
8. `07_GAMEPLAY/GAMEFLOW_COST_AND_BRIEFING.md` — 시간=돈·게임 흐름.
9. **`08_UI_UX/01_COMPLETE_GAME_UX_SPEC.md`** — 메뉴에서 엔딩까지 **전체 UX 최상위 명세**.
10. `08_UI_UX/02_SCREEN_WIREFRAMES.md`, `03_UI_FLOW_AND_COST_CONTRACT.json`, `04_CLICKABLE_UX_PROTOTYPE.html`, `06_OPENING_DIRECTOR_SCRIPT.md`, `07_UI_KOREAN_COPY_DECK.csv` — 화면 구조/시연/초동 연출/UI 문구.
11. `09_TECH_QA/01_STORY_PROOF_AND_CASE_LOGIC.md`, `02_ARCHITECTURE_CASE002_AND_ACCEPTANCE.md`, `03_CONFLICTS_MIGRATION_AND_NONNEGOTIABLE.md`, `04_QA_MATRIX.csv`, `05_VALIDATE_DATA_PACKAGE.py` — 반증·서버·품질 검증.
12. `10_IMPLEMENTATION/01_ORDER_OF_WORK_AND_DOD.md`, `02_CLAUDE_CODE_FIRST_RUN.md` — 단계별 구현/납품 정의.

## 2. 적용 우선순위
- **사건 진실·인격·타임라인:** V21 정본이 V11~V20의 사건 데이터를 대체.
- **화면/UX/조작:** 08_UI_UX와 승인 시각 레퍼런스(11_REFERENCE_ONLY)가 기본. **구버전 레퍼런스 그림의 날짜·스포일러·나이는 새로운 정본 아님.**
- **엔진·시간·증거·저장·QA:** 03_AI, 04_EVIDENCE, 07_GAMEPLAY, 09_TECH_QA, 10_IMPLEMENTATION이 우선.
- **실제 기존 Unity 모델·프리팹·씬·코드 및 미커밋 변경:** 백업/차이 확인 후 패치 방식으로 보존; 설계 변경을 이유로 일괄 폐기 금지.
- **제거 후보 13개:** Unity 씬에서 실물을 확인한 후 제거 여부 결정, 기존 ID/사용자 자료 사라지지 않게 추적.

## 3. 실제로 검증한 것과 아직 아닌 것
- **검증한 것:** JSON/CSV 정적 참조의 데이터 연결, 208원본 소품 ID 보존, 그룹·증거·사건 사실 ID의 유효성, 작성된 129개 QA 테스트 목록 및 UI 문구.
- **검증되지 않은 것:** Unity 씬/Windows 게임 빌드, 실제 AI 자유 대화 품질, 마이크/STT/TTS, 포렌식 계산, 3D 연기/애니메이션, 45~70분 밸런스, 60FPS.
- `08_UI_UX/04_CLICKABLE_UX_PROTOTYPE.html`은 배치와 이동을 눌러보는 UX 시안이며 **실제 게임이 아니다**.

## 4. 빠른 시작
- Claude Code에 **이 ZIP 전체**를 주고 `01_CLAUDE_CODE_ULTIMATE_PROMPT.md`를 실행 지시로 준다.
- 실제 Unity 프로젝트를 연 다음 `10_IMPLEMENTATION/02_CLAUDE_CODE_FIRST_RUN.md` 순서로 현상 감사→정본 정리→게임 루프부터 패치.
- 데이터만 확인하려면 `python 09_TECH_QA/05_VALIDATE_DATA_PACKAGE.py` 실행(실제 빌드 테스트와 별개).
- UX는 `08_UI_UX/04_CLICKABLE_UX_PROTOTYPE.html`을 브라우저로 연다(외부 라이브러리 불필요).
