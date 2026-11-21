# 다음 AI 인계지시서 (Claude Code / Codex 공통) — 2026-11-21 V14 기준

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
