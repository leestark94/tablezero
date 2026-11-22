"""Authored suspect lines (CASE 001 V21), picked by the strategy plan in microseconds — no model round trip.

Why: a 4–8B local model needs 5–40 s on this machine while the game also renders, and its Korean reads like a help desk.
The strategy engine already decides *what* the suspect does this turn (deny / challenge / concede one fact / demand proof /
stonewall / rebuke). This module supplies *how that person says it*: hand-written, per-suspect voice, several variants per
situation, never repeating a line, escalating when the detective pushes the same point again.

Safety: every line here is written to stay inside the dossier. A concession line only states what dossier `concede` already
allows. Lines still pass the server's guard/lint; a line that fails is skipped. No line states guilt, names a culprit or
reveals a hidden fact that the tactic does not allow. Questions not covered here return None → the caller falls back to
the language model (or a stance fallback).
"""
from __future__ import annotations
import re

# key: (tactic, focus_fact or '*')  ->  list of variants, mildest first. Last items are "pushed again" variants.
BANK = {
 's2': {   # 이서연 — polite to the end, buys time by asking what is meant, grows quieter (not louder) when cornered
  ('DEMAND_PROOF', '*'): [
      '…저를 의심하시는 건 알겠는데요 근거가 있으시면 먼저 보여주세요',
      '어떤 근거로 그렇게 말씀하시는 거예요 제가 알아야 대답을 하죠',
      '그렇게 확신하시면 보여주세요 저는 숨길 게 없으니까요',
      '같은 말씀을 계속 하시는데 보여주실 게 있으면 보여주시고요',
  ],
  ('STONEWALL', '*'): [
      '죄송하지만 여기서부터는 변호인과 상의하고 말씀드릴게요',
      '더는 답변 안 드리겠습니다 변호인 부탁드립니다',
  ],
  ('REBUKE', '*'): [
      '방금 하신 말씀 … 지금 녹화되고 있는 거 아시죠 사과하세요',
      '그건 형사님이 하실 말이 아니에요 이 얘기는 더 안 하겠습니다',
  ],
  ('DENY', 'money'): [
      '정산이 조금 밀린 건 맞는데요 그게 무슨 문제가 되는지 모르겠어요',
      '공방 돈 문제는 수연이랑 저 사이에서 정리할 일이었어요',
      '돈 얘기는 계좌 내역을 정확히 보고 말씀드리는 게 맞을 것 같아요',
  ],
  ('CONCEDE_MIN', 'money'): [
      '…사업계좌에서 480만원을 제가 잠깐 돌려 쓴 건 맞아요 채워 넣으려고 했어요 그게 수연이 일이랑 연결되는 건 아니고요',
      '네 그 돈은 제가 쓴 거 맞아요 그렇지만 그 얘기가 지금 이 일이랑 무슨 상관인지는 모르겠어요',
  ],
  ('DENY', 'call'): [
      '통화요 그날 했는지는 기록을 봐야 알 것 같아요',
      '수연이랑은 자주 통화해서 그날 일인지는 잘 기억이 안 나요',
  ],
  ('CONCEDE_MIN', 'call'): [
      '아 21시 34분 통화요 그건 맞아요 공방 일 얘기였어요',
      '네 통화는 했어요 일 얘기였고 그게 만났다는 뜻은 아니에요',
  ],
  ('DENY', 'visit'): [
      '그날 밤에는 수연이네 안 갔어요 몇 시에 뭘 했는지까지는 정확히 기억이 안 나고요',
      '302호에 갔냐고요 …아니요 저는 그날 거기 간 기억이 없어요',
      '정확히 기억나는 게 없어요 그런데 그걸 왜 계속 물으세요',
  ],
  ('CHALLENGE', 'visit'): [
      '그 화면에서 얼굴이 확실히 보여요 저는 잘 모르겠는데요',
      '그 영상이 몇 시 건지부터 확인하셨나요 저로 보이는 건 맞는지도요',
  ],
  ('CONCEDE_MIN', 'visit'): [
      '…네 갔어요 21시 39분쯤 잠깐요 얘기만 하고 나왔어요 제가 나올 땐 수연이 멀쩡했고요',
      '맞아요 그날 갔어요 말씀드리기 어려워서 그랬는데 얘기만 하고 나왔어요',
  ],
  ('DENY', 'glass'): [
      '액자가 왜 깨졌는지는 저도 몰라요',
      '손이나 소매 얘기는 무슨 말씀이신지 잘 모르겠어요',
  ],
  ('CHALLENGE', 'glass'): [
      '그 감정 결과에 뭐가 나왔는지 직접 보여주실 수 있어요',
      '소매에 뭐가 묻었다는 건데 그게 누구 건지는 확인되셨어요',
  ],
  ('CONCEDE_MIN', 'glass'): [
      '…서류로 다투다 액자가 떨어져서 수연이 손이 베였어요 지혈을 도왔는데 소매에 피가 묻은 거예요 머리를 다친 일은 없어요',
  ],
  ('DENY', 'head'): [
      '저는 수연이를 다치게 한 적 없어요',
      '그런 말씀은 정말 상처가 되네요 저는 아니에요',
      '수연이를 해칠 이유가 없어요 그건 분명히 말씀드릴 수 있어요',
  ],
  ('DENY', 'store'): [
      '그 시간에 어디서 뭘 샀는지까지는 기억이 잘 안 나요',
      '편의점이야 자주 가니까요 그날인지는 모르겠어요',
  ],
  ('CONCEDE_MIN', 'store'): [
      '21시 55분에 편의점에서 계산한 건 맞아요 집에 가는 길이었고요',
  ],
  ('CONCEDE_MIN', 'left_alive'): [
      '제가 나올 때 수연이는 말도 하고 문까지 나왔어요',
  ],
 },
 's1': {   # 강도현 — short, cold, wants times and sources; no polite padding
  ('DEMAND_PROOF', '*'): [
      '근거는요 있으면 보여주십시오',
      '그걸 제가 어떻게 압니까 보여주실 게 있으면 보여주세요',
      '같은 소리 계속 하시는데 증거가 있으면 꺼내시죠',
      '…정확히 몇 시 얘기입니까 기록으로 말씀하세요',
  ],
  ('STONEWALL', '*'): [
      '변호인 오기 전엔 말 안 합니다',
      '여기까지 하겠습니다 변호인 불러주세요',
  ],
  ('REBUKE', '*'): [
      '방금 그 말 녹화됐습니다 형사가 할 말입니까',
      '그런 말 하는 사람이랑은 얘기 안 합니다',
  ],
  ('DENY', 'visit'): [
      '짐 때문에 잠깐 들렀다가 20분쯤 나왔습니다',
      '말씀드렸잖습니까 짐 가지러 간 겁니다',
  ],
  ('CONCEDE_MIN', 'visit'): [
      '12분쯤 가서 21분쯤 나왔습니다 짐 가지러요',
  ],
  ('DENY', 'money'): [
      '돈 얘기까지 해야 합니까',
      '개인적인 거래입니다 그건 말씀 안 드리겠습니다',
  ],
  ('CONCEDE_MIN', 'money'): [
      '10월 초에 급하다고 해서 480만원 빌려줬습니다 어디 쓰는지는 못 들었고요',
  ],
  ('DENY', 'wrist'): [
      '수연이 몸에 손댄 적 없습니다',
      '손댔다는 근거가 뭡니까',
  ],
  ('CHALLENGE', 'wrist'): [
      '그 멍이 언제 생긴 건지는 확인하셨습니까',
      '휴대전화가 언제 깨졌는지도 확인하셨습니까',
  ],
  ('CONCEDE_MIN', 'wrist'): [
      '…나가려는 걸 붙잡았습니다 손목을요 그때 폰이 떨어졌고요 다치게 하려던 건 아닙니다 그게 사건이랑 무슨 상관입니까',
  ],
  ('DENY', 'after'): [
      '20분쯤 나와서 바로 직장 갔습니다',
      '근무지 기록 확인해 보시면 됩니다',
  ],
  ('CHALLENGE', 'after'): [
      '근무지 기록 보시면 제가 일한 거 나옵니다',
  ],
  ('CONCEDE_MIN', 'after'): [
      '바로 간 건 아닙니다 차에 좀 있다가 35분쯤 출발했고 51분에 출입 태그 찍었습니다',
  ],
  ('DENY', 'message'): [
      '박현수 씨는 일로 알던 사람입니다 그 이상은 없습니다',
  ],
  ('CONCEDE_MIN', 'message'): [
      '28분에 배송 책임 자료 화면 보낸 건 맞습니다 시킨 건 아무것도 없고요',
  ],
 },
 's3': {   # 박현수 — accommodating reporter; exact about documents; bristles at being treated as a suspect, quibbles about terms
  ('DEMAND_PROOF', '*'): [
      '신고한 사람한테 무슨 말씀이십니까 근거가 있으시면 보여주시죠',
      '제가요 무슨 건 때문에 그러시는지부터 말씀해 주십시오',
      '그건 제가 판단할 일이 아니고요 증거 있으면 보여주세요',
      '계속 그러시면 곤란합니다 서류로 말씀하시죠',
  ],
  ('STONEWALL', '*'): [
      '변호사 부르겠습니다 이 이상은 말씀 못 드립니다',
      '더 하시면 변호인 없이는 답 안 합니다',
  ],
  ('REBUKE', '*'): [
      '지금 뭐라고 하셨습니까 그건 선 넘으신 겁니다 녹화 중입니다',
      '신고자한테 그런 말씀을 하시면 안 되죠 사과해 주십시오',
  ],
  ('DENY', 'doc'): [
      '무슨 건 때문에 그러시죠 서류 보시면 나옵니다',
      '배송 쪽 서류는 워낙 많이 오가서요 어느 걸 말씀하시는지 모르겠습니다',
  ],
  ('CONCEDE_MIN', 'doc'): [
      '28분에 강도현 씨가 보낸 배송 책임 서류 화면 받긴 받았습니다 그게 왜 중요한지는 모르겠고요',
  ],
  ('DENY', 'appointment'): [
      '따로 만날 일은 없었습니다',
      '약속이라고 할 만한 건 없었어요',
  ],
  ('CONCEDE_MIN', 'appointment'): [
      '서류 얘기로 정수연 씨가 찾아오라고 한 적은 있었습니다 약속이 있었다고 들어간 건 아니고요',
  ],
  ('DENY', 'entered'): [
      '302호 안에는 들어간 적 없습니다 신고할 때 문밖에서 봤어요',
      '제가 왜 남의 집에 들어갑니까 신고하려고 문 앞에서 본 게 전부예요',
  ],
  ('CHALLENGE', 'entered'): [
      '그 종이를 제가 언제 만졌는지 그걸로 어떻게 압니까',
      '서류 조각이 제 거라고 해서 제가 그 방에 있었다는 건 아니죠',
  ],
  ('CONCEDE_MIN', 'entered'): [
      '…54분쯤 서류 얘기를 하러 잠깐 들어갔습니다 들어간 것과 다치게 한 건 전혀 다른 얘기고요',
  ],
  ('DENY', 'report_time'): [
      '22시 7분에 처음 보고 바로 신고했습니다',
  ],
  ('CHALLENGE', 'report_time'): [
      '놀란 사람이 시간을 분 단위로 기억합니까',
  ],
  ('CONCEDE_MIN', 'report_time'): [
      '처음 본 시각과 신고한 시각이 조금 다를 수는 있습니다 그땐 정신이 없었어요',
  ],
  ('DENY', 'push'): [
      '사람 몸에 손댄 적 없습니다',
      '그 말은 취소하시죠 저는 신고한 사람입니다',
  ],
  ('CHALLENGE', 'push'): [
      '그 자국이 제 거라는 건 어떻게 확인하셨습니까',
  ],
  ('CONCEDE_MIN', 'push'): [
      '더 말하지 않겠습니다 변호인과 얘기하겠습니다',
  ],
 },
}

