# 다음 AI 인계지시서 (Claude Code / Codex 공통)

## 0. 먼저 읽기
1. 바탕화면 `TABLE_ZERO_개발현황/개발현황.md` → 이 파일 → `미완성작업.md`
2. 사용자 원본 지시: `docs/TABLE_ZERO_CLAUDE_CODE_V11_FINAL_MASTER_DIRECTIVE.txt` + 백업/인계 규칙 + **로컬 AI 우선(유료 API 금지)** 정책
3. 실제 프로젝트: `C:\Users\imcok\Documents\TABLE_ZERO` (ZIP은 백업본). `git log --oneline -20`

## 1. 절대 규칙 (사용자 확정)
- 도형 캐릭터/장난감 소품을 완성품으로 쓰지 않는다. 없으면 `RELEASE_BLOCKED_ASSET`로 표기
- 사건 진실은 `reference/CASE001_CANON_LOCKED.json`만. 클라이언트·LLM에 통째 전달 금지
- `reference/CASE001_SUSPECT_PERSONAS_SERVER_ONLY.json`도 서버 전용
- 감정·거짓말 퍼센트 UI 금지, 빨간 정답 하이라이트 금지, 인게임 대사 끝 마침표 금지
- 세션 끝에 반드시 `pwsh -File tools/backup_full.ps1 -Label "<요약>"` → 출력 `BACKUP_OK` 확인

## 2. 빌드 파이프라인 (재실행 가능)
```
# 1) 3D: Blender로 302호 생성
"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -b --factory-startup -P blender/scripts/build_room302.py -- <repo>/blender/out/Room302.fbx <repo>/blender/source/Room302.blend
# 2) Unity 씬 생성 (에디터 열린 상태)
unity command script eval --project-path TableZero.Unity --timeout 900 --code 'TableZero.EditorTools.TZRoom302Builder.Build(); return "ok";'
#    → data/room302_prop_positions.json (서버 거리 검증용) 과 qa/logs/room302_renderer_coverage.tsv 갱신
# 3) Play Mode 검수 (포커스 없을 때 프레임 정지 방지)
unity command editor set_auto_tick --project-path TableZero.Unity
unity command editor.playmode start --project-path TableZero.Unity
pwsh -File tools/qa_unity_tour.ps1 -Tag <태그>        # 12컷 1920x1080
```
- Play Mode에 들어가면 `TZServer`가 Python 서버를 **랜덤 토큰으로 자동 실행**(qwen3:4b, CPU)
- 좌표: Unity x = −Blender x, Unity z = −Blender y, Unity y = Blender z

## 3. 서버
- 테스트: `python -m unittest discover -s tests` (132개)
- 라이브 AI 평가: `python -I tools/ai_eval.py --models qwen3:4b --seeds 11 23 37` (환경변수 `TABLEZERO_OLLAMA_NUM_GPU=0`)
- 주요 모듈: `suspect_mind.py`(기억 격리·가드), `interview_service.py`(재시도·시간 규칙), `case_flow.py`(소품 권한·채취 절차·데스크 요청/예산), `episode_controller.py`(장면·시계·자율행동)

## 4. 바로 이어서 할 일
`미완성작업.md`의 P0부터. 특히 심문실 씬과 로컬 모델 품질 재평가.
