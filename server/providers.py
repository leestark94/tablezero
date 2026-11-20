"""Opt-in AI adapters. Offline mode is explicitly SCRIPTED_PREVIEW, never called real AI.
Paid remote calls disabled unless explicit environment opt-in. No secrets in Unity.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error, time
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

class OllamaProvider:
    label='OLLAMA_LOCAL'
    def __init__(self,model=None,url='http://127.0.0.1:11434/api/chat', timeout_s=25):
        self.model=model or os.environ.get('TABLEZERO_OLLAMA_MODEL','')
        if not self.model:raise ProviderError('Set TABLEZERO_OLLAMA_MODEL to an installed model')
        if not url.startswith('http://127.0.0.1:') and not url.startswith('http://localhost:'):
            raise ProviderError('Ollama adapter restricted to localhost')
        self.url=url;self.timeout_s=timeout_s
    def reply(self,context):
        payload={'model':self.model,'stream':False,'format':REPLY_SCHEMA,
          'messages':[{'role':'system','content':SYSTEM_RULES},
                      {'role':'user','content':json.dumps(context,ensure_ascii=False)}],
          'options':{'temperature':0.6,'num_predict':320}}
        data=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        request=urllib.request.Request(self.url,data=data,headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=self.timeout_s) as response:
                obj=json.loads(response.read(1_000_000).decode('utf-8'))
                return json.loads(obj['message']['content'])
        except (ValueError,KeyError,urllib.error.URLError,TimeoutError) as e:
            raise ProviderError('Local model unavailable or invalid output') from e

class ProviderGate:
    def __init__(self,provider=None):self.provider=provider or PreviewProvider()
    def run(self,context):
        start=time.perf_counter()
        result=self.provider.reply(context)
        return {'result':result,'provider':self.provider.label,
                'latency_ms':round((time.perf_counter()-start)*1000,1)}

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
