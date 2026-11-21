# CASE 001~N 공통 AI 심문 엔진 구현 계약 — V21

## 0. 공통엔진 / 사건데이터 분리
공통: `InterviewOrchestrator`, `QuestionIntentResolver`, `PersonaPolicy`, `KnowledgeProjection`, `ClaimLedger`, `OfficerBeliefModel`, `PsychologicalState`, `EvidenceDisclosureRegistry`, `RightsAndRefusal`, `AnimationIntentDirector`, `SpeechAdapter`, `CostCommitter`, `AdversarialTestHarness`.
사건별: 고정 사건 진실, 직접 목격/간접 들음/추정/착각, 인물 외형·이력·성격, 인물별 숨길 이유, 각 진술 정책, 증거별 입증범위, 스토리 이벤트. `CASE001` 코드 분기 대신 선언형 데이터.

## 1. 원천적으로 막아야 할 치명적 실패
- 세 인물이 공통으로 “제가 거짓말한 건 맞습니다”, “그게 살인과는 다른 얘기잖아요”라고 스스로 논점을 정리해 주는 패턴 금지.
- 증거를 아직 제시하지 않았는데 “제가 도현한테 보낸 사진이요?”처럼 경찰이 모르는 일을 용의자가 먼저 설명하는 패턴 금지.
- '왜 숨겼어요?'를 물으면 숨긴 사실과 이유를 모두 설명하는 함정 금지.
- 진범만 유독 날카롭거나 평소보다 음산하게 행동하는 패턴 금지. 표정, 대사 길이, 고성, 침묵, 반문으로 정답 유추 불가능해야 한다.
- 진술의 모순을 추궁하면 “죄송합니다” 뒤 자동 인정 반복 금지. **정당한 반론·기억 불확실·재설명·새로운 미검증 주장·권리 행사를 구별**할 것.
- 질문이 반복되면 임의의 추가 사건을 지어내 게임이 진전되는 패턴 금지.
- LLM이 `culprit_id`, `CaseTruth`, `EvidenceIntegrity`, `CaseClock`, `ReportJudge`를 직접 수정하는 행위 금지.

## 2. 심문 입력 정규화
마이크: 사용자가 말함 → STT → UI 미리보기/수정 → 확인 → 정상 1턴. 텍스트: 입력 → 발송 확인 → 정상 1턴. 둘 다 동일한 Intent/Cost/AI 경로 사용. 욕설·반말·은어·문장 일부·오타·장문 가설도 의미 분석. 입·출력 큐가 겹칠 때 중복 청구 방지. 서로 다른 질문을 한 번에 던지면 `compound_question`으로 분해하고 하나의 비용에 담을 수 있는 범위와 다중 추궁 행동을 UI로 명확히 알려라. 네트워크/오디오/LLM 에러 0원.

## 3. 인물의 6층 심리
1. **기저 성격:** 단정적/회피적/고집/자존심/사교성 등 고정 성향. 1:1 공략 버튼 아님.
2. **대인관계 기억:** 상대와의 오래된 관계, 서로의 호칭, 상처가 되는 표현, 자신이 받은 도움·상처.
3. **현재 자기보호 목표:** 숨길 동기, 법적 위험, 관계 체면, 고용/돈, 누군가 보호, 자기합리화.
4. **현재 감정:** 두려움·분노·수치심·상실·피로·협조 욕구. 연속적으로 조정되나 HUD 진범확률 표시 금지.
5. **경찰에 대한 인식:** 자신에게 질문한 주제의 빈도, 지금까지 보여 준 증거, 조사관의 블러핑 성공/실패, 절차 준수 여부.
6. **실행 가능한 선택지:** 직접 답변, 범위 한정, 이전 진술 유지, 부분 부인, 확인 요구, 다른 사실로 화제 이동, 침묵, 변호인 요청, 자발적 설명, 정정 진술, 실제 기억을 털어놓기. 플레이어가 같은 방식으로 접근해도 성격·증거·면담 순서에 따라 확률/정책 변화.

