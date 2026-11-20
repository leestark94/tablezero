# MIGRATION_AND_CONFLICTS

- 기존 로컬 TABLE//ZERO 프로젝트 없음 (BlackLedger_EP01은 다른 게임) → V11 ZIP을 유일한 소스로 `833f127`에 원본 보존
- `unity/` → `TableZero.Unity/Assets/TableZero/{Scripts/Runtime,Scripts/Editor,UI,Data}`로 이동, 테스트 경로 갱신
- 중복 기능 정리:
  - `TZFirstPersonInvestigation`(V10, 손 리그 전제) ↔ 새 `TZPlayerController`: 씬은 새 컨트롤러 사용. 1인칭 손 에셋 도착 시 V10 컴포넌트의 hands/evidence 경로를 새 컨트롤러에 병합 예정
  - `TZPropFocusController`(V11) ↔ `TZInteractionDirector` 내부 레이캐스트: 디렉터가 같은 규칙(CanTarget+거리)으로 포커스 처리. FocusController는 미사용(삭제하지 않음)
  - `TZLocalBridgeClient`(V10, 수동 토큰) ↔ `TZServer`(자동 실행·랜덤 토큰): 새 코드는 TZServer 사용
  - `EpisodeController.question()`(V08) ↔ `InterviewService.ask()`(V11): 실제 경로는 InterviewService (시간 규칙·재시도·가드)
- 데이터 권한: 소품 위치는 Unity 빌더가 덤프한 `data/room302_prop_positions.json`이 기준, 관찰 문장은 `data/room302_scene_notes.json`이 manifest 문장을 덮어씀
- 테스트 변경: `test_19_contact_after_clock`는 장면 이동이 사건 시계를 소모하도록 바뀌어 시계를 22:07로 고정한 뒤 검증
