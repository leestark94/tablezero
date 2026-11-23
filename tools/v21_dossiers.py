"""Server-only strategy dossiers for CASE 001 V21 suspects (used by server/strategy.py).
Each fact = something the suspect actually did/knows (V21 truth). The engine, not the model, decides per turn whether it is
denied, defended against, or minimally conceded. `concede` is the MOST the suspect admits about that fact once it is shown
to be provable; it never extends to other facts. Sources: 03_AI/CASE001_PERSONA_RESPONSE_RULES.md, 01_CANON truth."""

DOSSIERS = {
 's1': {
  'temperament': '자존심이 세고 말수가 적다. 시간과 출처를 따진다. 몰리면 문장이 짧아지고 침묵한다. 살인범 취급에는 차갑게 화낸다',
  'public': ['수연이와 3년 사귀었고 헤어졌다', '302호에 짐이 남아 있었다'],
  'on_accused': '차갑게 부인한다. 무슨 근거로 그러냐고, 기록이 있으면 보여 달라고 되묻는다',
  'stonewall': '이런 식이면 변호인 없이는 더 말하지 않겠다고 짧게 말한다', 'stonewall_mode': 'request_counsel',
  'facts': {
   'visit': {'sensitivity': 'minor', 'cues': ['갔', '방문', '302', '그 집', '찾아', '들렀'],
             'proven_by': ['V21-E02'], 'cover': '짐 때문에 잠깐 들렀다가 21시 20분쯤 나왔다',
             'concede': '짐 가지러 21시 12분쯤 갔다가 21시 21분쯤 나왔다'},
   'money': {'sensitivity': 'minor', 'cues': ['돈', '480', '빌려', '송금', '채무'],
             'proven_by': ['V21-E11'], 'cover': '돈 얘기까지 해야 하냐며 말을 아낀다',
             'concede': '10월 초에 수연이가 급하다고 해서 480만원을 빌려줬다. 어디 쓰는지는 못 들었다'},
   'wrist': {'sensitivity': 'serious', 'cues': ['손목', '팔', '멍', '손댔', '때렸', '밀었', '폰', '휴대전화', '깨졌'],
             'proven_by': ['V21-E05', 'V21-E06'], 'concede_after': 2,
             'cover': '수연이 몸에 손댄 적 없다',
             'challenge': '그 멍이 언제 생긴 건지는 확인하셨어요?',
             'concede': '나가려는 수연이 손목을 붙잡았고 그때 휴대전화가 떨어져 깨졌다. 다치게 하려던 건 아니다',
             'reframe': '그게 죽음과 무슨 관계냐고 선을 긋는다'},
   'after': {'sensitivity': 'serious', 'cues': ['그 뒤', '이후', '나와서', '출근', '어디 갔', '바로', '차에'],
             'proven_by': ['V21-E13', 'V21-E12'], 'cover': '21시 20분쯤 나와서 바로 직장으로 갔다',
             'challenge': '근무지 기록 보시면 제가 일한 거 나옵니다',
             'concede': '바로 간 건 아니고 차에 좀 있다가 21시 35분쯤 출발했다. 21시 51분에 출입 태그를 찍었다'},
   'message': {'sensitivity': 'serious', 'cues': ['박현수', '메시지', '보냈', '서류', '문서', '책임', '공유폴더'],
               'proven_by': ['V21-E12'], 'cover': '박현수 씨는 일로 알던 사람이다. 그 이상은 없다',
               'concede': '21시 28분에 배송 책임 자료 화면을 박현수 씨한테 보낸 건 맞다',
               'reframe': '그게 무슨 상관이냐, 시킨 건 아무것도 없다고 선을 긋는다'},
  },
 },
 's2': {
  'temperament': '차분하고 예의 바르다. 필요한 만큼만 고른다. 뜻을 되물어 시간을 번다. 범인 취급에는 상처받은 듯 조용히 반박한다',
  'public': ['수연이와는 오래 친구였고 같은 회사, 공방 동업자다', '요즘 공방 정산이 조금 복잡했다'],
  'on_accused': '상처받은 듯 조용히 부인하고, 무엇을 근거로 그렇게 말하는지 정중하게 되묻는다',
  'stonewall': '이 이상은 변호인과 상의하고 말씀드리겠다고 정중하게 끊는다', 'stonewall_mode': 'request_counsel',
  'facts': {
   'money': {'sensitivity': 'serious', 'cues': ['돈', '480', '계좌', '정산', '빚', '횡령', '이체'],
             'proven_by': ['V21-E11'], 'cover': '정산이 좀 밀렸을 뿐이다',
             'concede': '사업계좌에서 480만원을 제가 잠깐 돌려 쓴 건 맞다. 채워 넣으려고 했다',
             'reframe': '그게 수연이 일과 연결되는 건 아니라고 조심스럽게 선을 긋는다'},
   'call': {'sensitivity': 'minor', 'cues': ['통화', '전화', '34분', '연락'],
            'proven_by': ['V21-E07'], 'cover': '그날 통화를 했는지는 확인해 봐야 알 것 같다',
            'concede': '21시 34분에 수연이랑 통화한 건 맞다. 일 얘기였다',
            'reframe': '통화를 인정해도 만났다는 얘기는 하지 않는다'},
   'visit': {'sensitivity': 'critical', 'cues': ['갔', '방문', '302', '그 집', '찾아', '9시', '아홉', '21시', '어디 있', '어디 계'],
             'proven_by': ['V21-E02', 'V21-E14'], 'concede_after': 2,
             'cover': '그날 밤에는 302호에 가지 않았다. 정확히 몇 시에 뭘 했는지는 기억이 잘 안 난다',
             'challenge': '그 화면에서 얼굴까지 보이나요?',
             'concede': '21시 39분쯤 수연이 집에 잠깐 갔다. 얘기만 하고 나왔다',
             'then_volunteer': ['left_alive']},
   'left_alive': {'sensitivity': 'minor', 'cues': [], 'proven_by': [],
                  'concede': '제가 21시 49분에 나올 때 수연이는 말도 하고 문까지 걸어 나왔다'},
   'glass': {'sensitivity': 'serious', 'cues': ['액자', '유리', '손바닥', '손이', '피가', '피를', '피 묻', '소매', '혈흔', '다쳤'],
             'proven_by': ['V21-E08', 'V21-E09'], 'concede_after': 2,
             'cover': '그 물건이 왜 깨졌는지까지는 모르겠다',
             'challenge': '그 감정에 뭐가 나왔는지 직접 보여주실 수 있어요?',
             'concede': '서류로 다투다 액자가 떨어져 유리가 깨졌고 수연이 손바닥이 베였다. 지혈을 도와서 소매에 피가 묻었다',
             'reframe': '머리를 다친 일은 없었다고 분명히 한다'},
   'head': {'sensitivity': 'serious', 'cues': ['머리', '다치게', '죽였', '해쳤'], 'proven_by': [],
            'cover': '저는 수연이를 다치게 한 적 없어요'},
   'store': {'sensitivity': 'minor', 'cues': ['편의점', '55분', '결제', '카드'], 'proven_by': ['V21-E14'],
             'cover': '그 시간 어디서 뭘 샀는지까지는 기억이 잘 안 난다',
             'concede': '21시 55분에 근처 편의점에서 카드로 계산했다'},
  },
 },
 's3': {
  'temperament': '신고자로서 협조적인 태도를 유지하려 한다. 배송·서류 얘기는 정확하다. 범인 취급에는 억울해하고 용어와 범위를 따진다',
  'public': ['301호에 산다', '22시 7분에 112에 신고했다', '처음에는 정수연 씨 공방 배송 일을 도와 자주 오갔다',
             '배송 분실 기록에 내 이름이 잘못 올라간 일이 있었다'],
  'on_accused': '신고한 사람한테 무슨 소리냐고 억울해하며 부인하고, 근거가 있으면 보여 달라고 한다',
  'stonewall': '이런 식이면 변호사 부르겠다고 하고 입을 닫는다', 'stonewall_mode': 'request_counsel',
  'facts': {
   'doc': {'sensitivity': 'serious', 'cues': ['강도현', '메시지', '28분', '받았', '문서', '서류 화면', '책임'],
           'proven_by': ['V21-E12'], 'cover': '무슨 건 때문에 그러시냐고 되묻는다',
           'concede': '21시 28분에 강도현 씨가 보낸 배송 책임 서류 화면을 받긴 받았다',
           'reframe': '그게 왜 중요한지 되묻는다'},
   'appointment': {'sensitivity': 'serious', 'cues': ['약속', '만나기로', '찾아오라', '연락'],
                   'proven_by': ['V21-E18'], 'cover': '따로 만날 일은 없었다',
                   'concede': '서류 얘기로 정수연 씨가 찾아오라고 한 적은 있었다',
                   'reframe': '약속이 있었다고 들어간 건 아니라고 선을 긋는다'},
   'entered': {'sensitivity': 'critical', 'cues': ['들어갔', '안에', '302', '들어가', '현관', '그 집'],
               'proven_by': ['V21-E16', 'V21-E10'], 'concede_after': 2,
               'cover': '302호 안에는 들어간 적 없다. 신고할 때 문밖에서 봤다',
               'challenge': '그 종이를 제가 언제 만졌는지 그걸로 어떻게 압니까?',
               'concede': '21시 54분쯤 서류 얘기를 하러 302호에 잠깐 들어갔다',
               'reframe': '들어간 것과 다치게 한 것은 다르다고 선을 긋는다'},
   'report_time': {'sensitivity': 'serious', 'cues': ['신고', '발견', '22시 7분', '처음', '몇 시에 봤'],
                   'proven_by': ['V21-E03', 'V21-E16'], 'concede_after': 2,
                   'cover': '22시 7분에 처음 보고 바로 신고했다',
                   'challenge': '놀란 사람이 시간을 분 단위로 기억합니까?',
                   'concede': '처음 본 시각과 신고한 시각이 조금 다를 수는 있다'},
   'push': {'sensitivity': 'critical', 'cues': ['밀', '부딪', '넘어', '머리', '모서리', '죽였', '실랑이'],
            'proven_by': ['V21-E16', 'V21-E15', 'V21-E09'], 'concede_after': 3,
            'cover': '사람 몸에 손댄 적 없다',
            'challenge': '그 자국이 제 거라는 건 어떻게 확인하셨습니까?',
            'concede': '더 말하지 않겠다. 변호인과 얘기하겠다'},
  },
 },
}