**이 여섯 층이 '범인 여부'를 유일한 결정변수로 삼지 않는다.** 진범이 아닌 이서연도 피가 묻은 옷과 횡령 문제 때문에 더 불안해할 수 있고, 진범 박현수는 익숙한 배송 분쟁 이야기에서는 아주 자연스러울 수 있다.

## 4. 턴 처리 상세 계약
```
InputTurn {
 turn_id, case_id, session_id, suspect_id, channel: text|mic,
 raw_text, confirmed_question, offered_evidence_ids[],
 requested_tactic: normal|compare|silence|soft_pressure|hard_pressure|desk,
 pending_cost_quote
}

1. preflight: save/LLM/scene/suspect availability, stt validity, affordability, legal status
2. snapshot: CaseRunState immutable; last claims; suspect's own facts; perceived officer disclosure
3. intent: time/location/motive/physical_contact/alibi/document/procedure/emotion/other
4. claim selection: eligible factual claims from speaker's facts only. mark lie/avoid/admit/refuse
5. defense planner: calculate cost of admission vs pressure vs alternate explanation and persona response
6. officer model: infer what officer may know using disclosed evidence/questions; never global inventory
7. NLG: generate Korean speech + embodied action (not truth mutation)
8. validators: forbidden facts, chronology, fact ID, new witness/route/forensics hallucination,
   uncontrolled self-incrimination, irrelevant answer, repeated canned phrasing
9. safe recovery: discard bad generation; controlled retrial or neutral case-consistent response
10. commit: append immutable transcript/claims/knowledge/tone/event and charge confirmed cost ONCE
11. render: subtitles/synced TTS, posture/eyes/hands, relevant audio. No extra cost.
```

`response_plan` schema:
```
{ speaker_id, permitted_fact_ids[], intentional_false_claim_ids[],
   reference_to_evidence_ids[], response_strategy,
   can_admit_fact_ids[], must_not_disclose_fact_ids[],
   emotional_shift, officer_assumption_update, confidence_language,
   animation_intent, willingness_to_continue, procedural_action }
```
LLM이 만든 `permitted_fact_ids`를 그대로 신뢰하지 말고, **서버 계획서가 정한 사실 ID 안에서만 문장을 만들게 해야 한다.** 유죄를 판단하는 `ReportEvaluator`는 이 대사 모델의 추론 결과를 입력으로 사용하지 않는다.

## 5. 거짓말 = 고정 문장 아님
- `omission`: 질문에 불리한 세부를 빼고 답한다. 예: “짐 가지러 갔어요.”
- `literal_narrowing`: 단어 해석을 좁힌다. “그날 회사에는 갔습니다” (바로 갔다는 뜻 아님).
- `deflection`: 질문의 추정 전제를 지적한다. “그 시간이라고 단정한 근거가 뭡니까.”
- `partial_truth`: 관계/채무는 사실대로, 방문/접촉은 생략.
- `memory_hedge`: 특정 분 단위 등 정말 기억이 흐릴 때의 정당한 불확실성.
- `fabricated_denial`: 캐릭터가 사실과 다른 적극적 거짓말. 루트 캐논에는 false claim과 대응증거를 작성.
- `qualified_admission`: 완벽한 반증 때문에 특정 관찰 사실을 제한적으로 인정.
- `counsel_or_silence`: 법적 권리를 행사하며 더는 답하지 않음.

답변 방식마다 사실·발생 조건·반박 경로가 있어야 한다. '아무거나 말하게 하는 AI'는 수사게임을 파괴한다.

