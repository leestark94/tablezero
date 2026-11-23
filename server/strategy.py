"""Suspect strategy engine (V21 common interrogation core, case data injected).

Design: a suspect KNOWS everything they did (dossier, server-only). Evidence does not "unlock" memories; it changes the
suspect's estimate of what the detective can prove, and the suspect re-plans each turn:
    read the detective  →  pick a tactic per relevant secret  →  hand the speaker ONLY what this tactic allows to be said.
The speaking model never sees secrets the plan keeps hidden, so it cannot blurt them, and its prompt stays short (fast).

Tactics (per relevant secret / per turn):
  DENY            cover story, no detail                    (not proven, not shown)
  CHALLENGE       attack the shown evidence's own limits     (shown once, evidence has a weakness)
  CONCEDE_MIN     admit exactly the proven fact + reframe    (proven, or challenged already)
  DEMAND_PROOF    "then show me"                             (accused / told 'we have evidence' with nothing shown)
  STONEWALL       short refusal / silence / counsel          (repeated accusation or pressure)
  ANSWER          ordinary cooperative answer                 (question not near any secret)
Nothing here decides truth or guilt; the case truth is untouched and confession is never the only route.
"""
from __future__ import annotations
import json, re
from dataclasses import dataclass, field
from pathlib import Path

ACCUSE = re.compile(r'(범인|죽였|죽인|살인|네가\s*했|당신이\s*했|니가\s*했|너지|자백|밀었지|거짓말\s*하지)')
BLUFF = re.compile(r'(증거\s*(다|도)?\s*있|다\s*알고|다\s*알아|이미\s*(다\s*)?(알|확인)|목격자|CCTV에\s*다)')
# Degrading / sexual / abusive remarks. A real person under questioning does not answer these politely like a help desk:
# they take offence, point out the room is being recorded, and stop cooperating if it continues.
ABUSE = re.compile(r'(가슴|젖|엉덩이|옷\s*(을|좀)?\s*벗|벗어|몸\s*(좀)?\s*보여|섹스|성관계|모텔|자자|씨발|시발|ㅅㅂ|병신|ㅂㅅ|개새|좆|존나\s*못|미친\s*년|년아|창녀|꺼져)')
PRESSURE = re.compile(r'(빨리\s*말해|말\s*안\s*해|똑바로|어디서\s*거짓|감옥|평생|인생\s*끝)')


@dataclass
class SuspectState:
    tactic_history: list = field(default_factory=list)
    challenged: set = field(default_factory=set)      # fact ids whose evidence was already challenged
    conceded: set = field(default_factory=set)        # fact ids admitted (become part of the allowed story)
    accusations: int = 0
    repeats: dict = field(default_factory=dict)       # fact id -> times the detective pushed on it
    bank_used: dict = field(default_factory=dict)     # authored-line variants already spoken (server/line_bank.py)
    abused: int = 0                                   # degrading remarks by the detective in this interview


def _dossier(personas: dict, sid: str) -> dict:
    return personas['suspects'][sid].get('dossier', {})


def relevant_facts(dossier: dict, question: str, presented_now: str | None):
    q = question or ''
    out = []
    for fid, f in dossier.get('facts', {}).items():
        hit = any(c in q for c in f.get('cues', []))
        if presented_now and presented_now in f.get('proven_by', []):
            hit = True
        if hit:
            out.append(fid)
    return out


