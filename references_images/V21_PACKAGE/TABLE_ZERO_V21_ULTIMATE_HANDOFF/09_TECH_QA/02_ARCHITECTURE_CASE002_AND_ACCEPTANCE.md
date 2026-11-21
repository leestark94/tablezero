# TABLE//ZERO — 공통엔진/Unity/AI/음성/저장 아키텍처와 완료 기준

## 1. 'CASE 001'과 'CASE 002 이상'의 정확한 구분

**코드/서버 공통:**
- `GameFlowController`: 실제 씬 전환, 첫 배정, 허브, 최종보고, 엔딩.
- `CaseRegistry`: 지정된 사건 패키지의 스키마 검사·버전/서명·캐시·일련 ID 분리.
- `ActionBudget` / `CostCommitter`: 수사분 예약·확정·롤백, 중복 이벤트 방지.
- `WorldClock` / `ShiftTransition`: 실제 사건 달력·검사 회신 시점(수사분과 별도).
- `SceneInspectionRegistry`: 현실 3D 물체 ID, 인스턴스 상태, 조작, 사진, 수집·봉인.
- `EvidenceCatalog` / `EvidenceProvenance`: 증거 원본, 출처, 독립소스 가족, 법적 절차, 확실성.
- `InterviewOrchestrator`: 마이크/채팅 입력 → 인물별 응답 계획 → 검사 → NLG/TTS/리깅 → 기록.
- `SuspectMemoryProjection`: 정본 `CaseTruth`를 해당 인물이 직접 아는 사실/추정/오해/공개 증거로 축소해 공급.
- `PersonaPolicy` + `PsychologicalState`: 인물의 성격·관계·위험·감정·자기보호 행동.
- `OfficerBeliefModel`: 인물이 자신을 조사하는 형사의 질문과 공개 증거만 보고 추론하는 모델.
- `ClaimLedger`: 모든 진술의 원문·시점·전제·수정·모순·공개 이력 append-only.
- `ForensicQueue`: 원본 채취/적법성/의뢰 종류/게임 세계 회신 시각, 결과 데이터.
- `ConditionalEventDirector`: 사실·시간·외부 통신 조건을 모두 검증하고 돌발 이벤트 실행.
- `FinalReportEvaluator`: 증거와 논증의 출처·독립성·반증 검토로 수사 의견 평가. **LLM 판단 금지.**
- `SaveLoad`: 사건 ID, 예산, 증거, 공개 사실, AI 진술, 사건 세계 상태, 이벤트 1회성, 보고서 초안/제출 상태 일관 저장.

**사건별로 교체:**
- `CaseTruth`, `Characters`, `PublicBrief`, `SceneHotspots`, `EvidenceCatalog entries`, `InterrogationClaims`, `ConditionalEvents`, `ProofRequirements`, `EndingScripts`, `ChapterAssets`, `Timeline`. 
- CASE 002 새 사건은 V21의 박현수·정수연·480만원을 **서버 프롬프트와 런타임/세이브에서 상속하면 실패**. 인격 엔진 코드만 재사용하되 성격과 사연은 사건별.

## 2. 런타임 데이터 권한 아키텍처

```text
Unity 6 (3D & HUD)
  UIInput / Mic / SceneInteraction / Dossier / EvidenceViewer
          ↓ confirmed action + only offered evidence IDs
Trusted Local Game Service
  ├─ Budget (reserve → commit/rollback)
  ├─ CaseTruth [PRIVATE per current case]
  ├─ SuspectMemoryProjection [ONLY speaker facts]
  ├─ Evidence & Claim Ledger (append-only)
  ├─ Forensics/WorldClock/LegalAccess/Event Director
  ├─ Interview strategy selection (avoid / deny / narrow / admit / refuse)
  ├─ Controlled LLM prompt (only permitted facts + chosen response constraints)
  ├─ Claim Safety Validator (hallucination / temporal leak / unsupported admission)
  └─ Atomic state commit / save
          ↓ validated response text, animation intent, visible result
Unity — TTS/STT/Animation/Subtitles/Transcript
```

특히 Unity 게임 오브젝트 네이밍에 `CULPRIT_PARK`나 `KILLER_BLOOD_X`처럼 유저가 UI로 볼 수 있는 정답을 싣지 말라. 단 로컬 PC에서 완전한 역공학 방지를 약속하지 말라; 일반 게임플레이/UI·LLM 프롬프트와 로그에서 정답 누출 차단이 목표.

## 3. API/데이터 계약 (의미상 프로토콜)

### 3-A. `InspectObject`
입력: `{case_id, prop_id, requested_action: look|rotate|read|photograph|collect, player_position, state_revision, nonce}`
결과: `{visible_observation, animation_intent, cost_committed, evidence_unlocks[], world_mutation?, save_revision}`. 
- LOOK/READ=0, PHOTO=1, COLLECT=3 초깃값. 파손/오염 주의 및 합법적 수집 권한 검사. 같은 소품 사진 중복 과금 X.

