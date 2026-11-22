# 인계 프롬프트 (계정이 바뀔 때마다 새 Claude Code 세션에 그대로 붙여 넣기)

```
너는 《TABLE//ZERO》 CASE 001 "302호의 밤"(한국형 실사 1인칭 수사 스릴러, 로컬 LLM 용의자)을 이어서 개발하는 Claude Code다.
이전 세션(다른 계정일 수 있음)의 작업을 그대로 이어받는다. 처음부터 다시 만들지 마라.

[1. 프로젝트 가져오기]
- 이 PC에 C:\Users\imcok\Documents\TABLE_ZERO 가 이미 있으면: 그 폴더에서 git checkout dev/v11-integration → git pull → git lfs pull
- 없으면: git clone https://github.com/leestark94/tablezero.git TABLE_ZERO → cd TABLE_ZERO → git checkout dev/v11-integration → git lfs install → git lfs pull
- 그다음 git log --oneline -15 로 마지막 작업을 확인한다.

[2. 반드시 먼저 읽기 (이 순서)]
1) docs/status/다음AI_인계지시서.md — 설치할 도구, 절대 규칙, 현재 상태, 남은 작업, 빌드 명령
2) docs/status/개발현황.md, docs/status/미완성작업.md, docs/status/변경이력.md
3) references_images/V21_PACKAGE/TABLE_ZERO_V21_ULTIMATE_HANDOFF/01_CLAUDE_CODE_ULTIMATE_PROMPT.md — 현재 최우선 지시(V21.1: 진범 박현수, 메뉴→엔딩 완주 게임). docs/v21/P0_CONFLICT_REPORT.md 로 진행 상황 확인. (V14 지시는 3D 품질 참고용)
4) references_images/ 의 승인 이미지(INTERROGATION_TARGET_VISUAL, SCENE_302_TARGET_VISUAL, V14/*)를 직접 본다.

[3. 절대 규칙]
- 유료 크레딧(Higgsfield·Tripo·Meshy 등)·유료 API·에셋 구매는 비용을 먼저 말하고 사용자 승인 후에만. 무단 사용 금지
- 미완성·미검증을 완성이라고 보고하지 마라. 코드 작성 ≠ 실제 완성. Unity Game View(또는 1080p 카메라 렌더)로 직접 확인하고 말한다
- 사건 진실(reference/CASE001_CANON_LOCKED.json)·서버 전용 페르소나는 Unity·LLM에 통째로 넘기지 않는다. 정답 힌트·거짓말 확률·감정 게이지 UI 금지
- 심문실 얼굴 규칙: 프로필은 선명한 실사 사진, 3D 심문실의 같은 인물은 눈·얼굴 윗부분이 조명·자세·머리카락으로 자연스럽게 어둠(검정 오버레이 금지)
- 승인된 용의자 호출 화면(좌 서류 대장 + 우 인물)을 카드형으로 되돌리지 않는다. EXAONE 금지
- API 키·비밀번호·토큰을 저장소에 넣지 않는다 (GitHub 저장소는 공개 상태)
- 사용자는 쉬지 않고 실제 게임 화면으로 검증하며 계속 개발하기를 원한다. 불필요한 질문은 줄이고, 결정이 필요한 것만 묻는다

[4. 바로 이어서 할 일]
다음AI_인계지시서.md 맨 위 "★★★ 최신 — V22-2" 블록과 docs/status/V22_종합평가.md 부터 따른다 (Codex 실플레이 QA 17건 대응 상태표 포함).
최우선: 우회 없는 새 사건→엔딩 실플레이/standalone 검증, UI 해상도 확인, 지연 재측정(첫 표시 목표 p50 1s 미달성), 박현수·강도현 슬롯 보강, 이서연 사실감(2D 레이어 아트 또는 MetaHuman). 사용자는 모바일이라 PC를 못 본다: 선택을 되묻지 말고 구현→플레이→수정→검증, 이서연 결과 이미지는 채팅에 직접 표시.

[5. 세션을 끝낼 때마다 (무한 인계 규칙 — 생략 금지)]
1) docs/status/다음AI_인계지시서.md 를 현재 상태로 갱신 (한 일, 확인 방법과 결과, 남은 일, 새로 설치해야 하는 도구, 주의점)
2) 개발현황.md / 미완성작업.md / 변경이력.md 갱신
3) 테스트 실행: python -m unittest discover -s tests (결과를 그대로 기록)
4) git add -A → git commit → git push (브랜치 dev/v11-integration). push가 원격과 일치하는지 git rev-parse HEAD origin/dev/v11-integration 로 확인
   - Git LFS 무료 용량(1 GB)이 거의 찼다. 큰 바이너리를 올리기 전에 사용자에게 알린다
5) 가능하면 바탕화면 백업: pwsh -File tools/backup_full.ps1 → BACKUP_OK 확인 (이전 백업 삭제·덮어쓰기 금지)
6) 사용자에게 이 파일(docs/status/HANDOFF_PROMPT.md)의 프롬프트를 다시 보여 주며 "다음 계정에 이걸 붙여 넣으면 이어집니다"라고 알린다.
   프롬프트 내용이 바뀌어야 하면(새 규칙·새 우선순위) 이 파일도 고쳐서 함께 push한다.
```
