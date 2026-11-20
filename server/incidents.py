"""Unplanned-feeling but authored, causally safe interruptions.
No fabricated evidence, culprit hints, or arbitrary truth mutation.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
from .runtime import GuardError

INCIDENTS=[
 {'id':'h_sensor_delay','scene':'hall','act':'arrival','line':'센서등이 한 박자 늦게 켜진다','needs':['hall_sensordelay','fluorescent_hum'],'changes_world':False},
 {'id':'h_wrong_door','scene':'hall','act':'arrival','line':'옆집 문고리가 잠깐 움직이다 멈춘다','needs':['neighbor_door_rig','door_latch'],'changes_world':False},
 {'id':'h_elevator','scene':'hall','act':'exploration','line':'아래층에서 엘리베이터 도착음이 울린다','needs':['elevator_audio'],'changes_world':False},
 {'id':'r_fridge','scene':'room302','act':'exploration','line':'냉장고 모터가 켜지며 잠깐의 정적을 깬다','needs':['fridge_loop'],'changes_world':False},
 {'id':'r_wall_thud','scene':'room302','act':'exploration','line':'위층에서 둔탁한 물건 끄는 소리가 난다','needs':['upstairs_furniture_audio'],'changes_world':False},
 {'id':'r_arriving_footsteps','scene':'room302','act':'redirection','line':'복도 발소리가 문 앞에서 멈추더니 다시 멀어진다','needs':['hall_footstep_audio'],'changes_world':False},
 {'id':'r_phone_vibration','scene':'room302','act':'pressure','line':'서류 옆 업무용 전화기가 짧게 진동한다','needs':['work_phone_mesh','phone_vibrate_audio'],'changes_world':False},
 {'id':'i_microphone','scene':'interview','act':'first_contact','line':'녹음기의 레벨 미터가 잠깐 치솟는다','needs':['recorder_mesh','mic_touch_sfx'],'changes_world':False},
 {'id':'i_paper_curl','scene':'interview','act':'pressure','line':'용의자가 종이 모서리를 천천히 접었다 펴 놓는다','needs':['paper_corner_animation','paper_rustle'],'changes_world':False},
 {'id':'i_cup_condensation','scene':'interview','act':'redirection','line':'물컵을 밀자 바닥의 물자국이 테이블 위에 남는다','needs':['glass_condensation_shader','cup_slide_audio'],'changes_world':False},
 {'id':'i_phone_ring','scene':'interview','act':'pressure','line':'조사실 밖 유선전화가 두 번 울리고 끊긴다','needs':['hall_phone_ring'],'changes_world':False},
 {'id':'d_printer','scene':'desk','act':'aftershock','line':'프린터에서 보완 요청 서류가 늦게 나온다','needs':['printer_mesh','printer_sfx'],'changes_world':False},
 {'id':'d_cold_coffee','scene':'desk','act':'redirection','line':'동료가 식은 커피를 한 모금 마시다 내려놓는다','needs':['colleague_drink_animation','ceramic_sfx'],'changes_world':False},
]
@dataclass
class IncidentState:
 seen:set[str]=field(default_factory=set)
 sequence:int=0
 last_at:float=-9999.0
 act_counts:dict[str,int]=field(default_factory=dict)

class IncidentDirector:
 def __init__(self,session_seed='case001'):
  self.seed=session_seed;self.state=IncidentState()

 def suggest(self,scene,act,now,verified_assets,*,safe_window=False):
  if not safe_window or now-self.state.last_at<135:return {'approved':False,'reason':'pacing_or_safe_window'}
  if self.state.act_counts.get(act,0)>=1:return {'approved':False,'reason':'one_incident_per_act'}
  options=[x for x in INCIDENTS if x['scene']==scene and x['act']==act and x['id'] not in self.state.seen]
  options=[x for x in options if set(x['needs']).issubset(set(verified_assets))]
  if not options:return {'approved':False,'reason':'missing_authored_assets'}
  idx=int(sha256(f'{self.seed}|{act}|{self.state.sequence}'.encode()).hexdigest()[:8],16)%len(options)
  x=options[idx]
  # No world state is changed; only a cue is authorized.
  if x['changes_world']:raise GuardError('Incident cannot mutate canonical world')
  self.state.seen.add(x['id']);self.state.sequence+=1;self.state.last_at=now
  self.state.act_counts[act]=self.state.act_counts.get(act,0)+1
  return {'approved':True,'incident_id':x['id'],'staging':x['line'],'asset_ids':list(x['needs']),
          'may_claim_new_evidence':False,'gameplay_interruptible':True}
