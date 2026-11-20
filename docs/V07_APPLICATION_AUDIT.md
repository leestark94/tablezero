# V0.7 USER DIRECTIVE — 적용·검증 매트릭스

원본: `reference/MASTER_DEVELOPMENT_DIRECTIVE_V07_ORIGINAL.txt`

| V0.7 요구 | 유지/신규 파일 | 검증 상태 | 실사 게임으로 마치기 위해 남은 일 |
|---|---|---|---|
| 기존 V0.3~V0.6 코드 우선 | 기존 V0.9 작업 사본·reference | V0.9 로컬 코드만 확인 | 사용자가 실제 개발 중인 Codex 저장소 diff·병합 |
| AI는 정답·타인 비밀 모름 | `server/runtime.py`, `server/episode_controller.py` | Python 테스트 | 실제 LLM 장기 테스트/프롬프트 누설 시험 |
| AI 자율 행동은 세계 변화 | `server/runtime.py`, `server/incidents.py` | Python 사례 테스트 | 게임 씬과 실제 NPC·전화·새 조사 경로 연결 |
| 진술은 미검증 주장 | `server/api.py`, `server/runtime.py` | 신규 계약 테스트 | 사람 감수로 한국어 대화 20턴 × 30세션 확인 |
| 상황 조건별 연출 | 기존 82 목록 + 사건별 비트 | Python 규칙 테스트 | 손 동작·접촉 프레임·음향·물리 prefab 결속 |
| 한국형 생활공간 | 기존 narrative/asset 지침 | 설계만 | 한국형 빌라·조사실 자체 제작·실사 에셋 선정 |
| 1인칭 조사 손과 물체 | `unity/Runtime/TZFirstPersonInvestigation.cs` 등 | C# 소스 작성 | 손 리깅·접점 IK·Unity 실제 에디터 검증 |
| AI 1대1 심문 | `server/providers.py`, `TZInterrogationPerformance.cs` | 규칙·코드 작성 | 실제 AI 연결, 얼굴·손·호흡 애니메이션 검증 |
| 5개 심문 국면 | 기존 연출 데이터/마스터 지시 | 설계 단계 | 독립 AI 판단→현장 acting 한 장면 연결 |
| 한국어 생활 표현, 억지 감정 힌트 금지 | `data/case001_scriptbook.json`, `server/dialogue_quality.py` | 정적 대사 검사 | 음성연기·성우/한국어 작가의 실제 감수 |
| UI의 물체 중심 정보 표시 | 기존 1인칭 조사 코드 / V10 desk | 부분 구현 | 3D 앵커 위치, 손으로 증거 조사 시 정합 테스트 |
| 수사 기록 메뉴/버튼 작동 | `CaseDesk.uxml`, `CaseDesk.uss`, `TZCaseDeskUI.cs` | UI 코드 작성·Python 계약 테스트 | Unity UI Toolkit 컴파일/실제 입력/폰트/카메라 포커스 검증 |
| 증거 출처·한계·비교 | **V10 신규** `TZCaseDeskUI.cs`, `server/api.py` | 데이터 노출·계약 테스트 | Unity에서 자료 고정/해제·선택 상태 사람 검수 |
| 수사 기회/입증 네 축 | 기존 server/episode_controller, outcomes | Python 테스트 | 플레이어 이해도·난이도·경제성 밸런싱 |
| 성공·실패·오인 결말 | 기존 `server/outcomes.py`, 연출 데이터 | Python 분기 테스트 | 5개 결말 컷·음성·실사 캐릭터 반응 제작 |
| 몰입·공포·긴장 연출 | 기존 docs, 감독 비트 | 데이터·연출 규칙 | 현장음 믹스, 역광, 물리/애니메이션 실제 검수 |
| AI API·키 서버 격리 | 기존 `server/api.py`, `providers.py` | 로컬 dev 보안 테스트 | 실제 운영 서버 인증·세션·비용·관측 체계 |
| 'AI티' 없는 3D 결과 | 기존 아트 감수 tool | 자동 거름망만 | 사용자가 직접 스크린샷 확인, Blender 재모델링 |
| 12단계 연속 실제 플레이 | 통합 구조 | **미완료** | Unity Play Mode 12단계 단일 녹화 필요 |

### UI 이전 상태에 관한 판단
V0.9 UI는 네비게이션·메뉴 열기·질문·보고 이벤트 구조가 있었지만 자료 선택 후 세부 한계 표시, 두 자료 비교, UX 검토용 별도 시연물은 부족했다. V10에 이 기능을 추가했다. **그러나 전문 게임 화면의 최종 그래픽·사용성 승인과 Unity 실행 검증은 여전히 미완료**다.

### 끝까지 지켜야 할 금지사항
- 네모난 임시 도형·외국식 실내·작위적 용의자 몸짓을 완성 게임 씬에 투입 금지
- 모든 인물에 같은 말투·같은 욕설·같은 침묵 길이 사용 금지
- 상대가 화를 냈다는 이유로 유죄 추측·거짓말 게이지 자동 표시 금지
- 신문 거부·변호인 요청을 자백 유도 버튼처럼 취급 금지
- 임의 계정·API 키·유료 에셋·Steam SDK 기능을 승인 없이 생성·구매 금지
- V0.7을 실제 Unity Play Mode 구현 완료로 보고하는 행위 금지
