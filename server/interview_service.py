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
 'default':'[다시] 규칙에 맞게 짧고 자연스러운 한국어로 다시 대답한다',
}

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

class InterviewService:
    max_attempts=3
    def __init__(self,episode, tactics=None):
        self._strategy={}; self.last_plan=None
        self.episode=episode
        self.tactics=tactics or TacticDirector()
        self._lock=threading.RLock()
        self._receipts:dict[str,TurnReceipt]={}
        self._fingerprints:dict[str,str]={}
    def begin(self,suspect_id):
        self.episode.start_interview(suspect_id)
        return self.tactics.begin(suspect_id)
    def close(self):
        actor=self.episode.state.interview_active
        self.episode.finish_interview()
        try:self.tactics.state(actor).active=False
        except GuardError:pass
        return self.episode.autonomy_after_interview(actor) if actor else None

    def ask(self,text,*,input_mode,action_id, presented_evidence=None,
            transcript_confirmed=True, on_partial=None):
        with self._lock:
            return self._ask_locked(text,input_mode=input_mode,action_id=action_id,
                presented_evidence=presented_evidence,transcript_confirmed=transcript_confirmed,on_partial=on_partial)

    def _ask_locked(self,text,*,input_mode,action_id, presented_evidence=None,
            transcript_confirmed=True, on_partial=None):
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
        strategic=getattr(getattr(self.episode.provider,'provider',None),'supports_plain_line',False) and 'dossier' in personas()['suspects'].get(actor,{})
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
        plan=None
        if strategic:
            st=self._strategy.setdefault(actor,SuspectState())
            ev_by_id={e['id']:e for e in world._canon['evidence']}
            plan=plan_turn(personas(),actor,st,text,presented_now,presented_evidence,ev_by_id,bool(tac['pressured']))
            motions=sorted(set(world.suspects[actor].get('possible_motions',[]))&world.motions)
            ctx['llm_messages']=speaker_messages(personas(),actor,plan,text,ev_by_id.get(presented_evidence) if presented_evidence else None,motions,recent)
            ctx['plain_line']=True
            memories=list(memories)+plan['allowed']   # what the plan allows may be voiced (gated-term check)
            self.last_plan={k:plan[k] for k in ('tactic','mode','relevant','accused','bluff')}
        base_messages=list(ctx['llm_messages'])
        if on_partial and plan is not None:
            gate=dict(blocked=False)
            def forward(t):
                # a partial is shown only while it passes the same leak/confession/concealment checks as a final line
                if gate['blocked']:return
                if len(t.strip())<4:return   # too short to judge yet; wait for more tokens
                # length/echo checks are only meaningful for a finished line; partials are screened for leaks only
                probs=set(guard_utterance(actor,t,presented=presented_now,detective_text=detective_text,memories=memories,question=text,recent=[],mode=plan['mode']))
                if probs-{'empty_or_non_korean_line','echoed_question','near_repeat'}:
                    gate['blocked']=True;on_partial('');return
                on_partial(t)
            ctx['on_partial']=forward
        # Authored in-voice line for this exact situation: instant, no model call. Same guards as a generated line.
        if plan is not None and not os.environ.get('TABLEZERO_NO_LINE_BANK'):
            banked=line_bank.pick(actor,plan,text,st.bank_used)
            if banked:
                try:
                    motions=sorted(set(world.suspects[actor].get('possible_motions',[]))&world.motions)
                    cand=world.validate_reply(actor,{'utterance':banked,'reply_mode':plan['mode'],'motion_id':pick_motion(plan['tactic'],motions),
                        'asserted_claim_ids':[],'new_unsupported_assertion':None,
                        'request_external_action':'request_counsel' if plan['tactic']=='STONEWALL' and plan['mode']=='request_counsel' else None})
                    bad=guard_utterance(actor,cand['utterance'],presented=presented_now,detective_text=detective_text,memories=memories,
                                        question=text,recent=[],mode=cand['reply_mode'])
                    bad=[b for b in bad if b not in ('near_repeat','echoed_question')]
                    if not bad:
                        cand['utterance']=clean_line(cand['utterance']);reply=cand
                        provider_reply={'provider':'LINE_BANK','latency_ms':0.0,'result':{}}
                        if on_partial:on_partial(cand['utterance'])
                    else:attempts.append('bank:'+','.join(bad))
                except (GuardError,KoreanDialogueError) as e:
                    attempts.append('bank:'+str(e))
        for attempt in range(self.max_attempts if reply is None else 0):
            if on_partial and plan is not None:
                gate['blocked']=False;on_partial('')
            if attempts and attempts[-1] not in ('provider_error',):
                # Bounded server-side redo with the reason; never shown to the player, never charged
                ctx['llm_messages']=base_messages+[{'role':'system','content':RETRY_HINTS.get(attempts[-1].split(',')[0],RETRY_HINTS['default'])}]
            ctx['temperature']=0.7+0.1*attempt
            if os.environ.get('TABLEZERO_EVAL_SEED'):
                ctx['seed']=int(os.environ['TABLEZERO_EVAL_SEED'])+attempt
            try:
                provider_reply=self.episode.provider.run(ctx)
            except ProviderError as e:
                attempts.append('provider_error');continue
            total_ms+=provider_reply['latency_ms']
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
                if blocking:
                    attempts.append(','.join(blocking));continue
                candidate['utterance']=clean_line(candidate['utterance'])
                reply=candidate;break
            except (GuardError,KoreanDialogueError) as e:
                attempts.append(str(e));continue
        self.episode._log('interview_generation',{'actor':actor,'attempts':len(attempts)+(1 if reply else 0),
                          'rejections':attempts,'latency_ms_total':round(total_ms,1)})
        if reply is None and plan is not None:
            from .strategy import fallback_line
            motions=sorted(set(world.suspects[actor].get('possible_motions',[]))&world.motions)
            reply=world.validate_reply(actor,{'utterance':fallback_line(plan),'reply_mode':plan['mode'],'motion_id':pick_motion(plan['tactic'],motions),
                                             'asserted_claim_ids':[],'new_unsupported_assertion':None,'request_external_action':None})
            attempts.append('fallback_line')
        if reply is None:
            raise GuardError('AI response rejected by server gates (no time charged): '+' | '.join(attempts[-3:]))
        result=self.tactics.perform(actor,tactic,action_id=action_id,approved=True)
        accepted=world.accept_reply(actor,reply)
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
                           reply_mode=accepted['reply_mode'],generation_attempts=len(attempts)+1)
        self._receipts[action_id]=receipt;self._fingerprints[action_id]=fingerprint
        self.episode._log('interview_turn',{'actor':actor,'input_mode':input_mode,
             'seconds_spent':receipt.seconds_spent,'provider':receipt.provider,
             'latency_ms':receipt.latency_ms,'unverified_claim':True})
        return receipt
