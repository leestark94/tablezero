"""Background local-LLM load for frame-time tests: runs the same model/config the dev server uses (qwen3:4b, CPU,
num_thread = cores/2) in a loop for N seconds and reports per-request latency.
  python tools/ai_load.py 60 > qa/logs/perf/ai_load.txt"""
import json, os, sys, time, urllib.request

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60
model = os.environ.get('TABLEZERO_OLLAMA_MODEL', 'qwen3:4b')
threads = max(2, (os.cpu_count() or 8) // 2)
prompt = '형사의 질문에 짧게 대답하는 용의자처럼, 한국어 한 문장으로: 그날 밤 어디에 있었습니까?'
t0 = time.time(); lat = []
while time.time() - t0 < secs:
    body = json.dumps({'model': model, 'prompt': prompt, 'stream': False, 'think': False,
                       'options': {'num_gpu': 0, 'num_thread': threads, 'num_predict': 60}}).encode()
    s = time.time()
    req = urllib.request.Request('http://127.0.0.1:11434/api/generate', body, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        out = json.loads(r.read())
    lat.append(time.time() - s)
    print(f'req {len(lat)} {lat[-1]:.1f}s eval_tokens={out.get("eval_count")} tok_s={out.get("eval_count", 0) / max(1e-6, out.get("eval_duration", 1) / 1e9):.1f}', flush=True)
print(f'SUMMARY requests={len(lat)} avg_latency_s={sum(lat) / max(1, len(lat)):.1f} threads={threads} model={model}')