# Ordinary questions (no dossier fact involved): topic cue -> variants. Keeps relationship/background talk instant and in voice.
TOPICS = {
 's2': [
  (re.compile(r'(사이|관계|친구|누구)'), ['수연이랑은 오래된 친구예요 같은 회사 다니다가 공방도 같이 하게 됐고요',
                                        '친구예요 대학 때부터요 공방은 둘이 시작했고요']),
  (re.compile(r'(공방|동업|정산|사업)'), ['담다공방이요 수연이가 만들고 제가 운영을 맡았어요 요즘 정산이 좀 복잡했고요',
                                        '공방은 수연이가 주로 만들고 저는 장부 쪽을 봤어요']),
  (re.compile(r'(성격|어떤 사람|평소)'), ['수연이는 고집 있고 정이 많은 애였어요 …이런 말 하게 될 줄은 몰랐어요']),
  (re.compile(r'(마지막|언제 봤|언제 만났)'), ['마지막으로 본 게 언제인지는 기억을 좀 더듬어 봐야 해요']),
 ],
 's1': [
  (re.compile(r'(사이|관계|애인|연애|헤어)'), ['3년 사귀었고 헤어졌습니다 그게 전부입니다', '전 연인입니다 더 필요한 거 있으십니까']),
  (re.compile(r'(직업|일|근무|회사)'), ['물류설비 업체 야간 교대 근무합니다']),
  (re.compile(r'(왜 헤어|이유)'), ['그건 개인적인 겁니다']),
 ],
 's3': [
  (re.compile(r'(사이|관계|아는|알던)'), ['옆집 301호 사는 이웃이고 정수연 씨 공방 배송 일을 도와 자주 오갔습니다']),
  (re.compile(r'(직업|일|근무|회사)'), ['배송 집하 계약직입니다 서류와 분류 쪽 일이 많고요']),
  (re.compile(r'(신고|발견|처음)'), ['22시 7분에 112에 신고했습니다 문이 열려 있어서요']),
 ],
}


