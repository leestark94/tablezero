"""Opt-in AI adapters. Offline mode is explicitly SCRIPTED_PREVIEW, never called real AI.
Paid remote calls disabled unless explicit environment opt-in. No secrets in Unity.
"""
from __future__ import annotations
import json, os, re, urllib.request, urllib.error, time
from .runtime import MODES, ACTIONS, ALLOWED_MOTIONS

class ProviderError(RuntimeError): pass

REPLY_SCHEMA = {'type':'object','additionalProperties':False,
 'properties':{
 'utterance':{'type':'string','minLength':1,'maxLength':240},
 'reply_mode':{'type':'string','enum':sorted(MODES)},
 'motion_id':{'type':'string','enum':sorted(ALLOWED_MOTIONS)},
 'asserted_claim_ids':{'type':'array','items':{'type':'string'},'maxItems':6},
 'new_unsupported_assertion':{'type':['string','null']},
 'request_external_action':{'type':['string','null'],'enum':sorted(ACTIONS)+[None]},
 },'required':['utterance','reply_mode','motion_id','asserted_claim_ids','new_unsupported_assertion','request_external_action']}
SYSTEM_RULES='''너는 한국형 범죄수사게임 속 조사 대상 한 명이다
설정에 없는 것을 보았다고 단정하지 마라
상대에게 없는 증거를 먼저 언급하지 마라
진술은 진실일 수도, 거짓말일 수도, 사생활 방어일 수도 있다
다른 인물의 비밀이나 수사 정답을 알아맞히지 마라
일상 한국어로 짧게 말하라, 과잉 설명과 도덕적 훈계 금지
신분과 관계에 따라 존댓말을 사용하고 격앙되면 간혹 짧고 어색하게 끊어라
욕설은 맥락 있을 때 드물게 사용하라
문장 끝 마침표를 쓰지 마라
극적인 행동은 제안할 수 있지만 실행 권한은 서버에 있다
JSON 데이터만 반환하라
'''

class PreviewProvider:
    label='SCRIPTED_PREVIEW_NOT_AI'
    def reply(self, context):
        motions=context.get('approved_motions') or ['still']
        question=context['question']
        sid=context['character']['id']
        if '시간' in question or '몇 시' in question:
            utterance={'s1':'그때는 나왔다고 말씀드렸잖아요','s2':'몇 시부터 말씀하시는 거예요?','s3':'정확한 시간은 모르죠, 시계를 본 게 아니라서요'}.get(sid,'그건 다시 확인해 봐야겠네요')
        elif '통화' in question:
            utterance={'s1':'제가 왜 그 전화까지 알아야 되는데요','s2':'전화는 했어요, 그건 맞아요','s3':'통화는 못 들었어요'}.get(sid,'잘 모르겠는데요')
        else:
            utterance={'s1':'말씀드린 그대로예요','s2':'그 부분은 제가 확인하고 말씀드릴게요','s3':'제가 들은 것하고 직접 본 건 달라요'}.get(sid,'잘 모르겠습니다')
        return {'utterance':utterance,'reply_mode':'answer','motion_id':motions[0],
            'asserted_claim_ids':[], 'new_unsupported_assertion':None,'request_external_action':None}

def compact_schema_for(context):
    """Short-key schema for local models: ~25 fewer output tokens per turn on CPU.
    Converted back to the 6-key REPLY contract by from_compact()."""
    motions=sorted(context.get('approved_motions') or ALLOWED_MOTIONS)
    own=[c['id'] for c in context.get('own_starting_claims',[])]
    return {'type':'object','additionalProperties':False,
      'properties':{'line':{'type':'string','minLength':1,'maxLength':200},
        'mode':{'type':'string','enum':sorted(MODES)},
        'motion':{'type':'string','enum':motions},
        'claims':{'type':'array','items':({'type':'string','enum':own} if own else {'type':'string'}),'maxItems':4},
        'action':{'type':['string','null'],'enum':sorted(ACTIONS)+[None]}},
      'required':['line','mode','motion','claims','action']}

