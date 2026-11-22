# 다음 AI 인계지시서 (Claude Code / Codex 공통)

## ★ 최신 상태 — 2026-11-22 세션 종료 시점 (여기부터 읽어라)
브랜치 `dev/v11-integration`. 최신 커밋은 `git log --oneline -5`로 확인.

**사용자 현재 최우선 요구 (원문 요지):**
1. **이서연 3D 외형을 "사람처럼"** — 지금은 "고무찰흙/고무인간 같다", 10점 중 2점 → 9점 목표. 다른 작업보다 먼저.
2. AI가 아직 덜 똑똑하고 **이서연의 성격이 드러나지 않음**. 다른 용의자(강도현·박현수)를 만들 때도 같은 실수 금지.
3. 302호 소품·증거 배치를 진짜처럼 전부 재배치, 302 조명 눈부심(복도 센서등 `L_HallSensor` 아직 밝음) — 아직 미착수.

**이번 세션에 끝난 것 (검증됨):**
- 용의자 AI 전략 엔진 `server/strategy.py` + 서버 전용 dossier `tools/v21_dossiers.py` (증거가 기억을 "해제"하지 않음; DENY/CHALLENGE/CONCEDE_MIN/DEMAND_PROOF/STONEWALL/REBUKE). 말하는 모델엔 허용된 사실만 들어감.
- **스트리밍**: 서버 `/v1/interview/ask_start` → `{job_id}`, `/v1/interview/ask_poll` → `{partial,done,ok,error,receipt}`. Unity `TZInterrogationScreen.AskCo`가 생성되는 대로 타이핑, 기다리는 동안 용의자 Think 연기. 실측(Unity 꺼짐, 8B 예열): **첫 글자 0.6~0.7초**, 한 줄 완성 2.4~3초.
- 예열(warm-up)이 질문과 같은 로드 옵션(`line_load_options()`: num_ctx 2048 등)을 쓰도록 수정 — 전에는 첫 질문에서 모델 재로드로 약 150초 걸렸음.
- `TZFramePacing`: 평소 60fps, AI 생성 중 30fps (무제한 렌더가 GPU 100%를 먹어 답변이 40~170초 걸리던 원인).
- 모욕·성적 발언 → 공손한 거절문이 아니라 화내며 항의(REBUKE), 두 번째부터 변호인 요구. "죄송합니다만…응할 수 없습니다/개인정보 보호" 같은 상담원 말투는 가드가 거부.
- 서버 테스트 144개 통과 (`python -m unittest discover -s tests`).

**정직한 한계 / 주의:**
- RTX 2070 SUPER 8GB: **Unity 에디터 Play 중에는 VRAM이 약 3GB 사용 → Kanana 8B(약 5GB)가 GPU에 다 안 올라감** → 매우 느려짐. 빌드된 플레이어에선 VRAM 사용이 적어 들어갈 가능성 있음(**미검증 — Windows 빌드로 측정 필요**).
- 테스트 중 에디터에 열린 `Case001_Interrogation` 씬의 TZServer `ollamaModel`을 **임시로 2.1B로 바꿔 둠(저장 안 함)**. 씬을 저장하지 말고 다시 열어 버려라(원래 값: `hf.co/DevQuasar/kakaocorp.kanana-1.5-8b-instruct-2505-GGUF:Q4_K_M`). 2.1B는 상담원 말투·사실 지어냄으로 품질 나쁨.
- Kanana 1.5 상업 이용 라이선스 미확인.

**이서연 "사람처럼" — 다음 담당자 출발점:**
- 현재 모델: MPFB2(MakeHuman) 기반 `blender/scripts/build_seoyeon.py` → `TZSuspectCharacterBuilder` (Humanoid, 얼굴 키 17종). 고무처럼 보이는 주원인 후보: 피부 셰이더(SSS 없음·스펙/러프니스 균일·노멀/모공 디테일 없음), 머리카락이 덩어리 메시(카드/알파 없음), 눈(각막 굴절·습기·속눈썹 부족), 옷 주름 없음, 조명이 평면적.
- 무료 경로: 피부 디테일 노멀/러프니스 맵 생성 + URP 피부 근사(SSS 랩 라이팅) + 헤어 카드 + 눈 셰이더 + 림/키 조명. 
- 사실적 품질(9점)을 확실히 원하면 고품질 인물 에셋 필요 — MetaHuman(현재 라이선스상 타 엔진 사용 가능 여부 확인 필요, Epic 계정 필요), Character Creator(유료). **비용·계정 필요한 건 사용자 승인 먼저.**

---

## (이전 기록) 2026-11-21 V14 기준

> **2026-11-22 V21.1 적용 시작 — 사건 정본이 바뀌었다.** 진범은 박현수(s3, 21:57 치명상). 구 정본(이서연 진범)은 `reference/legacy_v04/`에 보관만, 로드 금지.
> 최상위 지시: `references_images/V21_PACKAGE/TABLE_ZERO_V21_ULTIMATE_HANDOFF/01_CLAUDE_CODE_ULTIMATE_PROMPT.md` (+ `00_START_HERE.md`). 진행 상황: `docs/v21/P0_CONFLICT_REPORT.md`.
> 서버 정본은 `python -I tools/build_v21_runtime.py`로 V21 패키지에서 생성한다(손 편집 금지). 다음 단계: P1 메인 메뉴→엔딩 전체 화면 흐름.