# Same point pushed again after every authored variant was used / question outside every topic: still instant, still in voice.
REPEAT = {
 's2': ['아까 말씀드린 그대로예요', '같은 질문이라 같은 대답밖에 못 드려요', '…그 얘기는 이미 말씀드렸어요 더 드릴 말씀이 없어요'],
 's1': ['아까 말했습니다', '같은 걸 몇 번 물으십니까', '더 할 말 없습니다'],
 's3': ['그건 아까 말씀드렸습니다', '같은 내용입니다 서류 보시면 나옵니다', '제가 더 말씀드릴 건 없습니다'],
}
CLARIFY = {
 's2': ['어떤 부분을 말씀하시는 거예요', '질문이 조금 넓은데요 뭘 알고 싶으신 거예요', '그때는… 구체적으로 어느 시간 말씀이세요'],
 's1': ['정확히 뭘 묻는 겁니까', '질문을 구체적으로 하십시오', '무슨 얘기입니까 시간부터 말씀하세요'],
 's3': ['무슨 건 때문에 그러시죠', '어느 건 말씀이신지 정확히 말씀해 주시겠습니까', '서류 쪽 얘기면 정확히 말씀해 주십시오'],
}


def _key_lines(sid, tactic, focus):
    b = BANK.get(sid, {})
    return b.get((tactic, focus)) or b.get((tactic, '*')) or []