def from_compact(obj):
    if not isinstance(obj,dict) or 'line' not in obj:return obj
    return {'utterance':obj.get('line'),'reply_mode':obj.get('mode'),'motion_id':obj.get('motion'),
            'asserted_claim_ids':obj.get('claims') or [],'new_unsupported_assertion':None,
            'request_external_action':obj.get('action')}

def _schema_for(context):
    """Narrow the JSON schema to this suspect's own motions/claims so decoding cannot pick others."""
    schema=json.loads(json.dumps(REPLY_SCHEMA))
    motions=context.get('approved_motions')
    if motions:schema['properties']['motion_id']['enum']=sorted(motions)
    own=[c['id'] for c in context.get('own_starting_claims',[])]
    schema['properties']['asserted_claim_ids']['items']={'type':'string','enum':own} if own else {'type':'string'}
    return schema

class OllamaProvider:
    """Local, zero-API-cost provider (dev + candidate shipping path via bundled runtime).
    Uses server-built per-suspect messages (suspect_mind) when present."""
    label='OLLAMA_LOCAL'
    def __init__(self,model=None,url=None, timeout_s=None):
        self.model=model or os.environ.get('TABLEZERO_OLLAMA_MODEL','')
        if not self.model:raise ProviderError('Set TABLEZERO_OLLAMA_MODEL to an installed model')
        url=url or os.environ.get('TABLEZERO_OLLAMA_URL','http://127.0.0.1:11434/api/chat')
        if not url.startswith('http://127.0.0.1:') and not url.startswith('http://localhost:'):
            raise ProviderError('Ollama adapter restricted to localhost')
        self.url=url;self.timeout_s=timeout_s or float(os.environ.get('TABLEZERO_OLLAMA_TIMEOUT','90'))
        self.label=f'OLLAMA_LOCAL:{self.model}'
        self.temperature=float(os.environ.get('TABLEZERO_OLLAMA_TEMPERATURE','0.7'))
        self.last_stats={}
    supports_plain_line=True   # strategy engine decides mode/motion; the model only voices the line

    def _plain_line(self,context):
        payload={'model':self.model,'stream':False,'think':False,'keep_alive':'60m','messages':context['llm_messages'],
                 'options':{'temperature':context.get('temperature',self.temperature),'top_p':0.9,'repeat_penalty':1.15,
                            'num_predict':int(os.environ.get('TABLEZERO_LINE_TOKENS','56')),'num_ctx':2048,'stop':['\n\n','<|eot_id|>','<|im_end|>','<end_of_turn>']}}
        if context.get('seed') is not None:payload['options']['seed']=context['seed']
        if os.environ.get('TABLEZERO_OLLAMA_NUM_GPU') not in (None,''):
            payload['options']['num_gpu']=int(os.environ['TABLEZERO_OLLAMA_NUM_GPU'])
        if os.environ.get('TABLEZERO_OLLAMA_THREADS'):
            payload['options']['num_thread']=int(os.environ['TABLEZERO_OLLAMA_THREADS'])
        req=urllib.request.Request(self.url,data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout_s) as r:obj=json.loads(r.read(1_000_000).decode('utf-8'))
        except (ValueError,KeyError,urllib.error.URLError,TimeoutError,OSError) as e:
            raise ProviderError('Local model unavailable') from e
        self.last_stats={k:obj.get(k) for k in ('total_duration','load_duration','prompt_eval_count','prompt_eval_duration','eval_count','eval_duration')}
        line=(obj.get('message') or {}).get('content','').strip().strip('"').strip()
        line=line.split('\n')[0].strip()
        line=re.sub(r'<\|[^|>]*\|>|<end_of_turn>','',line).strip().strip('"“”').strip()
        if line.startswith('{'):
            try:line=json.loads(line).get('line','')
            except ValueError:pass
        return {'line':line}

    def reply(self,context):
        if context.get('plain_line'):return self._plain_line(context)
        messages=context.get('llm_messages') or [
            {'role':'system','content':SYSTEM_RULES},
            {'role':'user','content':json.dumps({k:v for k,v in context.items() if k!='llm_messages'},ensure_ascii=False)}]
        compact=bool(context.get('llm_messages'))
        payload={'model':self.model,'stream':False,'format':compact_schema_for(context) if compact else _schema_for(context),'think':False,
          'keep_alive':'30m','messages':messages,
          'options':{'temperature':context.get('temperature',self.temperature),'top_p':0.9,
                     'repeat_penalty':1.1,'num_predict':220,'num_ctx':8192,
                     'seed':context.get('seed')}}
        if payload['options']['seed'] is None:del payload['options']['seed']
        # GPU offload is opt-in per machine: the renderer owns VRAM during play, and on the dev PC
        # CUDA load triggers display-driver resets (see qa/bugs/BUG-0001). 0 = CPU-only inference.
        if os.environ.get('TABLEZERO_OLLAMA_NUM_GPU') not in (None,''):
            payload['options']['num_gpu']=int(os.environ['TABLEZERO_OLLAMA_NUM_GPU'])
        if os.environ.get('TABLEZERO_OLLAMA_THREADS'):
            payload['options']['num_thread']=int(os.environ['TABLEZERO_OLLAMA_THREADS'])
        data=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        request=urllib.request.Request(self.url,data=data,headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=self.timeout_s) as response:
                obj=json.loads(response.read(1_000_000).decode('utf-8'))
            self.last_stats={k:obj.get(k) for k in ('total_duration','load_duration','prompt_eval_count',
                             'prompt_eval_duration','eval_count','eval_duration')}
            out=json.loads(obj['message']['content'])
            return from_compact(out) if compact else out
        except (ValueError,KeyError,urllib.error.URLError,TimeoutError,OSError) as e:
            raise ProviderError('Local model unavailable or invalid output') from e