> 새 세션 시작용 붙여넣기 프롬프트와 세션 종료 시 인계 순환 규칙: [`HANDOFF_PROMPT.md`](HANDOFF_PROMPT.md)

## 0. 새 계정·새 PC에서 시작하기
```powershell
git clone https://github.com/leestark94/tablezero.git TABLE_ZERO
cd TABLE_ZERO
git lfs install; git lfs pull                 # 이미지·FBX·blend·폰트는 Git LFS
git checkout dev/v11-integration              # 작업 브랜치 (main은 이전 기준)
```
읽는 순서: 이 파일 → `docs/status/개발현황.md` → `docs/status/미완성작업.md` → `docs/status/변경이력.md`
→ `references_images/V14/CLAUDE_CODE_V14_MASTER_DIRECTIVE.txt` (현재 최우선 지시문) → `docs/TABLE_ZERO_CLAUDE_CODE_V11_FINAL_MASTER_DIRECTIVE.txt`

### 저장소에 없는 것 (PC마다 설치)
| 항목 | 설치 |
|---|---|
| Unity 6000.6.8f1 (URP 17.6, Cinemachine 3.1.7) | Unity Hub. `TableZero.Unity` 열면 Library 자동 재생성 |
| Unity CLI 연동(`unity command ...`) | Unity Pipeline 패키지(프로젝트에 포함) + `unity` CLI |
| Blender 4.5 | `C:\Program Files\Blender Foundation\Blender 4.5\` |
| MPFB2 (MakeHuman, 이서연 캐릭터 생성) | `blender --online-mode --command extension install --sync --enable mpfb` |
| MakeHuman 시스템 에셋(CC0, 280 MB) | https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip → `%APPDATA%\Blender Foundation\Blender\4.5\extensions\.user\blender_org\mpfb\data\` 에 압축 해제 |
| Python 3.12 + Pillow, numpy | 서버는 표준 라이브러리만 사용 |
| Ollama + `qwen3:4b` | `ollama pull qwen3:4b` (GPU 드라이버 리셋 이슈로 CPU 실행: `TABLEZERO_OLLAMA_NUM_GPU=0`) |
| Higgsfield / Tripo CLI | 선택. **크레딧 사용 전 반드시 비용을 말하고 사용자 승인** (무단 사용 금지 — 사용자 강력 요구) |
- `Builds/`(벤치 빌드)는 커밋 안 됨 → `TableZero.EditorTools.TZBuild.BuildBench302()`로 재생성
- API 키·토큰·비밀번호는 저장소에 없음(넣지 말 것)

## 1. 절대 규칙 (사용자 확정)
- 도형 캐릭터/장난감 소품을 완성품으로 쓰지 않는다. 없으면 `RELEASE_BLOCKED_ASSET`로 표기. 미완성을 완성이라 보고 금지
- 사건 진실은 `reference/CASE001_CANON_LOCKED.json`만. 클라이언트·LLM에 통째 전달 금지. `reference/CASE001_SUSPECT_PERSONAS_SERVER_ONLY.json`도 서버 전용
- 감정·거짓말 퍼센트 UI 금지, 정답 하이라이트 금지, 인게임 대사 끝 마침표 금지, 반응을 유무죄 신호로 쓰지 않음
- EXAONE 금지(비상업 라이선스). 유료 API 기본 비활성
- 심문실 얼굴 규칙: 프로필=선명한 실사 사진 / 3D 심문실=같은 인물이지만 눈·얼굴 윗부분은 조명·자세·머리카락으로 자연스럽게 어둠(검정 오버레이 금지)
- 용의자 호출 화면(좌 서류 대장 + 우 인물) 승인됨 — 카드형 UI로 회귀 금지
- Unity Game View로 실제 확인 후 보고. 세션 끝 `pwsh -File tools/backup_full.ps1` → `BACKUP_OK` 확인(바탕화면 `TABLE_ZERO_개발현황`), 이전 백업 삭제·덮어쓰기 금지
- 사용자는 쉬지 않고 실제 게임 화면으로 검증하며 계속 개발하길 원함. 불필요한 질문 최소화

## 2. 현재 상태 (V14 — 3D 심문실 최우선)
- **3D 진술녹화실 2**: `blender/scripts/build_interrogation.py` → `TZInterrogationRoomBuilder`(재질·조명 6개·반사 프로브 1회 렌더·포스트). 호출 화면에서 Enter → 실제 3D 방 입실(`TZInterrogationRoom3D.SitDown`)
- **이서연 3D**: `blender/scripts/build_seoyeon.py`(MPFB2, mixamo_unity 64본: 턱·눈·손가락, 얼굴 키 17종) → `TZSuspectCharacterBuilder.Import()` / `Place()` (Humanoid)
- **연기**: `TZSuspectActor` — 근육 공간 포즈 프리셋, 호흡·눈깜빡임·시선 도약·손가락·체중 이동(쿨다운)·턱, 팔 2본 IK로 손바닥 테이블 접촉, 서버 motion 16종 매핑(없는 동작은 거부·기록). 질문 흐름: Listen → Think(AI 생성 중) → Speak
  - 근육 부호(실측): 앞으로 숙임/고개 숙임 = 음수, 팔 앞으로 = 음수(Arm Front-Back), 앉은 허벅지 = 음수(Upper Leg Front-Back), 팔꿈치·무릎 굽힘 = 음수(Stretch)
- **진행 중(WIP, 커밋 e9cf074)**: 품질 패스
  - 완료: 승인 정면 레퍼런스 `assets_src/3d_sources/s2.png`를 얼굴 텍스처에 투영(`seoyeon_face_bake.py`, 코 위치 오차 약 2 px), 긴팔 상의+바지 분리(male_casualsuit04 → `Seoyeon_Knit`/`Seoyeon_Trousers`), 검정 플랫(shoes04), 눈썹은 사진에서
  - 남음: ① `TZSuspectCharacterBuilder.BuildMaterials`를 새 재질에 연결(피부 `seoyeon_skin_diffuse.png`, 니트=케이블 니트 텍스처 생성 필요, 바지=짙은 울) ② 앞머리·옆머리 카드(머리 본 100% 가중치)로 눈·이마 가리기 + 펜던트 갓 차광 강화 ③ 손목시계(왼손) ④ 추가 대기 자세(손으로 입 가리기, 한 팔 테이블) ⑤ Game View 비교 검수 → 커밋 → 백업
- **게임 순서 (2026-11-22)**: 게임 시작 = 302호 씬 → 브리핑(Enter 수사 시작) → 현장 조사(좌상단 확보 증거 수, 서버 기준) → Tab 수사 수첩 → Enter 경찰서 복귀(서버 scene→desk, 사건 시각 +38분) → `Case001_Interrogation` 로드(서버 프로세스 유지, 증거 그대로) → 호출 대장 → 심문. `TZCaseFlow`가 302 씬에 런타임으로 붙음(씬 재빌드 불필요)
- **심문 대화 UX (2026-11-22, 사용자 피드백 반영)**: 보내기 즉시 입력창 숨김 → 질문 표시 → "이서연 · · ·" → 답변 느리게 타이핑(구두점에서 멈춤) → 화면에 유지, Space·Enter·클릭으로 계속 → 입력창 복귀, 직전 답변은 입력창 위에 흐리게 유지
- 미구현: 심문 후 현장으로 돌아가기 버튼(서버는 desk→room302 허용), 302 브리핑 뒤 HUD 사물 안내가 희미하게 비침
- UI: 심문 중 좌·우 패널 기본 숨김(Tab 인물 기록 / E 증거 / R 심문 행동 / Q 추천 질문 / Esc 종료)

## 3. 빌드·검수 파이프라인
```
# 302호 / 심문실 / 이서연 (Blender)
blender -b --factory-startup -P blender/scripts/build_room302.py -- <repo>/blender/out/Room302.fbx <repo>/blender/source/Room302.blend
blender -b --factory-startup -P blender/scripts/build_interrogation.py -- <repo>/blender/out/Interrogation2.fbx <repo>/blender/out/Interrogation2.blend
blender -b -P blender/scripts/build_seoyeon.py            # MPFB 확장이 필요하므로 --factory-startup 없이
# Unity (에디터 열린 상태)
unity command script eval --code 'return TableZero.EditorTools.TZSuspectCharacterBuilder.Import();'
unity command script eval --code 'return TableZero.EditorTools.TZInterrogationBuilder.Build();'
unity command editor set_auto_tick --enabled true
unity command editor.playmode start
```
- Play Mode 진입 시 `TZServer`가 Python 서버를 랜덤 토큰·포트로 자동 실행(qwen3:4b CPU)
- 심문 확인: 플레이 중 `TZInterrogationScreen`의 `Select(1,true)` + `CallSelected()`(리플렉션) → 이서연 입실. 카메라를 RenderTexture로 1920x1080 렌더해 확인(Game View 창이 작으면 캡처가 확대되어 노이즈처럼 보임)
- 좌표: Unity x = −Blender x, Unity y = Blender z, Unity z = −Blender y

## 4. 성능·AI 실측
- 302 벤치 빌드(2070S 1080p): 기본 55.4 avg / 28.0 1% Low. 반사 프로브 1회 렌더·손전등만 그림자·TAA→SMAA 3종 모두 적용 시 176.6 / 105.7 (`qa/logs/perf/BENCH_SUMMARY.md`) — 302 빌더에 아직 미적용
- AI 응답 30~47초(qwen3:4b CPU) — 출시 불가 수준. AI 동시 실행 중 FPS 미측정

## 5. 서버
- 테스트: `python -m unittest discover -s tests` (134개 통과)
- 응답 계약: reply_mode 8종, motion_id 16종(`server/runtime.py` ALLOWED_MOTIONS) → Unity `TZSuspectActor.PlayMotion`