## 6. 인격별 최상위 방어 특성
- 강도현: 질문의 시간/단어/확인한 사실을 구분하는 과묵한 기술직. 근거 없는 살인 추궁은 또렷하게 부인. **그러나 개인에게 자신의 폭행을 공개하는 일은 무섭고, 변명할 때 '확인해 보시면'이 과용될 수도 있으므로 문장 중복 제한.**
- 이서연: 정중하고 대화 규칙을 지키는 듯하면서 '방문', '접촉', '상처', '돈 사용'을 구분. 친밀한 과거의 수연을 말할 때는 더 사적인 표현. **경찰이 보여 주지 않은 혈흔의 성분을 먼저 과학적으로 설명하지 않는다.**
- 박현수: 숫자·서류·자기 생계가 중요하지만 첫 질문부터 피해자 공격을 장황하게 늘어놓지 않는다. 자료가 하나 밝혀지면 그것이 시각/장소/목격의 어느 범위를 확인하는지 따져보려 한다. 마음이 흔들려도 먼저 자신의 밀침/서류 은닉을 정리하여 자백하지 않는다. **고지받지 못한 메모/정정서의 뒷장 내용을 본 적 있는 척하지 않는다.**

세 사람 모두 화도 내고 배려도 보일 수 있다. '협조적으로 보이면 무죄'도, '증거를 따지면 범인'도 틀린 판단이어야 한다.

## 7. AI의 형사 관찰과 역심문
내부 `OfficerBeliefModel(suspectId)`은 캐릭터마다 따로 생성. 다음 입력만 허용: 자신에게 실제로 물은 질문의 주제·선택된 표현·공개된 자료·신문 도중 형사가 언급한 사실·본인의 개인 지식·알려진 공개 보도. 다른 피의자 조사 로그·피해자 전화 포렌식·미공개 경찰 보고서는 직접 읽지 못한다.

역질문 예: “그건 누가 확인한 건데요?”, “제가 간 건 증명하셔도, 그 뒤를 봤다는 기록은 없잖아요”, “그 자료는 언제 작성된 겁니까”, “그 사람 진술부터 확인하셨습니까.” 같은 말은 실제 질문·단서에서만 나오도록. 형사의 공략 습관을 추론하되 '플레이어의 정답 여부'를 읽지 말 것.

## 8. 감정과 애니메이션 계약
가능한 애니메이션 intent: `listening_eye_shift`, `slow_inhale`, `hands_fold`, `finger_fidget`, `chair_adjust`, `look_to_document`, `brief_look_down`, `silent_wait`, `lean_back`, `paper_push`, `restrained_shock`, `counsel_request`, `speech_break`, `controlled_anger`.
마이크 입력 중 인물은 자연스럽게 듣고, 긴 질문에서 끄덕이거나 중간에 끼어드는 조건을 지원. 답변 시 입모양/표정/손/자막/음성을 동기화. 기계적 상체 흔들기나 매 답변 같은 손 동작 금지. 표정으로 진범 확률 힌트를 주지 않는다.

## 9. 압박과 권리
- 질문 권한과 현실적인 경찰 절차를 구분. 현장 임의 제출·압수·피의자 신문 조건 모두 같은 버튼으로 처리 금지.
- 법적 현실감: 피의자는 진술거부·변호인 조력을 요청할 수 있다. 강압/불법적 폭력은 증거 신빙성/절차 리스크/면담 종료를 발생시킬 수 있다.
- '책상 내려치기'는 선택 가능한 위험한 드라마적 전술이지만 절대 정답 버튼이 아니다. 피의자를 신체적으로 위협하는 반복 행동에 보상 금지.
- 모든 단계에서 유저가 읽고 이해할 수 있는 비용·권리/위험 고지. 극적인 연출과 적법한 수사는 분리.

## 10. 대화 품질 테스트
`case_id`와 `suspect_id` 별 최소 100개 의미 변형 입력, 전체 2,000개 이상 다양성/부정문/은어/거짓 전제/복합 질문/정중-무례 스타일 테스트. V21 첫 시나리오 품질 목표: 비공개 사실 누설 0, 자기 무고자백 0, 사건 시간표 모순 0, 서버 상태 불법변경 0, 반복 대사 패턴 경고, 실속 없는 과잉회피 경고. 실제 테스트에서 일부 실패 시 근거·재현 로그를 공개하고 '0'이라고 주장하지 않는다.

CASE 002 더미 인물로 갈아 끼운 후 100턴 실행: CASE 001 이름·돈·사망시각·진범 표현 누출 0. 같은 엔진의 성격별 답변 다양성을 확인.
