"""Live interrogation probe with the real local model (no Unity). Prints the strategy chosen, the spoken line and latency.
  python -I tools/live_interrogation_probe.py <model> [num_gpu] [suspect] > qa/logs/ai/probe_<model>.txt
Turns: (question, evidence presented with that question or None). Evidence is first acquired server-side."""
import os, sys, time, uuid, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
model = sys.argv[1] if len(sys.argv) > 1 else 'qwen3:4b'
os.environ['TABLEZERO_OLLAMA_MODEL'] = model
if len(sys.argv) > 2 and sys.argv[2] != '-': os.environ['TABLEZERO_OLLAMA_NUM_GPU'] = sys.argv[2]
sid = sys.argv[3] if len(sys.argv) > 3 else 's2'
from server.providers import OllamaProvider
from server.episode_controller import EpisodeController
from server.interview_service import InterviewService
from server.runtime import GuardError

SCRIPTS = {
 's2': [('피해자와 무슨 사이였습니까', None), ('너 범인이지?ㅋ', None), ('그날 밤 아홉 시 반쯤 어디 계셨어요?', None),
        ('증거 다 있어. 빨리 말해', None), ('이 화면 보세요. 이거 당신이죠?', 'V21-E02'),
        ('편의점 결제 기록도 있습니다', 'V21-E14'), ('그럼 그날 그 집에 갔던 거 맞죠?', None),
        ('수연 씨 머리를 다치게 했습니까?', None), ('정산 문제는 뭐였어요?', None), ('480만원 이체 기록입니다', 'V21-E11')],
 's3': [('신고하신 분이죠. 그날 상황 말씀해 주세요', None), ('당신이 죽였지?', None), ('302호 안에 들어간 적 있어요?', None),
        ('강도현 씨가 보낸 메시지 기록입니다', 'V21-E12'), ('정수연 씨랑 만나기로 했었죠?', 'V21-E18'),
        ('이 서류 조각, 당신 집에서 나왔습니다', 'V21-E16'), ('302호에 들어갔죠?', None)],
 's1': [('피해자와 어떤 사이였습니까', None), ('니가 죽였지?', None), ('21시 21분 이후에는 어디 갔어요?', None),
        ('피해자 왼팔에 멍이 있었습니다', 'V21-E05'), ('휴대전화도 깨져 있었고요', 'V21-E06'), ('바로 출근했다는 거 맞아요?', 'V21-E13')],
}

c = EpisodeController(provider=OllamaProvider()); s = InterviewService(c)
for q, ev in SCRIPTS[sid]:
    if ev: c.world.expose_evidence(ev)
c.transition('desk'); c.transition('interview'); s.begin(sid)
total = []
print(f'MODEL {model} num_gpu={os.environ.get("TABLEZERO_OLLAMA_NUM_GPU","default")} suspect={sid}')
for q, ev in SCRIPTS[sid]:
    t = time.time()
    try:
        r = s.ask(q, input_mode='typed', action_id=uuid.uuid4().hex, presented_evidence=ev)
        dt = time.time() - t; total.append(dt)
        print(f'형사: {q}' + (f'  [제시 {ev}]' if ev else ''))
        print(f'  -> [{(s.last_plan or {}).get("tactic")}/{r.reply_mode}] {r.suspect_text}   ({dt:.2f}s, 시도 {r.generation_attempts})')
    except GuardError as e:
        print(f'형사: {q}\n  -> 실패(차감 없음): {e}  ({time.time()-t:.2f}s)')
    sys.stdout.flush()
if total:
    print(f'SUMMARY avg {sum(total)/len(total):.2f}s  max {max(total):.2f}s  turns {len(total)}')
