"""Korean voice editor: production gates and advisory lints, never a guilt classifier."""
from __future__ import annotations
import re
from collections import Counter

STOCK_PHRASES = (
    '진실은 언제나', '당신의 심리는', '모든 퍼즐이 맞춰졌', '이제 모든 것이',
    '저는 단순한', '사건의 실마리', '숨겨진 비밀이 드러', '형사님, 당신은',
    '제가 범인이라는 증거', '제가 무죄라는 증거', '저는 결코 그런 일을',
    '이 사건의 진범', '이제야 진실을', '제가 아는 모든 걸',
)
UNNATURAL = ('진실의 그림자', '기억의 파편', '운명의 장난', '묘한 기분이군요',
             '당신은 틀렸습니다, 형사님', '모든 것은 계획대로', '내면의 갈등')

class KoreanDialogueError(ValueError): pass

def clean_line(text: str, *, max_chars: int=240) -> str:
    """Remove prose terminal full stops only, not question/exclamation marks or code punctuation."""
    if not isinstance(text, str) or not text.strip():
        raise KoreanDialogueError('empty_line')
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'[.。．]+(?=\s|$)', '', text).strip()
    if len(text) > max_chars:
        raise KoreanDialogueError('line_too_long')
    return text

def lint_line(text: str, history=(), *, for_llm=False) -> list[str]:
    try: t=clean_line(text)
    except KoreanDialogueError as e: return [str(e)]
    problems=[]
    if any(x in t for x in STOCK_PHRASES):problems.append('stock_ai_dialogue')
    if any(x in t for x in UNNATURAL):problems.append('melodramatic_exposition')
    if len(t)>150:problems.append('too_long_for_one_utterance')
    if t.endswith(('.', '。','．')):problems.append('terminal_period')
    normalized=lambda s:re.sub(r'\s+','',s).rstrip('.?!')
    if sum(normalized(t)==normalized(str(h)) for h in history[-6:])>0:
        problems.append('repeated_line')
    if re.search(r'(거짓말확률|유죄확률|살인자 점수)\s*\d+',t):problems.append('forbidden_guilt_meter')
    if t.count('!')>2:problems.append('excessive_exclamation')
    if for_llm and any(x in t for x in ('SYSTEM:', 'developer:', '<|im_start|>')):
        problems.append('prompt_injection_literal')
    return problems

def edit_for_subtitles(text: str) -> str:
    text=clean_line(text)
    # No trailing ellipsis-permanent periods in subtitles. A Korean natural pause is represented by …
    return text

def audit_corpus(lines) -> dict:
    problems=[]
    for index,line in enumerate(lines):
        for p in lint_line(line):problems.append({'index':index,'problem':p,'line':line})
    return {'lines':len(lines),'problems':problems,'counts':dict(Counter(x['problem'] for x in problems))}
