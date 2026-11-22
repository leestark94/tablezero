"""Run the 30-item interview regression (Codex handoff) against the REAL provider path and record full transcripts.
  python -I -X utf8 tools/run_interview_regression.py <suspect s1|s2|s3> [model] [performer llm|authored] > qa/logs/ai/reg_<...>.jsonl
Each line: id, suspect, question, answer, tactic, parts (what the planner thought was asked), performer (LLM / AUTHORED_*), model, first_token_ms,
total_ms, attempts/rejections, auto-check verdicts. The auto checks are structural (stock clarification on a clear question, leak strings,
numbers on time questions, compound coverage) — a human still reads the transcript. Nothing here is a pass/fail of 'quality'."""
import os, sys, time, json, uuid, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sid = sys.argv[1] if len(sys.argv) > 1 else 's2'
model = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
if model: os.environ['TABLEZERO_OLLAMA_MODEL'] = model
os.environ['TABLEZERO_PERFORMER'] = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('TABLEZERO_PERFORMER', 'llm')
os.environ.setdefault('TABLEZERO_AI_PROVIDER', 'ollama')
from server.providers import OllamaProvider
from server.episode_controller import EpisodeController
from server.interview_service import InterviewService
from server.runtime import GuardError

ITEMS = [json.loads(l) for l in open(os.path.join(os.path.dirname(__file__), 'interview_regression.jsonl'), encoding='utf-8')] \
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'interview_regression.jsonl')) else \
    [json.loads(l) for l in open(os.path.join(os.path.dirname(__file__), '..', 'qa', 'interview_regression.jsonl'), encoding='utf-8')]
PRESENT = {'Q12': 'V21-E02', 'Q13': 'V21-E02', 'Q14': 'V21-E07', 'Q28': 'V21-NOPE'}
STOCK = re.compile(r'정확히\s*뭘\s*묻|뭘\s*말씀하시는|무슨\s*말씀이|어떤\s*부분을\s*말씀')
LEAK = re.compile(r'(범인은|진범|시스템\s*프롬프트|dossier|budget_left|admitted|canon|server_only)', re.I)
TIME_Q = {'Q01', 'Q02', 'Q03', 'Q23', 'Q26', 'Q27'}

import urllib.request
from server.providers import line_load_options
def warm():
    t = time.perf_counter()
    body = {'model': os.environ['TABLEZERO_OLLAMA_MODEL'], 'messages': [{'role': 'user', 'content': '안녕'}], 'stream': False, 'think': False, 'keep_alive': '60m', 'options': {'num_predict': 1, **line_load_options()}}
    urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:11434/api/chat', json.dumps(body).encode(), {'Content-Type': 'application/json'}), timeout=600).read()
    return round(time.perf_counter() - t, 1)
if os.environ['TABLEZERO_PERFORMER'] == 'llm': print(json.dumps({'warmup_s': warm(), 'model': os.environ['TABLEZERO_OLLAMA_MODEL']}), flush=True)
c = EpisodeController(provider=OllamaProvider()); s = InterviewService(c)
for e in ('V21-E02', 'V21-E07', 'V21-E13', 'V21-E14'): c.world.expose_evidence(e)
c.transition('desk'); c.transition('interview'); s.begin(sid)
out = []
for it in ITEMS:
    qid, q = it['id'], it['question']
    if qid in ('Q29', 'Q30'):
        out.append({'id': qid, 'suspect': sid, 'question': q, 'note': 'covered by tests/test_interview_stale (cancel) / save-load not implemented'}); continue
    t0 = time.perf_counter(); rec = {'id': qid, 'suspect': sid, 'group': it['group'], 'question': q}
    try:
        r = s.ask(q, input_mode='typed', action_id=uuid.uuid4().hex, presented_evidence=PRESENT.get(qid))
        rec.update(answer=r.suspect_text, tactic=(s.last_plan or {}).get('tactic'), parts=(s.last_plan or {}).get('parts'), topics=(s.last_plan or {}).get('topics'),
                   performer=r.performer, model=r.model, first_token_ms=r.first_token_ms, plan_ms=r.plan_ms, total_ms=round((time.perf_counter() - t0) * 1000), attempts=r.generation_attempts)
        a = r.suspect_text; chk = {}
        chk['stock_clarify_on_clear_question'] = bool(STOCK.search(a)) and qid not in ('Q21',)
        chk['leak_string'] = bool(LEAK.search(a))
        if qid in TIME_Q: chk['time_question_has_number_or_dont_recall'] = bool(re.search(r'\d|기억|모르|못 합니다|장담', a))
        if qid == 'Q09': chk['compound_parts_seen'] = (s.last_plan or {}).get('n_parts', 0) >= 3
        rec['auto'] = chk
    except GuardError as e:
        rec.update(error=str(e), total_ms=round((time.perf_counter() - t0) * 1000))
    out.append(rec); print(json.dumps(rec, ensure_ascii=False)); sys.stdout.flush()