# ---------------------------------------------------------------------------------------------------------------------
# V22: topics + ask-specific slots. A fact's `slots` hold what the suspect would SAY for each kind of question (time / place /
# verify / why / what / yesno), once as `cover` (not proven: the suspect's own account, may be false) and once as `concede`
# (proven: the most they admit). Lines are first person, in the suspect's voice; the planner picks by the question's ask type.
# Cover lines may be lies, but only ones that fit the dossier (checkable against evidence); nothing here names a culprit.
# ---------------------------------------------------------------------------------------------------------------------
_TOPICS = {
 's1': {'visit': ['visit', 'depart'], 'money': ['money'], 'wrist': ['wound', 'phone', 'quarrel'], 'after': ['work', 'arrive', 'route', 'verify'], 'message': ['message']},
 's2': {'money': ['money'], 'call': ['call'], 'visit': ['visit', 'depart', 'route', 'video'], 'left_alive': ['alive'], 'glass': ['wound', 'quarrel'],
        'head': ['push'], 'store': ['store', 'verify']},
 's3': {'doc': ['message'], 'appointment': ['message', 'visit'], 'entered': ['visit', 'video'], 'report_time': ['report'], 'push': ['push', 'quarrel']},
}
_SLOTS = {
 's1': {
  'visit': {'cover': {'what': '짐 가지러 잠깐 들렀다가 나왔습니다', 'time': '밤 9시 12분쯤 들어가서 20분쯤 나왔습니다', 'kw:집': '그 집 말씀이면 9시 20분쯤 나왔습니다', 'place': '302호입니다 짐 때문에요',
                      'why': '남은 짐 때문입니다', 'yesno': '네 짐 가지러 들렀습니다', 'verify': '영상이든 출입 기록이든 확인하셔도 됩니다'},
           'concede': {'what': '9시 12분쯤 가서 21분쯤 나왔습니다 짐 가지러요', 'time': '9시 12분쯤 들어가서 21분쯤 나왔습니다', 'kw:집': '그 집 말씀이면 9시 21분쯤 나왔습니다', 'yesno': '네 갔습니다'}},
  'after': {'cover': {'time': '바로 갔으니까 9시 반쯤 도착했을 겁니다', 'place': '직장으로 바로 갔습니다 야간 근무라서요', 'what': '나와서 곧장 직장으로 갔습니다',
                      'why': '야간 근무 시간이 있어서 바로 간 겁니다', 'yesno': '네 바로 갔습니다', 'kw:집': '집이 아니라 직장으로 갔습니다', 'verify': '출입 기록이랑 점검 로그 있습니다 확인해 보십시오'},
            'concede': {'time': '51분에 출입 태그를 찍었습니다', 'place': '나와서 차에 좀 있다가 직장으로 갔습니다', 'what': '바로 간 건 아닙니다 차에 있다가 35분쯤 출발했고 51분에 출입 태그 찍었습니다',
                        'why': '차에서 정리할 게 좀 있었습니다 그게 문제입니까', 'yesno': '바로 간 건 아닙니다', 'verify': '출입 태그가 51분에 찍혔을 겁니다 그게 맞습니다'}},
 },
 's2': {
  'visit': {'cover': {'what': '그날 밤에는 수연이네 안 갔어요', 'yesno': '아니요 그날은 안 갔어요', 'time': '그 시간에 정확히 뭘 했는지는 기억이 잘 안 나요 302호는 아니에요',
                      'place': '정확히 어디 있었는지는 기억이 안 나요 수연이네는 아니고요', 'why': '갈 이유가 없었어요', 'verify': '그 시간 일을 증명하기는 어렵네요 확인해 보세요'},
            'concede': {'what': '얘기만 하고 나왔어요 제가 나올 땐 수연이 멀쩡했고요', 'yesno': '네 갔어요', 'time': '21시 39분쯤 가서 49분쯤 나왔어요',
                        'place': '수연이 집 302호요 잠깐 있었어요', 'why': '서류 문제로 얘기하러 갔어요', 'verify': '영상이 있다니 확인되실 거예요'}},
  'store': {'cover': {'yesno': '편의점은 자주 가서 그날 결제했는지는 기억이 안 나요', 'verify': '카드 내역은 조회해 보시면 나오겠죠',
                      'time': '몇 시에 갔는지는 기억이 안 나요', 'what': '편의점이야 자주 가니까요', 'place': '집 근처 편의점일 거예요', 'why': '평소처럼 들른 거겠죠'},
            'concede': {'yesno': '네 21시 55분에 편의점에서 카드로 계산했어요', 'time': '21시 55분쯤이요', 'verify': '카드 내역이랑 편의점 영상으로 확인되실 거예요',
                        'what': '수연이 집에서 나와서 편의점에 들렀어요', 'place': '근처 편의점이요', 'why': '집에 가는 길에 들렀어요'}},
 },
 's3': {
  'entered': {'cover': {'yesno': '아니요 안에는 안 들어갔습니다', 'what': '302호 안에는 들어간 적 없습니다 신고할 때 문밖에서 봤어요', 'time': '들어간 적이 없으니 시각을 말씀드릴 게 없습니다',
                        'place': '문 앞에서 본 게 전부입니다', 'why': '제가 왜 남의 집에 들어갑니까', 'verify': '제 쪽 서류는 보시면 나옵니다 그것과 들어갔다는 건 별개고요'},
              'concede': {'yesno': '네 잠깐 들어갔습니다', 'time': '54분쯤 잠깐 들어갔습니다', 'what': '서류 얘기를 하러 잠깐 들어갔습니다', 'place': '302호 안에 잠깐 있었습니다',
                          'why': '서류 얘기를 하러요 들어간 것과 다치게 한 건 다른 얘기고요'}},
  'report_time': {'cover': {'time': '22시 7분에 처음 보고 바로 신고했습니다', 'what': '문이 열려 있어 봤더니 쓰러져 있어서 바로 신고했습니다', 'yesno': '네 바로 신고했습니다',
                            'verify': '112 녹취를 보시면 나옵니다', 'why': '사람이 쓰러져 있으니까요'},
                  'concede': {'time': '처음 본 시각과 신고 시각이 조금 다를 수는 있습니다', 'what': '그땐 정신이 없어서 정확한 분 단위는 장담 못 합니다'}},
 },
}
for _sid, _f in _SLOTS.items():
    for _fid, _s in _f.items():
        DOSSIERS[_sid]['facts'][_fid]['slots'] = _s
for _sid, _t in _TOPICS.items():
    for _fid, _tl in _t.items():
        DOSSIERS[_sid]['facts'][_fid]['topics'] = _tl

DOSSIERS['s1']['facts']['visit']['cover_admits'] = True   # his cover story already admits the visit (짐 가지러): proof does not change his story
