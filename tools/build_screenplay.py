"""CASE001 handwritten dialogue bank, dramaturgy and reactive endings.
Not an LLM substitute. Never ship hidden witness/suspect alternate lines to Unity assets.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
R=[]
def dialogue(scene,act,speaker,intent,**variants):
    for mode,line in variants.items():
        if line:
            R.append({'id':f'd{len(R)+1:03d}','scene':scene,'act':act,'speaker':speaker,
              'intent':intent,'delivery':mode,'text':line,'source':'AUTHOR_WRITTEN_REFERENCE',
              'public_release':'SERVER_ONLY','fixed_reply':False})

# This is an original invented fictional case (not a dramatization of identifiable victims)
dialogue('hall','arrival','현장 보존 담당','문 앞 절차',neutral='형사님, 안에 감식팀 들어가 있어요',dry='덧신은 저쪽에 있습니다',quiet='계단 쪽은 통행 막아놨어요')
dialogue('hall','arrival','형사','동선 확인',neutral='들어온 사람부터 다시 체크하죠',low='문 잡은 사람 누구예요',busy='사진은 찍었어요?')
dialogue('hall','arrival','이웃 주민','호기심',hesitant='아이고, 무슨 일이 났길래 이렇게까지 해요',intrusive='아침에 애들 학교도 가야 되는데',worried='302호 아가씨, 그 사람 맞아요?')
dialogue('room302','arrival','형사','현장 공기',low='…환기가 안 됐네요',pragmatic='창문은 그대로 두세요',stop='잠깐, 발 디디지 마세요')
dialogue('room302','exploration','현장 감식','흔적 보존',pragmatic='그쪽은 아직 표시 안 했습니다',clear='바닥부터 사진 남기고요',tired='봉투 번호 다시 읽어주세요')
dialogue('room302','exploration','형사','일상 흔적',small='퇴근하고 바로 들어온 것 같은데',uneasy='밥 먹다가 그랬다는 건가',neutral='짐은 함부로 움직이지 마세요')
dialogue('room302','exploration','형사','시간 기록',realization='통화는 나중인데, 사람은 먼저 나갔네',calm='시간차가 있네요',cautious='아직 단정할 단계는 아니죠')
dialogue('room302','exploration','현장 감식','휴대전화',firm='휴대폰은 확보 절차부터 진행해야죠',neutral='잠금은 현장에서 바로 풀 수 있는 게 아니에요',tired='주변 손자국부터 보겠습니다')
dialogue('hall','exploration','이웃 주민','층간 소음',annoyed='밤마다 쿵쿵대는 건 저도 힘들었어요',defensive='그렇다고 제가 뭘 어떻게 했겠어요',regret='어젯밤 소리 들었는데 또 싸우나 했죠')
dialogue('hall','exploration','형사','증언 분리',neutral='직접 보신 것만 먼저 말씀해주세요',gentle='모르시는 건 모른다고 하셔도 돼요',followup='몇 층에서 들린 소리인지는 확실해요?')
dialogue('hall','exploration','이웃 주민','추측 교정',correct='아니, 그거 제가 봤다는 건 아니고',uncertain='계단 쪽인지 엘리베이터 쪽인지는 헷갈려요',shame='괜히 소문까지 냈나 봐요')
dialogue('interview','first_contact','강도현','도입',guarded='뭘 그렇게 계속 물으시는 건데요',defensive='아까 다 얘기했는데',frustrated='저 회사 가야 돼요, 언제 끝나요')
dialogue('interview','first_contact','형사','도입',neutral='오래 안 걸리게 해볼게요, 시간부터 확인하겠습니다',short='어젯밤에 어디서 만나셨어요',soft='말씀하기 불편한 건 나중에 해도 됩니다')
dialogue('interview','first_contact','강도현','다툼',admit='싸운 건 맞아요',deflect='근데 헤어진 사람끼리 말 한 번 못 합니까',hesitate='그날 좀… 말이 심하게 나왔어요')
dialogue('interview','pressure','강도현','퇴장 기록',relief='보세요, 나갔잖아요',angry='몇 번이나 얘기해야 돼요, 제가 나왔다고',low='저한테 뭐 더 덮어씌우실 거 있어요?')
dialogue('interview','pressure','강도현','사생활',defensive='그 여자분 얘기는 왜 꺼내세요',annoyed='그거 여기서 꼭 말해야 됩니까',quiet='그 사람까지 엮이고 싶지 않아서 그랬어요')
dialogue('interview','pressure','강도현','책상 분노',explosive='아, 씨발, 아니라니까요!',regret='…죄송합니다, 순간 욱해서',recede='말이 심했네요, 죄송합니다')
dialogue('interview','pressure','형사','격앙 제어',firm='손 내리세요, 얘기는 듣고 있습니다',neutral='물 한잔 드시고 다시 하죠',boundary='이 상태로는 더 진행하기 어렵겠습니다')
dialogue('interview','first_contact','이서연','도입',neat='제가 아는 건 말씀드릴게요',reserved='질문하시면 답하겠습니다',anxious='그 얘기를 지금 꼭 해야 하나요?')
dialogue('interview','first_contact','이서연','시간 범위',precise='아홉 시 이후 전체를 말씀하시는 거예요?',slow='제가 언제부터 집에 있었다고 했죠?',counter='그 시간은 누가 확인한 건가요?')
dialogue('interview','pressure','이서연','전화',partial='전화는 했어요, 그건 맞아요',quiet='그날 연락한 건 저예요',hedge='만난 건 아니고, 통화만 한 거예요')
dialogue('interview','pressure','이서연','돈 정산',irritated='돈 얘기야 했죠, 친한 사이에도 싸울 수 있잖아요',gentle='480만 원 때문에 그러는 거예요?',small='그 돈, 저만 쓴 거 아니에요')
dialogue('interview','pressure','이서연','출입 기록',pause='잠깐만요, 제가 말한 건…',counter='그 기록에 얼굴이 보여요?',quiet='제가 그 시간에 뭘 했는지 다시 생각해 볼게요')
dialogue('interview','redirection','이서연','편의점',hesitate='편의점요? 그건…',precise='거기 갔다는 건 부인한 적 없어요',defensive='제가 집에 있었다는 얘길 언제 했죠?')
dialogue('interview','pressure','이서연','타인 탐문',inquiring='다른 분들도 이 기록 보셨어요?',careful='박현수 씨는 뭐라고 하시던가요?',deflect='강도현 씨는 만나보셨죠?')
dialogue('interview','pressure','이서연','침묵',silence='…',short='지금은 대답 못 하겠어요',composed='좀 생각하고 말씀드릴게요')
dialogue('interview','pressure','이서연','변호인 요청',request='변호인하고 얘기하고 싶어요',low='오늘은 여기까지 해도 될까요',boundaries='이 질문엔 지금 답하지 않겠습니다')
dialogue('interview','aftershock','이서연','제출 이후',cool='이걸 보여주시려고 부르신 거예요?',measured='그때 얘길 더 하면 뭐가 달라지는데요',frayed='이제… 제가 뭐라고 해야 하는데요')
dialogue('interview','first_contact','박현수','도입',suspicious='저는 신고만 했는데 왜 자꾸 오라 그래요',busy='집에 강아지가 혼자 있어요',small='제가 들은 것까지는 말씀드렸죠')
dialogue('interview','pressure','박현수','층간소음',agitated='예민한 건 맞는데, 그거랑 사람 죽은 거랑 무슨 상관이에요',cautious='시끄러웠던 건 어제만이 아니에요',tired='그쪽 집이랑 몇 번 말다툼했어요')
dialogue('interview','pressure','박현수','소리 인식',honest='남자인지 여자인지는 못 들었어요',correct='쿵 소리 난 건 확실한데 시간은요, 그건 모르겠어요',retract='지금 생각하니까 발소리는 다른 집이었을 수도 있겠네요')
dialogue('interview','pressure','형사','증언 신빙성',neutral='들으신 거하고 생각하신 거는 따로 적겠습니다',soft='기억 바뀌어도 괜찮아요, 정확하게만 해주세요',followup='그때 집 안에 TV 켜져 있었습니까?')
dialogue('desk','pressure','동료 형사','자료 확인',serious='이 사람 얼굴은 확인 안 됩니다',practical='카메라 시각이랑 출입기록 시각부터 맞춰야죠',humble='컵에서 나온 거, 언제 묻은 건진 모르는 거예요')
dialogue('desk','pressure','동료 형사','상황 정리',low='강도현한테 몰리면 빠지는 거 놓쳐요',wary='오히려 너무 쉬운 답 아닙니까',frustrated='자료는 다 있는데 연결이 안 되네')
dialogue('desk','redirection','동료 형사','시각 오차',reveal='여기 시간 오차가 있어요, 기기별로 다릅니다',caution='이게 틀렸다고 나머지가 전부 맞는 건 아니고요',grind='한 번만 더 대조하죠')
dialogue('desk','aftershock','형사','가설 수정',responsible='제가 앞서 갔네요',careful='이 사람은 다시 봐야겠습니다',quiet='방금 보고 놓친 거, 어디서부터죠')
dialogue('hall','pressure','순경','돌발 주민',urgent='302호 가족분이라고 하는데요',uncomfortable='계속 안에 들어가겠다고 하세요',calm='밖에서 안내하고 있습니다')
dialogue('hall','pressure','가족','돌발 가족',shock='수연이 지금 어디 있어요',anger='누가 그랬는지 알긴 해요?',collapse='제가 어제 전화만 받았어도…')
dialogue('hall','pressure','형사','가족 대응',low='여기선 설명드리기 어렵습니다, 잠깐 이쪽으로',careful='확인된 내용부터 말씀드리겠습니다',quiet='죄송합니다, 지금은 안으로 들어가시면 안 됩니다')
dialogue('interview','pressure','형사','권리 보장',process='변호인 참여 요청하신 거 확인했습니다',neutral='잠시 중단하겠습니다',firm='의견 정리되면 다시 진행하죠')
dialogue('desk','pressure','기록 담당','연락 변화',sudden='참고인 한 분이 약속 취소하셨는데요',simple='아까 연락받고 마음이 바뀌셨대요',cautious='누가 연락했는지는 아직 확인 중입니다')
dialogue('desk','aftershock','동료 형사','보고서 제출',neutral='입증한 부분하고 추정한 부분을 나눠 적어주세요',severe='이대로 올리면 반려됩니다',quiet='지금은 지목 안 하는 게 낫겠습니다')
dialogue('desk','aftershock','형사','정답 성립',steady='추정은 추정으로 남겨놓죠',clear='자료 연결은 여기까지 확인됐습니다',quiet='더 할 말은 없네요')
dialogue('interview','aftershock','강도현','오인 지목 반응',furious='제가 아니라고 한 걸 어떻게 더 증명합니까',quiet='말해 봐야 소용없었네요',exhausted='이제 무슨 말을 해야 믿어주실 건데요')
dialogue('interview','aftershock','이서연','완전 입증 후',cold='자료는 잘 모으셨네요',fractured='그날로 돌아갈 수 있으면 좋겠어요',defiant='제가 얘기한 건 거짓말이 아니었어요, 전부는 아니어도')

# Shot planning uses evidence of character behaviors, no constant cuts, no false-flag film cues
scenes=[
 {'id':'act1_hall','minutes':'00-03','space':'복도/현관','tone':'나쁜 일이 평범한 공간에 들어온 어긋남','player_goal':'현장 보존, 접근 동선 판단','camera':'FP 자유시점 유지, 문턱 0.25초 멈칫','sound':'실내 센서등, 상층 배관, 문닫힘, 냉장고 먼 소리','surprise':'주민이 문을 열고 복도 소리가 변함','end':'혈흔 관찰이 아니라 현장 인물과 물건의 관계를 묻기 시작'},
 {'id':'act2_scene','minutes':'03-08','space':'302호','tone':'침착한 관찰이 사적인 슬픔으로 이동','player_goal':'영수증·휴대전화·문고리 상태와 시간차 기록','camera':'증거 앞 초점 이동만, 강제 줌 금지','sound':'봉투 비닐, 신발 덧신, 멈춘 TV, 낮은 전기음','surprise':'복도 주민 소음이 증언 후보로 바뀜','end':'21:21과 21:34 간격을 발견하되 결론은 유보'},
 {'id':'act3_first','minutes':'08-15','space':'조사실','tone':'상대방 말이 사실처럼 들려 흔들리는 시작','player_goal':'강도현과 이서연의 초기 진술, 자유질문','camera':'1인칭 고정, 컵과 손만 포커스','sound':'종이, 긴 침묵, HVAC, 복도 알림음','surprise':'AI 연락 요청 후 서버 승인 시 외부 전화 흔적','end':'15분에 범인 확정 없음'},
 {'id':'act4_pressure','minutes':'15-30','space':'조사실/수사대','tone':'기억이 아니라 기록과 맞부딪히는 순간','player_goal':'4개 입증 축 자료 확보 및 대안 검증','camera':'격앙 시 흔들림 0.004m 이하, 컵은 접촉 프레임에만 반응','sound':'벽시계, 의자 마찰, 마이크 접촉, 물컵','surprise':'변호인 요청/퇴장/자료 보완 등 조사 중단 가능','end':'분노와 죄책감을 혼동하지 않도록 설계'},
 {'id':'act5_redirection','minutes':'30-38','space':'증거 분석 데스크','tone':'오해를 깨는 정적','player_goal':'시각·추적 기록·감정 결과의 한계 재평가','camera':'비선형 시간축 인터페이스, 자유 조작','sound':'인쇄기, 형광등, 멀리서 울리는 유선전화','surprise':'오판 의심 시 새로운 조사 분기','end':'증거 4축 중 누락된 연결 확인'},
 {'id':'act6_report','minutes':'38-45','space':'보고서/조사실/복도','tone':'결론보다 책임의 무게','player_goal':'지목 또는 보류, 근거 출처 제출','camera':'종이·손·피사체 정적, 실패는 강제 감정 폭발 없이 진행','sound':'종이 넘기는 소리, 서류철, 복도문','surprise':'보고서 반려·인물의 예상 밖 반응','end':'충분 입증, 오인, 심증 부족, 절차 하자, 보류 각각 결과 다름'}
]
from server.dialogue_quality import edit_for_subtitles,audit_corpus
for row in R:row['text']=edit_for_subtitles(row['text'])
a=audit_corpus([x['text'] for x in R]);print('Dialogue lines',len(R),'lint',a['counts'])
(root:=ROOT/'data').mkdir(exist_ok=True)
(root/'case001_scriptbook.json').write_text(json.dumps({'schema':'tablezero.case001.authored_dialogues.v1','status':'authored_reference_not_verbatim_llm_script','dialogues':R,'scenes':scenes},ensure_ascii=False,indent=2),encoding='utf-8')
(root/'dialogue_audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