def plan_turn(personas: dict, sid: str, state: SuspectState, question: str, presented_all: set,
              presented_now: str | None, evidence_by_id: dict, pressured: bool) -> dict:
    d = _dossier(personas, sid)
    facts = d.get('facts', {})
    q = question or ''
    accused = bool(ACCUSE.search(q))
    bluff = bool(BLUFF.search(q)) and not presented_now
    pressed = pressured or bool(PRESSURE.search(q))
    if accused:
        state.accusations += 1
    rel = relevant_facts(d, q, presented_now)
    for fid in rel:
        state.repeats[fid] = state.repeats.get(fid, 0) + 1

    say, avoid, directives, counter = [], [], [], None
    focus = None
    tactic, mode = 'ANSWER', 'answer'

    # 0) degrading / sexual remark: in-character offence, never a polite refusal; repeated -> stop talking
    if ABUSE.search(q):
        state.abused += 1
        state.tactic_history.append('REBUKE')
        allowed = list(dict.fromkeys(d.get('public', []) + [facts[x]['concede'] for x in sorted(state.conceded)]))
        if state.abused >= 2:
            return {'tactic': 'STONEWALL', 'mode': 'request_counsel', 'allowed': allowed, 'this_turn': [],
                    'directives': ['또 그런 말을 들었다. 차갑게, 이 면담은 더 못 하겠다, 변호인 불러 달라, 방금 말 다 녹화됐다고 말한다'],
                    'counter_question': None, 'relevant': [], 'accused': False, 'bluff': False, 'pressed': True, 'abuse': True}
        return {'tactic': 'REBUKE', 'mode': 'angry', 'allowed': allowed, 'this_turn': [],
                'directives': ['형사가 방금 모욕적이고 부적절한 말을 했다. 그 말을 되풀이하지 않는다. 정색하고 따진다: 지금 녹화되고 있다, 형사가 할 말이냐, 사과하라. 사건 얘기는 하지 않는다'],
                'counter_question': None, 'relevant': [], 'accused': False, 'bluff': False, 'pressed': True, 'abuse': True}

    # 1) accused / bluffed with nothing on the table: deny and make the detective show it
    if (accused or bluff) and not presented_now:
        if state.accusations >= 3 or (pressed and state.accusations >= 2):
            tactic, mode = 'STONEWALL', d.get('stonewall_mode', 'request_counsel')
            directives.append(d.get('stonewall', '더 이상 이런 식이면 대답하지 않겠다고 짧게 말한다'))
        else:
            tactic, mode = 'DEMAND_PROOF', 'counter'
            directives.append(d.get('on_accused', '어이없다는 듯 부인하고, 그렇게 확신하면 증거를 보여 달라고 되묻는다'))
    # 2) evidence on the table or questions near a secret: decide per fact
    RANK = {'critical': 3, 'serious': 2, 'minor': 1}
    decided = []   # (rank, tactic, mode)
    base_tactic, base_mode = tactic, mode
    for fid in sorted(rel, key=lambda x: -RANK.get(facts[x].get('sensitivity', 'minor'), 1)):
        f = facts[fid]
        tactic, mode = 'ANSWER', 'answer'
        proven = set(f.get('proven_by', [])) & presented_all
        if fid in state.conceded:
            say.append(f['concede']); decided.append((RANK.get(f.get('sensitivity','minor'),1), 'CONCEDE_MIN', 'partial_admission', fid)); continue
        if not proven:
            # never volunteer; keep the cover
            if f.get('cover'):
                say.append(f['cover'])
            decided.append((RANK.get(f.get('sensitivity','minor'),1), 'DENY', 'deny' if f.get('sensitivity') != 'minor' else 'uncertain', fid))
            continue
        shown = presented_now in f.get('proven_by', []) if presented_now else False
        weak = f.get('challenge') and fid not in state.challenged
        strong = len(proven) >= f.get('concede_after', 1)
        if shown and weak and not (strong and len(proven) >= 2):
            state.challenged.add(fid)
            tactic, mode = 'CHALLENGE', 'counter'
            counter = f['challenge']
            if f.get('cover'):
                say.append(f['cover'])
        elif strong or fid in state.challenged or state.repeats.get(fid, 0) >= 3:
            state.conceded.add(fid)
            tactic, mode = 'CONCEDE_MIN', 'partial_admission'
            say.append(f['concede'])
            if f.get('reframe'):
                directives.append(f['reframe'])
            for other in f.get('then_volunteer', []):   # e.g. "when I left she was fine" — the suspect's own defence
                if other in facts:
                    say.append(facts[other].get('concede') or facts[other].get('cover', ''))
        else:
            tactic, mode = 'DENY', 'deny'
            if f.get('cover'):
                say.append(f['cover'])
        decided.append((RANK.get(f.get('sensitivity','minor'),1), tactic, mode, fid))
    # accusation/bluff handling wins; otherwise the most sensitive fact sets the stance for the whole reply
    if base_tactic in ('STONEWALL', 'DEMAND_PROOF'):
        tactic, mode = base_tactic, base_mode
    elif decided:
        best = max(decided, key=lambda x: (x[0], x[1] != 'CONCEDE_MIN'))
        tactic, mode, focus = best[1], best[2], best[3]
    else:
        tactic, mode = base_tactic, base_mode
    if pressed and tactic not in ('STONEWALL',):
        directives.append('위압적인 말투가 불쾌하다는 걸 짧게 드러낸다. 겁먹어서 털어놓지는 않는다')

    # what the speaker may assert: public persona + cover + everything already conceded + this turn's plan
    allowed = list(dict.fromkeys([s for s in d.get('public', [])] + [facts[x]['concede'] for x in sorted(state.conceded)] + say))
    state.tactic_history.append(tactic)
    return {'tactic': tactic, 'mode': mode, 'allowed': allowed, 'this_turn': list(dict.fromkeys(say)),
            'directives': directives, 'counter_question': counter, 'relevant': rel,
            'accused': accused, 'bluff': bluff, 'pressed': pressed, 'focus': focus,
            'accusations': state.accusations, 'repeat': state.repeats.get(focus, 0) if focus else 0,
            'shown_now': presented_now}


