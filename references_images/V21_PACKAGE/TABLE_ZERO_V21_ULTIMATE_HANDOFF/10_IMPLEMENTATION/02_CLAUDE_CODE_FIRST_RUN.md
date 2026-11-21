# Claude Code에 전달할 때 실제 작업 절차

1. **기존 Unity 프로젝트 폴더를 열고** 이 ZIP 전체를 참조 자료 폴더(`design/V21_ULTIMATE`)에 풀어 둔다. 현재 Unity 프로젝트 **전체를 이 ZIP으로 덮어쓰지 말 것**. 본 ZIP은 설계문서이고 Unity 원본 프로젝트는 아니다.
2. 메인 명령 `01_CLAUDE_CODE_ULTIMATE_PROMPT.md`를 Claude Code에 읽히게 하고, `00_START_HERE.md`의 참조 우선순위를 함께 제공한다.
3. Claude에게 현재 프로젝트 상태(`Scenes`, `Prefabs`, `MonoBehaviour`, 실제 호출 로컬 AI, 미커밋 변경)를 먼저 감사하게 한다.
4. **V21 진범 박현수**를 정본으로 고정한 뒤 구버전 V16 이서연 정답 레퍼런스를 분리하게 한다.
5. 메인 메뉴~엔딩까지 우선 구현 후 각 씬을 AI/현장/수사분/포렌식과 이어 붙인다.
6. `08_UI_UX/04_CLICKABLE_UX_PROTOTYPE.html`은 **로컬 브라우저로 열어 동작과 배치만 참고**한다. 단순 HTML을 게임에 붙여 넣는 대신 기존 승인 Unity UI와 조화시킨다.
7. `09_TECH_QA`의 테스트와 `10_IMPLEMENTATION` 개발 정의가 맞을 때까지 '완료'라고 말하지 않는다.

## Claude에 처음 보낼 최소 요청문

> 첨부한 TABLE_ZERO_V21_ULTIMATE_HANDOFF.zip을 모두 읽고 `01_CLAUDE_CODE_ULTIMATE_PROMPT.md`의 명령을 지금 열어둔 Unity 6 프로젝트에 적용해줘. V21의 진범은 박현수(s3)다. 기존 Unity/3D/AI 코드를 보존하고, 첫 단계에서 현재 상태와 V16~V20 충돌을 감사한 뒤 **메뉴→사건 브리핑→302호→수사본부→마이크·채팅 AI 심문→포렌식→수사보고서→엔딩**의 완주 가능한 게임 루프를 구현해. 화면 레이아웃과 조작은 `08_UI_UX/01_COMPLETE_GAME_UX_SPEC.md`, 심문 공통 로직은 `03_AI/INTERROGATION_CORE_ENGINE.md`, 사건 진실은 `01_CANON/CASE001_V21_TRUTH.json`을 각각 최상위 기준으로 해. 첫 통합 후 실제 Unity Play Mode 오류·미연결·남은 일을 숨기지 말고 기록해.