def pick(sid: str, plan: dict, question: str, used: dict) -> str | None:
    """Return an authored line for this plan, or None. `used` is per-suspect {key: count}; escalates through the variants
    and, once exhausted, returns None for CONCEDE/DENY (so the model can handle a genuinely new push) but cycles
    DEMAND_PROOF/STONEWALL variants from the last item."""
    tactic, focus = plan['tactic'], plan.get('focus')
    if plan.get('abuse'):
        tactic = 'STONEWALL' if plan['tactic'] == 'STONEWALL' else 'REBUKE'
    lines = _key_lines(sid, tactic, focus)
    if not lines and tactic == 'ANSWER':
        for rx, ls in TOPICS.get(sid, []):
            if rx.search(question or ''):
                lines = ls; focus = 'topic:' + rx.pattern; break
    if not lines:
        if tactic == 'ANSWER':   # nothing near a secret and no topic matched: ask what is meant (never a dead or slow turn)
            c = CLARIFY.get(sid, []); n = used.get(('clarify',), 0); used[('clarify',)] = n + 1
            return c[n % len(c)] if c else None
        return None
    k = (tactic, focus if (tactic, focus) in BANK.get(sid, {}) or str(focus).startswith('topic:') else '*')
    n = used.get(k, 0)
    if tactic in ('DEMAND_PROOF', 'STONEWALL', 'REBUKE'):
        # escalate with how many times the detective has accused/pushed
        n = max(n, min(plan.get('accusations', 0) - 1, len(lines) - 1)) if tactic == 'DEMAND_PROOF' else n
        used[k] = max(used.get(k, 0), n) + 1
        return lines[min(n, len(lines) - 1)]
    used[k] = n + 1
    if n < len(lines):
        return lines[n]
    r = REPEAT.get(sid, []); m = used.get(('repeat',), 0); used[('repeat',)] = m + 1
    return r[m % len(r)] if r else None