class ProviderGate:
    def __init__(self,provider=None):self.provider=provider or PreviewProvider()
    def run(self,context):
        start=time.perf_counter()
        result=self.provider.reply(context)
        return {'result':result,'provider':self.provider.label,
                'latency_ms':round((time.perf_counter()-start)*1000,1),
                'stats':getattr(self.provider,'last_stats',{})}

class OpenAIProvider:
    """Optional paid API via official JSON schema Chat Completions. NEVER enabled by default.
    Caller must explicitly opt in, configure model and key; don't put these in Unity.
    """
    label='PAID_REMOTE_AI_OPENAI'
    def __init__(self,model=None,timeout_s=30):
        if os.environ.get('TABLEZERO_ALLOW_PAID_API')!='I_APPROVE_PAID_API_CALLS':
            raise ProviderError('Explicit paid API opt-in missing')
        self.key=os.environ.get('OPENAI_API_KEY','')
        if not self.key:raise ProviderError('OPENAI_API_KEY missing on server')
        self.model=model or os.environ.get('TABLEZERO_OPENAI_MODEL','')
        if not self.model:raise ProviderError('Set TABLEZERO_OPENAI_MODEL to an available supported model')
        self.timeout_s=timeout_s
    def reply(self,context):
        payload={'model':self.model,
            'messages':[{'role':'system','content':SYSTEM_RULES},
                        {'role':'user','content':json.dumps(context,ensure_ascii=False)}],
            'response_format':{'type':'json_schema','json_schema':{
                'name':'tablezero_suspect_response','strict':True,'schema':REPLY_SCHEMA}}}
        data=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=data,
            headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout_s) as r:
                obj=json.loads(r.read(2_000_000).decode('utf-8'))
            message=obj['choices'][0]['message']
            if message.get('refusal'):raise ProviderError('Model refused')
            if not message.get('content'):raise ProviderError('Empty model content')
            return json.loads(message['content'])
        except (KeyError,IndexError,ValueError,urllib.error.URLError,TimeoutError) as e:
            raise ProviderError('Paid API call failed or response not schema-compliant') from e

def choose_provider_from_env():
    selected=os.environ.get('TABLEZERO_AI_PROVIDER','preview').lower()
    if selected=='preview':return PreviewProvider()
    if selected=='ollama':return OllamaProvider()
    if selected=='openai':return OpenAIProvider()
    raise ProviderError('Provider must be preview, ollama, or openai')