### 3-B. `InterviewTurn`
입력: `{case_id, session_id, suspect_id, turn_uuid, channel: text|mic, confirmed_question, offered_evidence_ids[], selected_tactic, state_revision}`
결과: `{response_text, subtitle_segments, animation_intent, claim_ids, disclosed_evidence_ids[], officer_model_delta, valid_turn, final_cost, save_revision}`.
- 성공한 1개 턴만 코스트. 텍스트/마이크 동일 엔진. STT 확인 전 비용 없음.
- `turn_uuid`로 멱등성. timeout 후 retry 시 같은 UUID는 완료/롤백 중 하나로 복원. 두 번 비용 차감 금지.
- 비공개 `CaseTruth`와 `culprit_id`를 LLM의 원문 context에 전부 통째로 넣지 말라.

### 3-C. `RequestForensics`
입력: `{evidence_id, test_type, source_integrity, legal_basis, budget_quote, request_uuid}`
결과: `{request_status, receipt_id, cost_committed, world_result_due_shift, dependencies, limitations}`.
- 요청 단계에서 판정값·정답 미공개. 회신은 고정 사건 원본/출처에 따라 계산된 데이터, 모델의 자유발명이 아님.

### 3-D. `SubmitReport`
입력: `{accused_id_or_hold, claim_chains:[{axis, authored_statement, cited_original_evidence_ids[], cited_claim_ids[], alternative_discussion}], final_submission_uuid}`
결과: `{accepted_submission, case_result_code, disclosed_postgame_summary, saved_revision}`.
- 제출 가능한 상태와 성공 판정은 다른 개념. 이름을 누른 것만으로 성공 처리 금지.

## 4. AI의 실제 인격과 '수만줄 대사' 문제
- **정적 대사 수만 줄을 인물에게 주입하지 말 것.** 소설·드라마 바이블은 인물들이 과거에 어떤 삶을 살았는지와 심리전 선택 이유를 정하는 정본이다.
- 사건 사실·거짓말/진술전환 규칙은 정형 데이터로 두고, LLM은 `무엇을 말할지`보다 `어떻게 말할지`의 언어 다양성을 주로 책임진다.
- 조사가 길어져도 발화전략이 `인정→정정→반론`처럼 무한 진전하지 않도록 `fact gate`와 `ClaimLedger`를 사용.
- `OfficerBeliefModel`이 형사의 허세를 탐지할 가능성은 있으나 미공개 서버 증거를 훔쳐보는 능력은 없음.
- 모델 출력의 할루시네이션이 통과하면 금지된 미래 사실·검사 결과가 새로 생겨 사건 해결 자체가 오염되므로 각 발화 뒤 의미·시각·인물 지식 검증 필요. 검증 실패 후에는 사건과 모순 없는 제한적 회피답변을 사용하되 동일 문장 무한 반복 금지.
- 인격의 고유한 생활언어(수연 호칭, 도현 시간 표현, 서연 업무용 단어, 현수 정산·서류 표현)는 **얼굴이 아닌 말만 들어도 구별 가능할 정도**를 목표로 검수. 단 범인만 특정 신호를 갖게 해서는 안 됨.

## 5. 진술거부·압박·법적 고증
- 일상 참고인 면담과 피의자 신문/강제수색을 같은 UI 자격으로 처리하지 말 것.
- 변호인 요청/진술거부/휴식·면담 취소는 적절한 상태/조건에서 가능; 해당 캐릭터가 범인이라는 자동 신호 금지.
- 책상 내리치기·고성은 실제 행동으로 비용 12/6과 기록 리스크, 반응 및 절차문제로 연결 가능하나 자백 확률 상승/진술 신빙성 보상 금지.
- **한국 수사법·개인정보·감식 실무는 출시 전 별도 실무 고증**해야 하며 '게임 코스트'가 현실 수사규칙인 것처럼 홍보하지 말 것.
- 사망확인/부검·감정과 관련한 현실성 역시 의료·과학수사 자문 전 작가 가안/검수 필요 영역으로 표기.

## 6. Unity/성능/에셋
- Unity 6 씬 구조는 현재 프로젝트를 실제로 감사해 확정. 보유 에셋과 승인된 아트가 있으면 그대로 유지.
- 캐릭터3명 각 본체 리깅/표정/눈/호흡/가슴/손 IK/립싱크/증거받기/침묵 모션. TTS가 없는 경우에도 텍스트로 완주 가능.
- 3D 현장 고품질 라이트맵·실제 원룸 스케일과 낮은 탁자·충돌 경로 현실성. CCTV 실제 화각을 캐릭터 트랜스폼으로 검증, 편리한 가짜 카메라 데이터 삽입 금지.
- 테스트 머신 Ryzen 7 5700X / RTX 2070 SUPER / RAM32GB 수준, 1080p 60fps **목표값**(실제 측정 전 달성 주장 금지). 로컬 LLM 대기 중 렌더가 멈추지 않는지 측정. 미완료 아트/모션은 코드로 속이지 말고 명시.

