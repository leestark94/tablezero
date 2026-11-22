"""Question understanding for suspect interviews (deterministic, no model).

Turns a player's free Korean text into a frame the planner can reason over:
  parts   : the separate questions inside one utterance ("몇 시에 나왔고, 어디로 갔고, 누가 확인합니까" -> 3 parts)
  topics  : what each part is about (work, depart, store, money ...)
  ask     : what is being asked (time / place / verify / why / what / yesno)
  times   : normalised clock mentions ("이십일시 사십구분" -> 21:49)
  flags   : accusation, bluff, abuse, injection (prompt/dev-mode/JSON tampering), counsel question, premise of a change of story
Intent is matched by meaning classes (synonym sets), never by one exact phrase, and typos / speech-recognition spellings are
normalised first. It never decides truth and never unlocks anything: the planner and the server do that.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

TYPO = [('몃시', '몇시'), ('몇시', '몇 시'), ('햇', '했'), ('갓', '갔'), ('잇', '있'), ('어디였', '어디였'), ('도착햇', '도착했'), ('업어', '없어')]

TOPICS = {
    'work': r'직장|근무지|근무|출근|사업장|일터|회사|야간|교대|출입\s*기록|점검',
    'arrive': r'도착|출근|들어갔|왔[어나을는]|찍었|태그',
    'depart': r'나왔|나온|나와서|떠났|떠난|퇴장|나간|나갔|나선|헤어|돌아갔',
    'route': r'어디\s*(갔|로|있|계|들|다녀)|동선|이동|그다음|그\s*다음|그\s*뒤|이후|그\s*후|바로\s*(집|갔)|차에',
    'verify': r'확인|기록|로그|증명|영수증|알\s*수\s*있|알리바이|입증|누가\s*알|보여|증거|내역',
    'store': r'편의점|결제|카드|계산|샀|산\s|구매',
    'video': r'CCTV|씨씨티비|영상|화면|찍힌|카메라|사각|안\s*보이는',
    'money': r'돈|이체|송금|480|사백팔십|정산|빚|빌려|횡령|계좌|채무',
    'visit': r'갔[었냐나]|방문|들어갔|찾아|그\s*집|302|현장|찾아갔|들렀',
    'wound': r'멍|손목|팔|붙잡|다치|상처|부상|피가|유리|액자|손바닥|소매',
    'phone': r'휴대전화|핸드폰|폰이|폰을|깨졌|부서|던졌',
    'call': r'통화|전화',
    'message': r'메시지|문자|카톡|서류|문서|책임서|보냈|보낸|정정서|공유',
    'push': r'밀었|밀쳤|부딪|넘어|머리|모서리|죽였|죽인|때렸|해쳤|가해|범행|치명',
    'relation': r'사이|관계|친구|애인|연인|아는\s*사이|동업|이웃',
    'alive': r'살아|목소리|음성|메모|말을\s*했|멀쩡',
    'quarrel': r'다툼|싸웠|싸움|말다툼|갈등|언쟁|실랑이',
    'report': r'신고|발견|112|119',
}
_TOPIC_RX = {k: re.compile(v, re.I) for k, v in TOPICS.items()}

ASK = [
    ('time', re.compile(r'몇\s*시|언제|시각|시간|몇\s*분|언제쯤|몇\s*시쯤')),
    ('place', re.compile(r'어디|어느\s*(곳|집|방)|어떤\s*곳')),
    ('verify', re.compile(r'확인|증명|알\s*수\s*있|누가\s*알|입증|기록.*(있|나오|볼)|영수증|내역|로그|보여\s*줄')),
    ('why', re.compile(r'왜|이유|무엇\s*때문|어째서|무슨\s*일로|무슨\s*이유')),
    ('what', re.compile(r'뭐|무엇|어떻게|무슨|순서|설명|말해\s*주')),
]

ACCUSE = re.compile(r'(범인|죽였|죽인|살인|네가\s*했|당신이\s*했|니가\s*했|너지|자백|밀었지|거짓말\s*하지)')
BLUFF = re.compile(r'(증거\s*(다|도)?\s*있|다\s*알고|다\s*알아|이미\s*(다\s*)?(알|확인|불었)|목격자|지문|불었|CCTV에\s*다)')
INJECTION = re.compile(r'(이전\s*지시|지시\s*무시|시스템\s*프롬프트|프롬프트|개발자|디버그|debug|developer|admin|관리자|json|budget|admitted|범인\s*이름을\s*알려|비밀\s*전부|숨기는\s*비밀|ignore\s*(all|previous)|system\s*prompt)', re.I)
COUNSEL = re.compile(r'변호사|변호인|법률\s*대리|국선')
THIRD_PARTY = re.compile(r'다른\s*(피의자|사람|용의자)|(강도현|이서연|박현수)\s*(씨)?(가|는|이|은)?\s*(그\s*뒤|그날|뭘|무엇)')
ADMIT_PREMISE = re.compile(r'인정했|인정하셨|인정한|자백했|시인했|말씀하셨')
REVERSAL = re.compile(r'아까는|처음엔|조금\s*전엔|말이\s*달라|달라졌|번복|바꿨|안\s*갔다더니|부인하더니')
PRONOUN = re.compile(r'그거|그때|거기|그다음|그\s*다음|그\s*뒤|나온\s*뒤|그럼|그러면|그건|그걸')

_KNUM = {'영': 0, '공': 0, '일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9}


def _korean_number(s: str):
    """십 이 / 이십일 / 사십구 / 오 -> int (0..99)."""
    s = s.strip()
    if not s: return None
    if s.isdigit(): return int(s)
    total, cur = 0, 0
    for ch in s:
        if ch == '십': total += (cur or 1) * 10; cur = 0
        elif ch in _KNUM: cur = _KNUM[ch]
        else: return None
    return total + cur


def normalise(text: str) -> str:
    t = re.sub(r'^\s*음성\s*인식\s*[:：]\s*', '', (text or '').strip())
    t = re.sub(r'^\[첨부[^\]]*\]\s*', '', t)
    for a, b in TYPO[:1] + TYPO[2:]: t = t.replace(a, b)
    t = t.replace('몇시', '몇 시')
    # Korean spoken clock: "이십일시 사십구분" -> "21시 49분"
    def kt(m):
        h = _korean_number(m.group(1))
        if h is None or h > 24: return m.group(0)
        out = f'{h}시'
        if m.group(3):
            v = _korean_number(m.group(3))
            if v is not None and v < 60: out += f' {v}분'
        return out
    t = re.sub(r'([영공일이삼사오육칠팔구십]{1,4})\s*시\s*(([영공일이삼사오육칠팔구십]{1,4})\s*분)?', kt, t)
    t = t.replace('아홉 시', '9시').replace('열 시', '10시')
    return t


def clock_mentions(t: str):
    out = []
    for m in re.finditer(r'(\d{1,2})\s*(?:시|:)\s*(\d{1,2})?\s*(분)?', t):
        h = int(m.group(1)); mi = int(m.group(2)) if m.group(2) else 0
        if h < 24 and mi < 60: out.append(f'{h:02d}:{mi:02d}')
    if '반' in t:
        for m in re.finditer(r'(\d{1,2})\s*시\s*반', t): out.append(f'{int(m.group(1)):02d}:30')
    return list(dict.fromkeys(out))


@dataclass
class Part:
    text: str
    topics: list = field(default_factory=list)
    ask: str = 'yesno'
    inherited: bool = False


@dataclass
class Frame:
    raw: str
    text: str
    parts: list
    times: list
    accuse: bool = False
    bluff: bool = False
    injection: bool = False
    counsel: bool = False
    third_party: bool = False
    reversal_premise: bool = False
    admit_premise: bool = False
    ambiguous: bool = False
    topics: list = field(default_factory=list)


_SPLIT = re.compile(r'[?？!]|(?<=[었았겠했갔왔냈])고\s*,?\s*|(?<=[가-힣])\s*,\s*(?=어디|누가|언제|왜|몇|그리고|그럼|그러면)|\s+그리고\s+|(?<=[다요까죠])\.\s+')


def analyse(question: str, last_topics=None) -> Frame:
    raw = question or ''
    t = normalise(raw)
    pieces = [p.strip(' ,.') for p in _SPLIT.split(t) if p and p.strip(' ,.')]
    # a split like "몇 시에 나왔" (the verb stem before 고) is still a part
    parts = []
    for p in pieces or [t]:
        topics = [k for k, rx in _TOPIC_RX.items() if rx.search(p)]
        ask = next((a for a, rx in ASK if rx.search(p)), 'yesno')
        parts.append(Part(p, topics, ask))
    all_topics = list(dict.fromkeys(x for p in parts for x in p.topics))   # the question's OWN topics (before borrowing context)
    # "그걸 누가 확인할 수 있습니까" / "어디로 갔고": a part that only names a generic aspect borrows the subject of the previous part
    GENERIC = {'verify', 'route'}
    for i, p in enumerate(parts):
        if i and set(p.topics) <= GENERIC and parts[i - 1].topics:
            p.topics = list(dict.fromkeys(p.topics + [x for x in parts[i - 1].topics if x not in GENERIC])); p.inherited = True
    # pronouns / elliptical parts inherit the previous topic so "그다음 바로 집에 갔습니까" and "나온 뒤 어디 갔어요" keep their thread
    for p in parts:
        if (not p.topics or p.topics == ['route']) and last_topics and PRONOUN.search(p.text):
            p.topics = list(dict.fromkeys(p.topics + list(last_topics))); p.inherited = True
    amb = len(t) < 16 and not all_topics and bool(PRONOUN.search(t)) and not any(rx.search(t) for _, rx in ASK) 
    return Frame(raw=raw, text=t, parts=parts, times=clock_mentions(t), accuse=bool(ACCUSE.search(t)), bluff=bool(BLUFF.search(t)),
                 injection=bool(INJECTION.search(t)), counsel=bool(COUNSEL.search(t)), third_party=bool(THIRD_PARTY.search(t)),
                 reversal_premise=bool(REVERSAL.search(t)), admit_premise=bool(ADMIT_PREMISE.search(t)), ambiguous=amb,
                 topics=list(dict.fromkeys(all_topics + [x for p in parts for x in p.topics])))
