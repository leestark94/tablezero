"""Actual provider-backed interview turn service for CASE001.
The prompt may come from typed free text, mic transcription or suggested UI.
Typing speed, speech recognition latency and model latency are NOT penalized.
Only a successfully validated, committed spoken turn spends interview attention time.
This is an INTERVIEW SCENE time resource, NOT the global case action budget.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,threading,json,os
from .runtime import GuardError
from .tactics import TacticDirector,TAC_COST
from .dialogue_quality import clean_line,lint_line,KoreanDialogueError
from .providers import ProviderError
from .suspect_mind import build_messages,render_question,guard_utterance,active_memories,personas
from .strategy import SuspectState,plan_turn,speaker_messages,pick_motion
from . import line_bank
from . import interview_planner as IP
import time as _time, re as _re

RETRY_HINTS={
 'volunteered_concealed_detail':'[다시] 방금 대답은 형사가 묻지도 보여주지도 않은 구체적인 내용을 먼저 말했다. 지금 말할 수 있는 기억과 경찰에게 하기로 한 말 안에서만 다시 대답한다',
 'unearned_confession':'[다시] 너는 지금 그 일을 인정할 생각이 없다. 짧게 부인하거나 말을 아끼는 대답으로 다시 한다',
 'false_confession_innocent':'[다시] 너는 그런 일을 하지 않았다. 억울함이나 당황을 담아 다시 대답한다',
 'repeated_line':'[다시] 직전과 같은 말이다. 다른 표현으로, 질문에 맞게 다시 대답한다',
 'near_repeat':'[다시] 앞에서 한 말을 거의 그대로 반복했다. 이번 질문에만 새로 답하고, 시간이나 같은 문장을 되풀이하지 않는다',
 'echoed_question':'[다시] 형사의 말을 따라 했다. 네 입장에서 대답한다',
 'empty_or_non_korean_line':'[다시] 대사가 비었다. 한국어로 짧게 대답한다. 말하기 싫으면 "…" 대신 짧게 거절한다',
 'meta_ai_reference':'[다시] 너는 실제 사람이다. 사람으로서 다시 대답한다',
 'stage_direction_in_line':'[다시] 괄호나 행동 묘사 없이 입으로 하는 말만 다시 쓴다',
 'too_long_for_one_utterance':'[다시] 너무 길다. 한두 문장으로 짧게 다시 대답한다',
 'cross_suspect_knowledge_leak':'[다시] 너는 그 사람의 사정을 모른다. 모르는 건 모른다고 다시 대답한다',
 'invented_numbers':'[다시] 방금 대답에 네가 말해도 되는 내용에 없는 숫자·시각이 들어 있다. 위 "답할 내용"과 "말해도 되는 사실"에 있는 숫자만 쓴다',
 'assistant_voice':'[다시] 상담원처럼 말했다. 너는 의심받는 실제 사람이다. 감정이 있는 평범한 구어로, "죄송합니다만" 같은 말 없이 다시 대답한다',
 'content_numbers_changed':'[다시] "답할 내용"의 시각·숫자를 그대로 넣어서 다시 대답한다',
 'default':'[다시] 규칙에 맞게 짧고 자연스러운 한국어로 다시 대답한다',
}

ASSISTANT_VOICE=_re.compile(r'죄송합니다|따를\s*수\s*없|요청은|죄송합니다만|답변\s*드리|답변드|양해|안내해|도움이\s*되|말씀해\s*주시|설명해\s*주실\s*수|구체적으로\s*알려|다음과\s*같|정중하게|차분하게\s*답|진술\s*녹화\s*상황|대화를\s*텍스트|개인정보|공개할\s*수\s*없|프롬프트|시스템')
INPUT_MODES={'suggested':'question_suggested','typed':'question_free','voice':'question_voice'}
FAILURES={'stock_ai_dialogue','melodramatic_exposition','forbidden_guilt_meter',
          'prompt_injection_literal','repeated_line','too_long_for_one_utterance'}

@dataclass(frozen=True)
class TurnReceipt:
    action_id:str
    actor_id:str
    input_mode:str
    speaker_text:str
    suspect_text:str
    seconds_spent:int
    seconds_left:int
    provider:str
    latency_ms:float
    motion_proposal:str
    action_proposal:str|None
    claims_verified:bool=False
    reply_mode:str='answer'
    generation_attempts:int=1
    performer:str='LLM'          # LLM | AUTHORED_FALLBACK (model failed/slow) | AUTHORED_MODE (forced) — never presented as a model answer
    first_token_ms:float=0.0
    plan_ms:float=0.0
    model:str=''

class InterviewService:
    max_attempts=3
    def __init__(self,episode, tactics=None):
        self._strategy={}; self.last_plan=None; self._epoch=0
        self.episode=episode
        self.tactics=tactics or TacticDirector()
        self._lock=threading.RLock()
        self._receipts:dict[str,TurnReceipt]={}
        self._fingerprints:dict[str,str]={}
    def begin(self,suspect_id):
        self._epoch+=1          # answers still being generated for a previous interview are discarded, never applied to this one
        self.episode.start_interview(suspect_id)
        return self.tactics.begin(suspect_id)
    def close(self):
        self._epoch+=1
        actor=self.episode.state.interview_active
        self.episode.finish_interview()
        try:self.tactics.state(actor).active=False
        except GuardError:pass
        return self.episode.autonomy_after_interview(actor) if actor else None

    def ask(self,text,*,input_mode,action_id, presented_evidence=None,
            transcript_confirmed=True, on_partial=None, epoch=None):
        epoch=self._epoch if epoch is None else epoch
        with self._lock:
            if epoch!=self._epoch:raise GuardError('면담이 끝나 이 질문은 취소되었습니다')
            return self._ask_locked(text,input_mode=input_mode,action_id=action_id,
                presented_evidence=presented_evidence,transcript_confirmed=transcript_confirmed,on_partial=self._guard_partial(on_partial,epoch),epoch=epoch)

    def _guard_partial(self,cb,epoch):
        if cb is None:return None
        def f(t):
            if epoch==self._epoch:cb(t)      # a stale generation never writes to the screen
        return f

    def _ask_locked(self,text,*,input_mode,action_id, presented_evidence=None,
            transcript_confirmed=True, on_partial=None, epoch=0):
        t_plan0=_time.perf_counter()
        if not isinstance(action_id,str) or len(action_id)<12 or len(action_id)>100:
            raise GuardError('Invalid idempotency key')
        if input_mode not in INPUT_MODES:raise GuardError('Unsupported question source')
        if input_mode=='voice' and not transcript_confirmed:
            raise GuardError('Voice transcript must be confirmed before use or charge')
        actor=self.episode.state.interview_active
        if not actor or self.episode.state.scene!='interview':raise GuardError('No active interview')
        # Hash inputs before idempotency handling so network retry cannot change its meaning
        text=clean_line(text,max_chars=500)
        fingerprint=hashlib.sha256(f'{actor}|{input_mode}|{text}|{presented_evidence}'.encode()).hexdigest()
        if action_id in self._receipts:
            if self._fingerprints[action_id]!=fingerprint:raise GuardError('Duplicate ID used for different turn')
            return self._receipts[action_id]
        self.tactics.assert_can_question(actor)
        tactic=INPUT_MODES[input_mode]
        if self.tactics.state(actor).seconds_left<TAC_COST[tactic]:
            raise GuardError('Not enough interview time')
        if presented_evidence is not None and presented_evidence not in self.episode.world.available_evidence:
            raise GuardError('Evidence not acquired')
        world=self.episode.world
        presented_before=set(world.presented_to[actor])
        presented_now=presented_before|({presented_evidence} if presented_evidence else set())
        ctx=world.prompt_context(actor,text,presented_evidence)
        strategic=(getattr(getattr(self.episode.provider,'provider',None),'supports_plain_line',False) or os.environ.get('TABLEZERO_PERFORMER','').lower()=='authored') and 'dossier' in personas()['suspects'].get(actor,{})
        tac=self.tactics.context(actor)
        ctx['interview_approach']=tac
        climate={'pressured':tac['pressured'],
                 'trust_turns':sum(1 for t in world.transcripts[actor] if not t.get('pressured'))}
        known=[{'summary':e.payload.get('summary_for_'+actor) or e.payload.get('summary','')}
               for e in world.events if actor in e.visible_to and (e.payload.get('summary_for_'+actor) or e.payload.get('summary'))]
        ctx['llm_messages']=build_messages(world,actor,text,presented=presented_now,
            newly_presented=presented_evidence if presented_evidence not in presented_before else None,
            climate=climate,known_events=known,transcript=world.transcripts[actor])
        # Network / model errors, invalid outputs and invalid dialogue are uncharged.
        # Server retries a bounded number of times; the player never pays for a bad generation.
        recent=[x['utterance'] for x in world.claims if x['suspect_id']==actor]
        detective_text=' '.join([t['q_render'] for t in world.transcripts[actor]]+[text])
        memories=active_memories(actor,presented_now,climate)
        attempts=[];provider_reply=None;reply=None;total_ms=0.0
        plan=None; performer='LLM'; first_token_ms=0.0; plan_ms=0.0; model_label=''
        if strategic:
            st=self._strategy.setdefault(actor,IP.SuspectMemory())
            ev_by_id={e['id']:e for e in world._canon['evidence']}
            plan=IP.plan_turn(personas(),actor,st,text,presented_now,presented_evidence,ev_by_id,bool(tac['pressured']))
            plan_ms=(_time.perf_counter()-t_plan0)*1000
            motions=sorted(set(world.suspects[actor].get('possible_motions',[]))&world.motions)
            from .strategy import habit_hint
            hist=[h['a'] for h in st.history]
            ctx['llm_messages']=IP.performer_messages(personas(),actor,plan,text,ev_by_id.get(presented_evidence) if presented_evidence else None,st,habit_hint(personas()['suspects'][actor].get('verbal_habits',[]),hist))
            ctx['plain_line']=True
            memories=list(memories)+plan['allowed']   # what the plan allows may be voiced (gated-term check)
            self.last_plan={k:plan[k] for k in ('tactic','mode','relevant','accused','bluff')}
            self.last_plan['parts']=[{k:po[k] for k in ('text','ask','fact','kind')} for po in plan['parts']]
            self.last_plan['topics']=plan['frame'].topics;self.last_plan['n_parts']=len(plan['frame'].parts)
        base_messages=list(ctx['llm_messages'])
        provider_label=getattr(self.episode.provider.provider,'label','?') if strategic else ''
        gate=dict(blocked=False)
        if on_partial and plan is not None:
            def forward(t):
                # a partial is shown only while it passes the same leak/confession/concealment checks as a final line
                if gate['blocked']:return
                if len(t.strip())<4:return   # too short to judge yet; wait for more tokens
                probs=set(guard_utterance(actor,t,presented=presented_now,detective_text=detective_text,memories=memories,question=text,recent=[],mode=plan['mode']))
                if probs-{'empty_or_non_korean_line','echoed_question','near_repeat'}:
                    gate['blocked']=True;on_partial('');return
                on_partial(t)
            ctx['on_partial']=forward
        mode_env=os.environ.get('TABLEZERO_PERFORMER','llm').lower()
        t_gen0=_time.perf_counter()
        first=[None]
        if 'on_partial' in ctx:
            inner=ctx['on_partial']
            def timed(t):
                if first[0] is None and t.strip():first[0]=_time.perf_counter()
                inner(t)
            ctx['on_partial']=timed
        elif plan is not None:
            def timed2(t):
                if first[0] is None and t.strip():first[0]=_time.perf_counter()
            ctx['on_partial']=timed2
        ctx['first_token_s']=float(os.environ.get('TABLEZERO_FIRST_TOKEN_S','4'))
        n_attempts=0 if (plan is not None and mode_env=='authored') else self.max_attempts
        for attempt in range(n_attempts):
            if on_partial and plan is not None:
                gate['blocked']=False;on_partial('')
            if attempts and attempts[-1] not in ('provider_error',):
                ctx['llm_messages']=base_messages+[{'role':'system','content':RETRY_HINTS.get(attempts[-1].split(',')[0],RETRY_HINTS['default'])}]
            ctx['temperature']=0.6+0.1*attempt
            if os.environ.get('TABLEZERO_EVAL_SEED'):
                ctx['seed']=int(os.environ['TABLEZERO_EVAL_SEED'])+attempt
            try:
                provider_reply=self.episode.provider.run(ctx)
            except ProviderError as e:
                attempts.append('provider_error')
                if plan is not None:break        # model unreachable/too slow: do not wait through more attempts, answer from the plan
                continue
            total_ms+=provider_reply['latency_ms']
            if epoch!=self._epoch:raise GuardError('면담이 끝나 이 답변은 폐기되었습니다')
            try:
                result=provider_reply['result']
                if plan is not None:
                    motions=sorted(set(world.suspects[actor].get('possible_motions',[]))&world.motions)
                    result={'utterance':result.get('line',''),'reply_mode':plan['mode'],'motion_id':pick_motion(plan['tactic'],motions),
                            'asserted_claim_ids':[],'new_unsupported_assertion':None,
                            'request_external_action':'request_counsel' if plan['tactic']=='STONEWALL' and plan['mode']=='request_counsel' else None}
                candidate=world.validate_reply(actor,result)
                issues=lint_line(candidate['utterance'],recent,for_llm=True)
                if candidate['reply_mode']=='silence' and len(candidate['utterance'].strip())<2:
                    candidate['utterance']='…'
                blocking=sorted(FAILURES.intersection(issues))+guard_utterance(actor,candidate['utterance'],
                    presented=presented_now,detective_text=detective_text,memories=memories,
                    question=text,recent=recent,mode=candidate['reply_mode'])
                if plan is not None:
                    # a model may not invent facts: every number in its line must come from the allowed content, the question or the shown evidence
                    src=' '.join(plan['allowed'])+' '+text+' '+(json.dumps(ev_by_id.get(presented_evidence) or {},ensure_ascii=False) if presented_evidence else '')+' '+' '.join(h['a'] for h in st.history[-4:])
                    ok_nums=set(_re.findall(r'\d+',src))
                    bad_nums=[n for n in _re.findall(r'\d+',candidate['utterance']) if n not in ok_nums]
                    if bad_nums:blocking=list(blocking)+['invented_numbers']
                    if ASSISTANT_VOICE.search(candidate['utterance']):blocking=list(blocking)+['assistant_voice']
                    if len(candidate['utterance'])>260:blocking=list(blocking)+['too_long_for_one_utterance']
                    # fidelity: every number/time the plan put in the allowed content must survive into the spoken line
                    need=set(_re.findall(r'\d+',' '.join(po['line'] for po in plan['parts'] if po.get('line'))))
                    if need and not need.issubset(set(_re.findall(r'\d+',candidate['utterance']))) and plan['tactic'] not in ('STONEWALL','REBUKE','OFFTOPIC'):
                        blocking=list(blocking)+['content_numbers_changed']
                if blocking:
                    attempts.append(','.join(blocking));continue
                candidate['utterance']=clean_line(candidate['utterance'])
                reply=candidate;break
            except (GuardError,KoreanDialogueError) as e:
                attempts.append(str(e));continue
        if first[0] is not None:first_token_ms=(first[0]-t_gen0)*1000
        model_label=provider_label
        self.episode._log('interview_generation',{'actor':actor,'attempts':len(attempts)+(1 if reply else 0),
                          'rejections':attempts,'latency_ms_total':round(total_ms,1),'first_token_ms':round(first_token_ms,1),
                          'plan_ms':round(plan_ms,2),'performer_mode':mode_env,'model':provider_label})
        if reply is None and plan is not None:
            # Honest fallback: the answer is composed from the plan's own authored lines (every question part answered) and is labelled
            from .strategy import fallback_line
            motions=sorted(set(world.suspects[actor].get('possible_motions',[]))&world.motions)
            line=IP.authored_line(plan)
            if not plan['parts'] and not plan['this_turn']:
                line=line_bank.pick(actor,plan,text,st.bank_used) or fallback_line(plan)
            reply=world.validate_reply(actor,{'utterance':clean_line(line),'reply_mode':plan['mode'],'motion_id':pick_motion(plan['tactic'],motions),
                                             'asserted_claim_ids':[],'new_unsupported_assertion':None,
                                             'request_external_action':'request_counsel' if plan['tactic']=='STONEWALL' and plan['mode']=='request_counsel' else None})
            if on_partial:on_partial(reply['utterance'])
            performer='AUTHORED_MODE' if mode_env=='authored' else 'AUTHORED_FALLBACK'
            provider_reply={'provider':'AUTHORED_LINES','latency_ms':0.0,'result':{}}
            attempts.append(performer.lower())
        if reply is None:
            raise GuardError('AI response rejected by server gates (no time charged): '+' | '.join(attempts[-3:]))
        if epoch!=self._epoch:raise GuardError('면담이 끝나 이 답변은 폐기되었습니다')
        result=self.tactics.perform(actor,tactic,action_id=action_id,approved=True)
        accepted=world.accept_reply(actor,reply)
        if plan is not None:
            st.history.append({'q':text[:120],'a':reply['utterance'][:160],'tactic':plan['tactic']})
            if presented_evidence:st.shown.add(presented_evidence)
        if presented_evidence:world.presented_to[actor].add(presented_evidence)
        world.transcripts[actor].append({
            'q_render':render_question(world,text,presented_evidence if presented_evidence not in presented_before else None),
            'a_json':json.dumps({'line':reply['utterance'],'mode':reply['reply_mode'],'motion':reply['motion_id'],
                                 'claims':reply['asserted_claim_ids'],'action':reply['request_external_action']},ensure_ascii=False),
            'a_text':reply['utterance'],'pressured':tac['pressured'],'evidence':presented_evidence})
        if reply['request_external_action']:
            self.episode.state.pending_proposals.append({'actor':actor,'kind':reply['request_external_action']})
        receipt=TurnReceipt(action_id,actor,input_mode,text,accepted['utterance'],
                           TAC_COST[tactic],result['seconds_left'],
                           provider_reply['provider'],round(total_ms,1),
                           accepted['motion_proposal'],accepted['action_proposal'],
                           reply_mode=accepted['reply_mode'],generation_attempts=len(attempts)+1,
                           performer=performer,first_token_ms=round(first_token_ms,1),plan_ms=round(plan_ms,2),model=model_label)
        self._receipts[action_id]=receipt;self._fingerprints[action_id]=fingerprint
        self.episode._log('interview_turn',{'actor':actor,'input_mode':input_mode,
             'seconds_spent':receipt.seconds_spent,'provider':receipt.provider,
             'latency_ms':receipt.latency_ms,'unverified_claim':True})
        return receipt
