import json,pathlib
R=pathlib.Path('/mnt/data/TABLE_ZERO_V21_FINAL_MASTER')
# (id,title,trigger,conditions,perception,event,guard)
a=[
('EV01','초동 배정과 피해자 부재','CASE_START',['no_case_loaded'],'2026.10.15 22:07 신고 / 병원 이송·사망 확인 뒤 현장 배정','경찰서의 야간 호출→사진/사건 카드→302호 출발','정확한 범행시각·범인·3인 모두의 진실 공개 금지'),
('EV02','복도 카메라 화각 검증','CAMERA_INSPECT',['CR-006 examined'],'카메라는 공동계단 쪽, 301→302 문 앞 일부 사각','Unity 실제 시점에서 플레이어가 녹화 가능/불가 각도를 직접 확인','범인이니까 카메라가 자동 고장나는 연출 금지'),
('EV03','네 사람이 웃던 사진','PHOTO_INSPECT',['LV-029 examined'],'4명 모두 본래 서로 친했다','사진 앞뒤/날짜 확인, 후속 심문 주제 생성','사진이 유리 파손과 살인범 신원을 자동 말하지 않음'),
('EV04','강의 근무 시각 반문','S1_DIRECT_WORK_CONFRONT',['s1_session','evidence V21-E13 disclosed'],'21:21 퇴장과 21:51 근무 시작 간 공백','강이 형사에게 “그 사이가 왜 필요합니까” 같은 시간/근거 질문','언제 차에 있었고 무엇을 전송했는지 스스로 장황한 자백 금지'),
('EV05','강의 격정과 침묵','S1_ARM_EVIDENCE',['s1_session','V21-E05 disclosed','prior arm-contact denial'],'팔 접촉을 시인할지 고민하는 도현','손톱 주변을 만지려다 멈춤·목소리 낮아짐·사실 확인 요구','연출=살인 증거 금지; 강만 같은 긴장 애니 사용 금지'),
('EV06','도현이 보내지 말라는 말을 무시했다','S1_OLD_DOC_REVEAL',['s1_session','V21-E12 disclosed'],'수연이 만류한 옛 책임서 메시지','도현이 문서 버전/박에게 보낸 의도에 대한 설명 범위를 조정','박 폭행을 미리 예상한 공범 창작 금지'),
('EV07','서연이 사건 중 피를 만졌다는 오해','S2_BLOOD_PRESENT',['s2_session','V21-E08 or V21-E09 disclosed'],'서연의 소매 접촉혈과 수연 오른손 열상','서연이 정확히 어떤 감정인지 확인 요청·조용히 답변 범위 한정','혈액=치명적 두부 손상 혈액으로 자동 전환 금지'),
('EV08','이서연에게 불리한 편의점 영상','S2_STORE_RECORD',['s2_session','V21-E14 disclosed'],'21:55 편의점 기록','서연이 자신의 동선을 날짜/시각으로 고정하려는 시도','영상의 존재를 알기 전에 미리 논박 금지'),
('EV09','수연의 사후활동이 밝혀지는 순간','VOICE_MEMO_VERIFIED',['V21-E07 acquired','phone integrity verified'],'21:50~51 살아서 업무 기록','조용한 음성파일 원본 청취·CaseBoard 새 확정 사실 추가','범인 이름 언급/고발문 금지, 서연 무죄 자동 확정 금지'),
('EV10','박현수의 신고시각과 발견시각','S3_DISCOVERY_TIME',['s3_session','V21-E03 disclosed'],'22:07 신고 내용과 처음 발견 시간은 별개','박의 말 끊김·서류 문구로 질문 되받기','박만 유독 공포/땀 연기 금지'),
('EV11','현수가 마주한 서류 뒷장','S3_CORRECTION_REVEAL',['s3_session','V21-E10 authentic correction acquired','officer presents correction content'],'자기 누명을 바로잡을 정정서가 이미 준비되어 있었다는 사실','반응의 틈과 침묵·상실감을 표현, 그러나 진범 자백은 선택적','뒷장 보기 전 박의 사전 기억에 진짜 내용 주입 금지'),
('EV12','종이 조각 출처 일치','PAPER_MATCH_RETURN',['V21-E16 acquired','authenticity confirmed'],'302호 정정서 봉투와 박쪽에서 확보한 자료가 물리적으로 관계 있음','재구성 UI에 맞물리는 찢김·서체·원본 상태 검증','파편만으로 폭행·정확한 분·법적 유죄 확정 금지'),
('EV13','119 흔적 때문에 바뀌는 가설','EMS_RECORDS',['V21-E17 acquired','LV-041 examined'],'끌린 자국 일부는 EMS의 처치로도 설명 가능','현장 사진에 대안 가설 추가 표시','119 흉내를 범행 은폐로 오인하게 만드는 불공정 정답 트릭 금지'),
('EV14','변호인 요청','COUNSEL_REQUEST',['any suspect session','legal risk or free choice'],'자신에게 불리한 진술을 더 하지 않기로 결정','의자 자세 변화→면담 중단/재예약, 객관수사 경로 계속','실제 권리 행사에 숨은 범죄 확률 부여 금지'),
('EV15','면담 중 감식 회신 알림','FORENSIC_NOTICE',['player in interview','forensic job ready'],'새 결과가 조사본부에 도착했다는 통지만','문 밖 전화·비서 메모. 대화를 중단할지 선택','용의자가 결과 내용을 자동으로 알지 못함, 회신은 과학적 시간 지연'),
('EV16','핵심 알리바이 후속 확인','KANG_WORK_CONFIRM',['V21-E13 source corroborated'],'21:51 이후 강 야간근무 독립 확인','형사의 가설보드에 구간별 신뢰도 정리','강의 별도 폭행·문서 전송 행위 지우지 않음'),
('EV17','자율적으로 형사를 분석하는 도현','S1_OFFICER_PROFILE',['s1_session','officer mentioned message twice'],'형사의 관심이 문서 전송에 집중됐다고 유추','도현 “계속 그 얘기면 보내기 전후 확인하신 거죠?” 반문','경찰이 숨긴 다른 용의자 대화 내용 읽기 금지'),
('EV18','자율적으로 형사를 분석하는 이서연','S2_OFFICER_PROFILE',['s2_session','officer mentioned blood without lab details'],'형사의 증거가 완전하지 않을 수 있다고 추측','이 “확인된 게 접촉인지, 어느 상처에서 난 피인지 알 수 있나요?” 반문','미공개 분석결과를 알고 묻는 것처럼 연기 금지'),
('EV19','자율적으로 형사를 분석하는 박현수','S3_OFFICER_PROFILE',['s3_session','officer presses visit time repeatedly'],'형사가 실제 목격이 아닌 진술모순을 좇는다고 추정','박 “지금 무슨 기록을 보고 시간부터 물으시는 거예요?” 반문','정답 암시 금지; 다른 사람도 역심문 가능'),
('EV20','자료 제출 거절 뒤 대체 경로','EVIDENCE_REFUSAL',['suspect refuses voluntary material'],'임의제출 없이도 정당한 자료 경로 존재','법적 절차 요청/다른 독립 증거 조사 선택 UI','거절했다는 이유로 이미 있던 증거 전부 소멸/범인 표식 생성 금지'),
('EV21','형사가 카메라 영상의 허점을 파악','CCTV_LIMIT_RECOGNIZED',['player observes actual camera geometry','V21-E02 seen'],'어느 구간은 보이고 어느 구간은 보이지 않음','도면에 투명한 시야각 레이어와 미확인 구간 표기','사각지대 비어있다는 사실만으로 그곳에 박이 있었다고 확정 금지'),
('EV22','마지막 사진의 다른 의미','ENDING_FOUR_PERSON_PHOTO',['ending reached','LV-029 previously examined'],'옛날 네 사람이 함께 웃던 기억','선택된 엔딩에 맞춰 사진과 정정서 비교, 정서적 종결','현장 정답 새로 공개하는 마법 연출·10분 스킵 컷신 금지')]
arr=[]
for id,title,trigger,conds,fact,scene,guard in a:
 arr.append({'event_id':id,'title':title,'trigger':trigger,'preconditions':conds,'perceived_fact_only':fact,'presentation':scene,'protection':guard,'once_per_case':True,'action_cost_of_event':0,'server_mutation':'공개된 사실/질문 전술/연출 상태만. 진실·유죄 여부 변경 금지'})
(R/'06_EVENTS/CONDITIONAL_SURPRISE_EVENTS.json').write_text(json.dumps({'version':'21.0','case_id':'001','events':arr,'prior_V16_events':'정본 s2와 관련된 V16 이벤트는 V21 승인 없이 마이그레이션 금지'},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(arr))