TACTIC_KO = {
    'ANSWER': '평범하게 답한다. 아는 범위에서 짧게',
    'DENY': '부인한다. 아래 "이번에 할 말" 범위를 넘지 않는다. 구체적인 시각·장소를 새로 만들지 않는다',
    'CHALLENGE': '제시된 자료의 약점을 짚어 되묻는다. 인정하지 않는다',
    'CONCEDE_MIN': '이미 드러난 그 사실 하나만 최소한으로 인정하고, 그 이상은 인정하지 않는다',
    'DEMAND_PROOF': '부인하고, 근거를 보여 달라고 되묻는다',
    'STONEWALL': '대답을 거부하거나 변호인을 요구한다. 아주 짧게',
    'REBUKE': '모욕을 당한 사람으로서 화를 내며 항의한다. 공손한 거절문이 아니라 감정이 실린 말',
}


def habit_hint(habits: list, recent_lines: list) -> str:
    """Offer at most one verbal habit, on roughly one turn in three, and never one used in the last lines.
    (Listing all habits every turn made the model glue them onto every answer.)"""
    if not habits or len(recent_lines) % 3 != 1:
        return ' / 이번에는 입버릇을 쓰지 않는다'
    fresh = [h for h in habits if not any(h in r for r in recent_lines[-4:])]
    return (' / 입버릇 하나를 써도 된다: ' + fresh[len(recent_lines) % len(fresh)]) if fresh else ' / 이번에는 입버릇을 쓰지 않는다'


def speaker_messages(personas: dict, sid: str, plan: dict, question: str, presented_evidence: dict | None,
                     motions: list, recent_lines: list) -> list:
    """Short prompt for the line generator: voice + plan + only the allowed statements. No hidden secret is present."""
    p = personas['suspects'][sid]; d = p.get('dossier', {})
    lines = [
        f"너는 '{p.get('name', sid)}'({p['age']}세, {p['job']})다. 경찰서 진술녹화실에서 너를 의심하는 형사와 마주 앉아 있다.",
        '너는 상담원이나 비서가 아니다. 공손한 안내 문구("말씀해 주시길 바랍니다", "확인해 주시길")를 쓰지 않는다. 너 자신에 대해 1인칭(저, 제가)으로만 말한다. 너를 이름이나 3인칭으로 부르지 않는다',
        '너는 자기를 지키려는 사람이다. 불리한 건 먼저 말하지 않고, 짧게 끊어 말하거나 되묻거나 불쾌함을 드러낸다',
        '[말투] ' + p['register'] + habit_hint(p.get('verbal_habits', []), recent_lines),
        '[성격] ' + d.get('temperament', ''),
        '[이번 대응] ' + TACTIC_KO[plan['tactic']],
    ]
    if plan['directives']:
        lines.append('[방법] ' + ' / '.join(plan['directives']))
    if plan['counter_question']:
        lines.append('[되물을 것] ' + plan['counter_question'])
    lines.append('[네가 말해도 되는 사실 — 이것 말고 그날 밤의 구체적인 사실은 말하지 않는다]')
    lines += ['- ' + s for s in plan['allowed']] or ['- (없음)']
    if plan['this_turn']:
        lines.append('[이번 질문에 쓸 말 — 내용을 빠뜨리지 말고 네 말투로] ' + ' / '.join(plan['this_turn']))
    if presented_evidence:
        lines.append(f"[형사가 방금 보여준 자료] {presented_evidence['name']} — {presented_evidence['detail']} (한계: {presented_evidence['limitations']})")
    if recent_lines:
        lines.append('[네가 직전에 한 말, 반복 금지] ' + ' / '.join(recent_lines[-3:]))
    lines += [
        '[주의] 형사가 보여준 자료 내용을 그대로 읽어 주지 않는다. 자료에 나온 다른 사람 이야기를 네 일처럼 말하지 않는다. 매번 같은 말로 끝맺지 않는다',
        '[규칙] 대사 한 줄만 쓴다(JSON·따옴표·설명 없이). 한국어 구어 1~2문장, 50자 안팎. 대사만. 문장 끝 마침표 금지. 질문을 되풀이하지 않는다. 자신이 범인이라고 말하지 않는다. 다른 사람을 범인으로 단정하지 않는다',
    ]
    return [{'role': 'system', 'content': '\n'.join(lines)}, {'role': 'user', 'content': question}]


