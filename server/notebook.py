"""Investigation notebook (server side): keeps FACTS, STATEMENTS, HYPOTHESES and TO-CHECK items apart, and compares two records
without ever issuing a verdict.

observation/record : what a source says (acquired evidence), with where it was found, its original source family, and its limits
statement          : who said it, when in the case clock, in answer to what, and whether it was a claim / admission / correction
hypothesis         : the player's own idea (free text + optional links). Never promoted to fact by the server
to_check           : record requests that are possible now (cost/time/prerequisite shown, result NOT shown) + the player's open questions
compare            : two items side by side — the times each mentions, whether they come from the same original source family,
                     which limits apply. "Same original" summaries are not counted as two independent records.
A document's recorded time is NOT the time the event happened (DOCUMENT/MESSAGING/PHONE families say so explicitly).
"""
from __future__ import annotations
import re
from .runtime import GuardError
from .question_frame import clock_mentions

EST_WORDS = ('시각 편차', '시각오차', '시각 오차', '시계', '압축', '기기시각', '저장지연', '부정확', '오차')
RECORDED_TIME_NOT_EVENT = {'DOCUMENT', 'MESSAGING', 'PHONE_DIGITAL', 'FINANCE', 'DISPATCH'}
MAX_HYP = 40


def _fam(ctrl):
    return {e['id']: e for e in ctrl.world._canon['evidence']}


def _time_info(e):
    text = f"{e.get('detail','')} {e.get('name','')}"
    times = sorted(set(clock_mentions(re.sub(r'(\d{1,2}):(\d{2})', r'\1시 \2분', text))))
    est = any(w in (e.get('limitations', '') or '') for w in EST_WORDS)
    note = ''
    if e.get('source_family') in RECORDED_TIME_NOT_EVENT:
        note = '이 기록에 적힌 시각은 기록·전송·접수 시각일 수 있고, 사건이 일어난 시각과 같다고 단정할 수 없다'
    return {'times': times, 'certainty': 'estimated' if est else 'recorded', 'certainty_ko': '추정 범위(시각 오차 가능)' if est else '기록된 시각', 'note': note}


def observations(ctrl):
    ev = _fam(ctrl); out = []
    for eid in sorted(ctrl.world.available_evidence):
        e = ev.get(eid)
        if not e: continue
        ti = _time_info(e)
        out.append({'id': eid, 'kind': 'record', 'title': e['name'], 'what': e['detail'], 'found': e['found'], 'source_family': e.get('source_family', ''),
                    'limitation': e['limitations'], 'time': ti, 'chain': ctrl.state.acquired_chain.get(eid, [])})
    return out


def statements(ctrl, service):
    """Per suspect, in case-clock order. Built from the server's own committed turns (never from client text)."""
    out = []
    mem = getattr(service, '_strategy', {}) if service else {}
    for sid, m in mem.items():
        name = ctrl.world.suspects[sid]['name']
        for i, h in enumerate(m.history):
            kind = {'CONCEDE_MIN': 'admission', 'CHALLENGE': 'challenge', 'DENY': 'claim', 'DEMAND_PROOF': 'pushback', 'STONEWALL': 'refusal'}.get(h.get('tactic'), 'statement')
            out.append({'actor': sid, 'name': name, 'turn': i + 1, 'asked': h['q'], 'said': h['a'], 'kind': kind, 'tactic': h.get('tactic'),
                        'times': sorted(set(clock_mentions(h['a']))), 'unverified': True,
                        'evidence': h.get('evidence')})
        for r in m.reversals:
            out.append({'actor': sid, 'name': name, 'turn': None, 'asked': '', 'said': '처음 부인했던 점을 나중에 인정함 (기록으로 남음)', 'kind': 'change_of_story', 'fact': r, 'times': [], 'unverified': False})
    return out


def to_check(ctrl):
    from .case_flow import REQUESTS
    items = []
    for eid, r in REQUESTS.items():
        if eid in ctrl.world.available_evidence: continue
        ok, why = ctrl.desk._eligible(eid)
        items.append({'request_id': eid, 'label': r['label'], 'cost': r['cost'], 'minutes': r['minutes'], 'available': ok, 'blocked_reason': '' if ok else why})
    items.sort(key=lambda x: (not x['available'], x['cost']))
    return {'requests': items, 'questions': list(getattr(ctrl, 'open_questions', []))}