## 7. 오류 처리 및 세이브 무결성
- `ActionBudget`는 잔액과 사용 내역을 일관되게 저널링. 유효 턴→성공 응답→원자적 commit. 완료 실패가 났으면 재시도·취소·환불 중 명확한 한 상태.
- 저장 포함 필수: `case_id`, story version, current scene, world clock, budget & transactions, seen/clipped props, provenance, claim history, suspect trust/emotions, officer belief per suspect, forensic requests + ETA, unlocked events, final report draft and submission count, RNG seed for presentation only.
- AI 모델 바꿨을 때 이미 했던 진술이 불일치하지 않도록 **의미적 불변 진술**은 엔진에서 유지. 대사 표면은 다음부터 바뀔 수 있으나 확인된 진술은 로그에 남아야 한다.
- 저장/로드 이후 심문 질문의 누적 비용 또는 저장된 증거 상태가 초기화되면 P0 버그.

## 8. 필수 테스트 분류와 완료 정의

### P0 절대 실패
1. V16 `s2` 정답이 서버에 살아 있어 001 결과 판정에 섞임.
2. 다른 용의자의 비공개 비밀을 AI가 원문으로 유출.
3. 스포일러가 브리핑·씬 명칭·HUD에 표시.
4. 진범만 특별한 표정/행동으로 튀어나옴.
5. 21:17/21:42/21:57의 세 충돌을 LLM이 같은 사건으로 설명.
6. 이서연의 옷에 혈액만 있고 박이 현장에 접촉했다는 객관 근거가 없음.
7. 마이크에서 실수로 재전송하여 2회 비용 차감.
8. AI 서버 에러/강제종료 후 비용만 차감되고 답변 없음.
9. 범인 이름 클릭만으로 정식 성공.
10. CCTV에 실제 보이는 장면을 편의대로 숨김.
11. 정본에 없는 '결정적 CCTV 복원'/'고의 시계 오차'를 갑자기 생성.
12. 외부 공개 문서/프로필에 정확한 진범/치명상 시각 공개.

### P1 실제 완료
- 메인 메뉴→사건배정/스킵→사건 브리핑→302호 조사→허브→3명 선택적 심문→유효 음성/채팅 질문→자료 요청/회신→보고서→결말까지 Windows 빌드 1회 실제 완주.
- 모든 UI 버튼(우클릭/키보드/패드 대체 포함) 실제 기능·에러경로; 장식 버튼·가짜 데모 버튼 없음.
- 208개 원본 ID가 존재하며 최종 유지/통합/배경/제거 후보 매핑은 씬 검증 증거 포함. 핵심 18개 조사 묶음은 게임내 체감 의미 있음.
- AI 3명 x 50개 이상 사건별 질문 변형 및 공통 002용 더미 사건 100턴 테스트, 별도 QA CSV의 반증 테스트 통과.
- 범인 자백 없이도 진실 입증 경로, 정답 지목만 하면 실패, 오인 보고서·시간소진·절차문제 등 엔딩 진입.
- 실제 녹화 영상/로그/성능 지표/불합격 항목 제출.

### P2 품질 목표
- 외부 테스트에서 45~70분 평균 완주 가능, 심문 체감 중심, 힌트 없이 사건 흐름 이해 가능.
- 인물별 사소한 관계 대화에서 자연스러운 유머/건조한 반응/상처가 드러나지만 사건 비밀은 최초부터 덤프되지 않음.
- 수사 비용을 왜 냈는지 미리 이해, 컷신·로딩·번역 오류로 시간 손실 없음.
- 실제 AI 지연/입력 중 3D 화면 유지, TTS 실패해도 텍스트로 완주.

## 9. CASE 002 실전 격리 시험

작은 더미 사건을 실제 실행하도록 만들 것(`CASE002_SMOKE`는 출시에 사용하지 않음).

- `case_id = 002_test`에 새로운 장소·피해자·관계인·단서 3개·증거 2개·시간 1개·거짓 진술 하나를 **직접 지정**.
- 기존 `InterviewOrchestrator`를 수정하지 않고 `CaseRegistry.Load(002_test)`만 호출.
- 3인 서로 다른 성격/언어를 넣고 100턴 랜덤 의미 변형 질문.
- 001의 `정수연/강도현/이서연/박현수/480만/302호/21:57`이 출력되면 불합격. 로그·메모리·클라이언트 디버그 UI도 검사.
- `case_id` 없이 전역 인물 상태/증거 상태가 이어지면 불합격.