# Body language is chosen by the CONVERSATIONAL situation (what was just asked / done to them) and varies turn to turn.
# It must never read as a lie detector: the same tactic (e.g. DENY) is used for true and false denials, so several motions are
# acceptable for it and the pick rotates by turn number + suspect, not by whether the statement is true.
MOTION_PREF = {
    'ANSWER': ['still', 'cup_touch', 'finger_tap', 'look_down', 'chair_shift'],
    'DENY': ['still', 'chair_shift', 'cup_touch', 'back_in_chair', 'look_down', 'finger_tap'],
    'CHALLENGE': ['lean_forward', 'still', 'jaw_tight', 'cup_touch'],
    'CONCEDE_MIN': ['exhale', 'hand_stop', 'deep_breath', 'look_down', 'chair_shift'],
    'DEMAND_PROOF': ['lean_forward', 'jaw_tight', 'cross_arms', 'still', 'back_in_chair'],
    'STONEWALL': ['cross_arms', 'back_in_chair', 'lean_back', 'still'],
    'REBUKE': ['lean_back', 'jaw_tight', 'back_in_chair', 'cross_arms'],
    'OFFTOPIC': ['still', 'chair_shift', 'finger_tap'],
    'UNKNOWN_OTHER': ['still', 'cup_touch', 'chair_shift'],
    'COUNSEL_Q': ['still', 'cross_arms', 'back_in_chair'],
    'CLARIFY': ['still', 'lean_forward', 'chair_shift'],
}


def pick_motion(tactic: str, available: list, variant: int = 0) -> str:
    prefs = [m for m in MOTION_PREF.get(tactic, []) if m in available]
    if prefs:
        return prefs[variant % len(prefs)]
    return available[0] if available else 'still'


# Portrait beat for the on-screen performance: derived from what the DETECTIVE just did (accused, showed a record, insulted, pressed),
# never from whether the suspect is telling the truth.
def pick_beat(plan: dict, presented_evidence) -> tuple:
    t = plan['tactic']
    if t == 'REBUKE': return 'Angry', 0.8
    if t in ('STONEWALL', 'COUNSEL_Q'): return 'Withdrawn', 0.6
    if presented_evidence: return 'Challenged', 0.5 + 0.1 * min(3, plan.get('accusations', 0))
    if plan.get('accused') or t == 'DEMAND_PROOF': return 'Guarded', 0.5 + 0.1 * min(3, plan.get('accusations', 0))
    if t in ('CLARIFY', 'UNKNOWN_OTHER', 'OFFTOPIC'): return 'Considering', 0.3
    if plan.get('pressed'): return 'Guarded', 0.5
    return 'Answering', 0.3


FALLBACK = {
    'ANSWER': '그건 아까 말씀드린 그대로예요',
    'DENY': '아니요, 그런 일 없어요',
    'CHALLENGE': '그걸로 뭘 확인하셨다는 건지 모르겠네요',
    'CONCEDE_MIN': '…그건 맞아요 그 이상은 없어요',
    'DEMAND_PROOF': '무슨 근거로 그러시는 거예요 있으면 보여주세요',
    'STONEWALL': '더는 말 안 하겠습니다',
    'REBUKE': '지금 그게 형사가 할 말이에요? 이거 다 녹화되고 있어요',
}


def fallback_line(plan: dict) -> str:
    """Deterministic line when every generation failed: the suspect still answers in-stance (never a dead turn)."""
    if plan.get('counter_question'):
        return plan['counter_question'].rstrip('.')
    if plan['tactic'] in ('DENY', 'CONCEDE_MIN') and plan.get('this_turn'):
        return plan['this_turn'][0].rstrip('.')
    return FALLBACK.get(plan['tactic'], '…')
