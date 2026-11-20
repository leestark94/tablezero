"""Deterministic CASE 001 interrogation tactics.

No model may change this state. A tense reaction never proves guilt. Player intimidation
has tangible procedural consequences; it is not a shortcut to a confession.
Server methods are demonstrations; production must supply verified actor/scene authority.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
from .runtime import GuardError

TAC_COST = {
 'question_calm': 25, 'target_discrepancy': 45, 'present_evidence': 35,
 'question_suggested': 14, 'question_free': 24, 'question_voice': 24,
 'wait_in_silence': 30, 'raise_voice': 50, 'strike_table': 85,
 'offer_pause': 80, 'review_record': 55, 'end_interview': 0,
}
ACTOR_RESPONSES = {
 's1': {
    'raise_voice': ['목소리 좀 낮추세요, 제가 무슨 죄인입니까', '아니, 지금 저한테 왜 이러세요'],
    'strike_table': ['뭐 하시는 겁니까 지금', '아니, 지금 뭐 하시는 거냐고요'],
    'wait_in_silence': ['뭐라도 말씀을 하시죠', '그냥 이렇게 앉아 있으면 됩니까'],
 },
 's2': {
    'raise_voice': ['말씀은 알아들었어요, 소리 안 지르셔도 돼요', '그 얘긴 아까도 했잖아요'],
    'strike_table': ['이런 식으로 하시면 저도 더 말씀 못 드리겠어요', '저한테 화내실 건 아니잖아요'],
    'wait_in_silence': ['더 물으실 거 없으세요?', '그렇게 보셔도 달라지는 건 없는데요'],
 },
 's3': {
    'raise_voice': ['저 지금 겁주시는 겁니까', '아, 제가 한 건 신고밖에 없다니까요'],
    'strike_table': ['아니 왜 갑자기 책상을 쳐요', '저 이렇게는 조사 못 받겠어요'],
    'wait_in_silence': ['제가 기억나는 만큼 다 말씀드렸습니다', '집에 가봐도 돼요?'],
 }
}
@dataclass
class InterviewTacticState:
 actor_id:str
 seconds_left:int=900
 tactic_history:list[str]=field(default_factory=list)
 credibility_damage:int=0
 hostility:int=0
 contact_discomfort:int=0
 counsel_requested:bool=False
 active:bool=True
 recorded_coercive_episodes:int=0
 pressured_statement_ids:list[int]=field(default_factory=list)
 last_action_id:str=''

class TacticDirector:
 def __init__(self):
  self._states:dict[str,InterviewTacticState]={}
  self._action_ids:dict[str,dict]={}

 def begin(self,actor_id):
  if actor_id not in {'s1','s2','s3'}:raise GuardError('Unknown CASE001 actor')
  state=InterviewTacticState(actor_id)
  self._states[actor_id]=state
  return self.public_state(actor_id)

 def state(self, actor_id):
  s=self._states.get(actor_id)
  if not s or not s.active:raise GuardError('No active interrogation tactics session')
  return s

 def assert_can_question(self,actor_id):
  s=self.state(actor_id)
  if s.counsel_requested or s.seconds_left<=0:raise GuardError('Interview suspended or time exhausted')

 def perform(self,actor_id,tactic,*,action_id,approved=False,performance_ready=False,
             evidence_id=None, acquired_evidence=None):
  """Only caller-confirmed server authorization. `performance_ready` must be sourced
  from scene asset verification, NEVER a client-provided boolean in production.
  Idempotency key prevents double charging on network retry.
  """
  if not approved:raise GuardError('Server approval missing')
  if not isinstance(action_id,str) or len(action_id)<12 or len(action_id)>100:raise GuardError('Invalid action id')
  if action_id in self._action_ids:
   data=self._action_ids[action_id]
   if data['actor_id']!=actor_id or data['tactic']!=tactic:raise GuardError('Idempotency key collision')
   return data['result']
  s=self.state(actor_id)
  if s.counsel_requested:raise GuardError('Interview ended after counsel request')
  if tactic not in TAC_COST:raise GuardError('Unsupported tactic')
  if tactic=='strike_table':
   if not performance_ready:raise GuardError('Authored hand animation, table contact and sound not verified')
   if 'strike_table' in s.tactic_history:raise GuardError('Physical intimidation cannot be repeated for rewards')
  if tactic=='present_evidence' and (not evidence_id or evidence_id not in (acquired_evidence or set())):
   raise GuardError('Present only acquired evidence')
  cost=TAC_COST[tactic]
  if s.seconds_left<cost:raise GuardError('Not enough interview time')
  s.seconds_left-=cost
  s.tactic_history.append(tactic)
  if tactic=='strike_table':
   s.credibility_damage+=2;s.hostility+=2;s.contact_discomfort+=2;s.recorded_coercive_episodes+=1
  elif tactic=='raise_voice':
   s.credibility_damage+=1;s.hostility+=1;s.contact_discomfort+=1;s.recorded_coercive_episodes+=1
  elif tactic=='offer_pause':
   s.hostility=max(0,s.hostility-1);s.contact_discomfort=max(0,s.contact_discomfort-1)
  elif tactic=='review_record':
   s.hostility=max(0,s.hostility-1)
  elif tactic=='target_discrepancy':
   s.hostility+=int(s.hostility>=2)
  if s.seconds_left<=0 or tactic=='end_interview':s.active=False
  # Person-dependent reaction; no guilt dependency
  bark=None
  options=ACTOR_RESPONSES.get(actor_id,{}).get(tactic)
  if options:
   index=int(sha256(f'{actor_id}|{action_id}|{tactic}'.encode()).hexdigest()[:8],16)%len(options)
   bark=options[index]
  # Repeated force + low cooperation -> right to stop conversation, not compelled confession
  if s.contact_discomfort>=3 or (actor_id=='s3' and tactic=='strike_table'):
   s.counsel_requested=True;s.active=False
   bark='변호인하고 얘기하고 싶습니다' if actor_id!='s3' else '저 이거 더 안 할래요, 변호사 불러주세요'
  result={'actor_id':actor_id,'tactic':tactic,'action_id':action_id,
          'seconds_left':s.seconds_left, 'interview_active':s.active,
          'counsel_requested':s.counsel_requested,'procedure_note':
          ('강압성 장면 기록 · 이후 진술 신빙성 검토 필요' if s.recorded_coercive_episodes else ''),
          'suggested_bark':bark,'performance_cue':('INVESTIGATOR_TABLE_STRIKE' if tactic=='strike_table' else None),
          'recording_event':'recorded_'+tactic,
          'coercion_flag_for_statement_quality':bool(s.recorded_coercive_episodes)}
  self._action_ids[action_id]={'actor_id':actor_id,'tactic':tactic,'result':result}
  return result

 def context(self,actor_id):
  s=self.state(actor_id)
  return {'seconds_left':s.seconds_left,'recent_player_tactics':s.tactic_history[-6:],
          'pressured':s.recorded_coercive_episodes>0,'hostility_context':min(s.hostility,3),
          'instruction':'Natural Korean only. A pressured person may object, withhold or request counsel. Never treat aggression as guilt. No forced confession.'}

 def public_state(self,actor_id):
  s=self._states.get(actor_id)
  if not s:return {'active':False}
  return {'active':s.active,'seconds_left':s.seconds_left,'counsel_requested':s.counsel_requested,
          'recording_warning':bool(s.recorded_coercive_episodes),'last_tactic':s.tactic_history[-1] if s.tactic_history else None}

 def mark_statement(self,actor_id,claim_index):
  s=self._states.get(actor_id)
  if s and s.recorded_coercive_episodes:
   s.pressured_statement_ids.append(claim_index)
   return 'PRESSURED_UNCORROBORATED'
  return 'UNVERIFIED'
