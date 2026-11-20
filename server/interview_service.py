"""Actual provider-backed interview turn service for CASE001.
The prompt may come from typed free text, mic transcription or suggested UI.
Typing speed, speech recognition latency and model latency are NOT penalized.
Only a successfully validated, committed spoken turn spends interview attention time.
This is an INTERVIEW SCENE time resource, NOT the global case action budget.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,threading
from .runtime import GuardError
from .tactics import TacticDirector,TAC_COST
from .dialogue_quality import clean_line,lint_line

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

class InterviewService:
    def __init__(self,episode, tactics=None):
        self.episode=episode
        self.tactics=tactics or TacticDirector()
        self._lock=threading.RLock()
        self._receipts:dict[str,TurnReceipt]={}
        self._fingerprints:dict[str,str]={}
    def begin(self,suspect_id):
        self.episode.start_interview(suspect_id)
        return self.tactics.begin(suspect_id)
    def close(self):
        self.episode.finish_interview()

    def ask(self,text,*,input_mode,action_id, presented_evidence=None,
            transcript_confirmed=True):
        with self._lock:
            return self._ask_locked(text,input_mode=input_mode,action_id=action_id,
                presented_evidence=presented_evidence,transcript_confirmed=transcript_confirmed)

    def _ask_locked(self,text,*,input_mode,action_id, presented_evidence=None,
            transcript_confirmed=True):
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
        ctx=self.episode.world.prompt_context(actor,text,presented_evidence)
        ctx['interview_approach']=self.tactics.context(actor)
        # Network / model errors, invalid outputs and invalid dialogue are uncharged
        provider_reply=self.episode.provider.run(ctx)
        reply=self.episode.world.validate_reply(actor,provider_reply['result'])
        recent=[x['utterance'] for x in self.episode.world.claims if x['suspect_id']==actor]
        issues=lint_line(reply['utterance'],recent,for_llm=True)
        if FAILURES.intersection(issues):raise GuardError('AI dialogue failed quality gate: '+','.join(issues))
        reply['utterance']=clean_line(reply['utterance'])
        result=self.tactics.perform(actor,tactic,action_id=action_id,approved=True)
        accepted=self.episode.world.accept_reply(actor,reply)
        receipt=TurnReceipt(action_id,actor,input_mode,text,accepted['utterance'],
                           TAC_COST[tactic],result['seconds_left'],
                           provider_reply['provider'],provider_reply['latency_ms'],
                           accepted['motion_proposal'],accepted['action_proposal'])
        self._receipts[action_id]=receipt;self._fingerprints[action_id]=fingerprint
        self.episode._log('interview_turn',{'actor':actor,'input_mode':input_mode,
             'seconds_spent':receipt.seconds_spent,'provider':receipt.provider,
             'latency_ms':receipt.latency_ms,'unverified_claim':True})
        return receipt
