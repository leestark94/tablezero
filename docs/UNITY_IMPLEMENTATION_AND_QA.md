# Unity 에디터 통합 및 QA 우선순위

## 1 Git/충돌 점검
- Codex가 만든 최신 Git 브랜치에 체크포인트/백업 생성
- Unity 패키지 버전 확인: Unity 6, UI Toolkit, Input System, Cinemachine, Timeline, Animation Rigging, URP/HDRP
- 기존 `TZCaseDeskUI`, `TZCaseDeskBridge`, `server/api.py`와 이름/경로/기능별 diff를 비교하고 충돌을 설명할 것
- `reference/CASE001_CANON_LOCKED.json`은 서버 전용. StreamingAssets·Resources·Addressables로 복사 금지

## 2 UI 구성
1. `UIDocument`에 PanelSettings와 `unity/UI/CaseDesk.uxml`을 할당
2. `TZCaseDeskUI` 컴포넌트 할당. `designSheet`에 `CaseDesk.uss`를 연결하고 `investigator`에 실제 1인칭 컴포넌트 할당
3. `TZCaseDeskBridge`에서 `ui`와 `bridge` 연결
4. 기존 입력 처리기에서 TAB→`ui.Toggle()`, ESC→`ui.HandleEscape()`를 UI 포커스 상태에 따라 연결. 기존 INPUT 시스템이 있다면 별도 중복 입력기를 생성하지 말 것
5. 폰트: 상업 재배포 가능한 라이선스가 확인된 한국어 폰트 에셋을 프로젝트로 가져와 실제 화면에서 glyph 누락·읽기 난이도를 검증
6. 교차 패널 상태·자료 선택·이전 화면 복귀·기록 갱신 중 UI가 튀지 않는지 확인

## 3 서버 상태
- `python -m unittest discover -s tests -v` 테스트를 먼저 실행
- 서버 dev bridge는 `127.0.0.1`과 개발용 토큰으로만 사용; public/prod가 아님
- 실제 LLM은 Ollama 또는 승인한 유료 API 서버에서 호출. 테스트 모드는 LOCAL PREVIEW 배너를 반드시 표시
- 진범/비공개 사실은 Unity 응답에서 공개하지 말 것. 레코드가 화면에 보이면 서버 획득 이력이 존재해야 함

## 4 시각적 릴리즈 게이트
- 현장: 한국형 빌라의 콘센트, 현관 구조, 도어락, 가구/문, 실측 스케일
- 인물: 손과 팔 T/A pose 및 contact pose, 손톱·피부 셰이더, 옷깃·상체 무게 중심, 음성/호흡
- 물리: 한 손 접촉 프레임 + 컵/서류 진동 + 사운드와 카메라 흔들림 일치
- UI: 1920×1080, 2560×1440, 3440×1440에서 본문 가독성, 정렬, 포커스 복귀, 모든 메뉴 작동
- UX: 한 장면 5분 관찰 시 '의미 없는 반복 손짓/가짜 SF 팝업/기계적인 대사/무관한 소품'이 있으면 실패
- 화면과 영상을 직접 본 사람의 기록이 없으면 QA 통과로 표시하지 말 것

## 5 완성·미완성 보고
완료: 실제 경로, 빌드/로그, 서버 권한 검증, 녹화 파일
미완료: 모델/모션/성우/동작 연출/물리/서버 운영 환경/유료 API 승인 등
차단: 정확한 원인, 필요한 자산, 누구의 결정을 기다리는지

**현재 산출물은 코드 통합 후보. Unity 게임의 최종 실행/시각 검증 결과가 아니다.**