def add_hypothesis(ctrl, text, links=()):
    text = (text or '').strip()
    if len(text) < 2 or len(text) > 600: raise GuardError('가설은 2~600자로 적어 주세요')
    hyps = ctrl.__dict__.setdefault('hypotheses', [])
    if len(hyps) >= MAX_HYP: raise GuardError('가설은 최대 %d개까지 적을 수 있습니다' % MAX_HYP)
    ok_links = [l for l in links if isinstance(l, str) and l in ctrl.world.available_evidence][:8]
    h = {'id': f'H{len(hyps)+1}', 'text': text, 'links': ok_links, 'status': 'open', 'clock': ctrl.clock_text()}
    hyps.append(h); return h


def add_question(ctrl, text):
    text = (text or '').strip()
    if len(text) < 2 or len(text) > 300: raise GuardError('질문은 2~300자로 적어 주세요')
    qs = ctrl.__dict__.setdefault('open_questions', [])
    if len(qs) >= 40: raise GuardError('열어 둔 질문이 너무 많습니다')
    q = {'id': f'Q{len(qs)+1}', 'text': text, 'clock': ctrl.clock_text()}; qs.append(q); return q


def compare(ctrl, service, a, b):
    """a/b: evidence id (e.g. 'V21-E07') or statement ref 's2#3'. Returns facts to weigh; never a conclusion."""
    ev = _fam(ctrl)
    def resolve(ref):
        if ref in ev and ref in ctrl.world.available_evidence:
            e = ev[ref]; ti = _time_info(e)
            return {'item_ref': ref, 'kind': 'record', 'title': e['name'], 'text': e['detail'], 'times': ti['times'], 'certainty': ti['certainty_ko'], 'time_note': ti['note'],
                    'source_family': e.get('source_family', ''), 'facts': e.get('fact_ids', []), 'limitation': e['limitations']}
        mo = re.fullmatch(r'obs:([a-z0-9_]+):([a-z0-9_]+)', ref or '')
        if mo:
            rec = ctrl.props.observed.get(mo.group(1), {}).get(mo.group(2))
            if not rec: raise GuardError('아직 기록하지 않은 관찰입니다')
            return {'item_ref': ref, 'kind': 'observation', 'title': f"{rec['prop_label']} — {rec['label']}", 'text': rec['text'], 'times': [], 'certainty': '현장에서 직접 본 것',
                    'time_note': '', 'source_family': 'SCENE:' + mo.group(1), 'facts': [], 'limitation': rec['limit']}
        m = re.fullmatch(r'(s[1-3])#(\d+)', ref or '')
        if m and service:
            mem = getattr(service, '_strategy', {}).get(m.group(1))
            i = int(m.group(2)) - 1
            if mem and 0 <= i < len(mem.history):
                h = mem.history[i]
                return {'item_ref': ref, 'kind': 'statement', 'title': f"{ctrl.world.suspects[m.group(1)]['name']}의 진술 {i+1}", 'text': h['a'], 'times': sorted(set(clock_mentions(h['a']))),
                        'certainty': '본인 주장(미검증)', 'time_note': '', 'source_family': 'STATEMENT:' + m.group(1), 'facts': [], 'limitation': '진술은 확인 전까지 사실로 취급하지 않는다'}
        raise GuardError('비교할 수 없는 기록입니다(확보하지 않았거나 없는 항목)')
    A, B = resolve(a), resolve(b)
    same_family = A['source_family'] == B['source_family'] and bool(A['source_family'])
    shared_facts = sorted(set(A['facts']) & set(B['facts']))
    ta, tb = set(A['times']), set(B['times'])
    notes = []
    if same_family: notes.append('같은 출처군의 기록입니다. 같은 원본의 요약·사본이면 독립 근거 두 개로 세지 않습니다')
    if ta and tb and not (ta & tb): notes.append('두 기록이 가리키는 시각이 겹치지 않습니다. 시각이 다른 것과 모순인 것은 다릅니다. 각 기록의 시각 한계를 확인하세요')
    if ta & tb: notes.append('같은 시각이 두 기록에 모두 나옵니다: ' + ', '.join(sorted(ta & tb)))
    for X in (A, B):
        if X['time_note']: notes.append(f"{X['title']}: {X['time_note']}")
    return {'a': A, 'b': B, 'same_source_family': same_family, 'shared_fact_ids': shared_facts, 'notes': notes, 'verdict': None}


def projection(ctrl, service):
    return {'observations': observations(ctrl), 'statements': statements(ctrl, service), 'hypotheses': list(getattr(ctrl, 'hypotheses', [])),
            'scene_observations': ctrl.props.scene_observations(), 'to_check': to_check(ctrl), 'custody': ctrl.props.custody(), 'clock': ctrl.clock_text()}
