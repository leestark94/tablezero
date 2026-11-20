"""Proof-of-integration barrier for V11 movie-like beats.
LLMs cannot choose the exact physical execution; server permits candidate only, Unity
must confirm actual playback. No sound or animation asset = no cinematic claim.
"""
from __future__ import annotations
from collections import defaultdict
import json,time,uuid
from pathlib import Path
from .runtime import GuardError
CATALOG=Path(__file__).resolve().parents[1]/'data'/'v11_signature_cinematic_beats.json'

class CinematicGate:
    def __init__(self):
        data=json.loads(CATALOG.read_text('utf-8'))
        self.beats={b['beat_id']:b for b in data['beats']}
        self.counts=defaultdict(int)
        self.last_played=defaultdict(lambda:-10_000.)
        self.pending={}
        self.playback_log=[]

    def request(self,beat_id,*,scene,flags=(),verified_asset_ids=(),now=None,safe_window=False):
        if beat_id not in self.beats:raise GuardError('Unknown shot ID')
        b=self.beats[beat_id];now=time.monotonic() if now is None else float(now)
        if b['scene']!=scene:return {'approved':False,'reason':'scene_mismatch'}
        if not safe_window:return {'approved':False,'reason':'unsafe_play_window'}
        if not set(b['conditions']).issubset(set(flags)):
            return {'approved':False,'reason':'conditions_not_met'}
        if not set(b['required_assets']).issubset(set(verified_asset_ids)):
            return {'approved':False,'reason':'authored_assets_missing'}
        self.pending={k:v for k,v in self.pending.items() if now-v['time'] <= 15.0}
        if any(x['beat_id']==beat_id for x in self.pending.values()):
            return {'approved':False,'reason':'playback_already_pending'}
        if self.counts[beat_id]>=b['per_session_limit']:
            return {'approved':False,'reason':'session_repeat_limit'}
        if now-self.last_played[beat_id]<b['cooldown_s']:
            return {'approved':False,'reason':'cooldown'}
        token=uuid.uuid4().hex
        self.pending[token]={'beat_id':beat_id,'time':now}
        return {'approved':True,'authorization_token':token,'beat_id':beat_id,
                'performance':b['performance'],'sound_direction':b['sound_direction'],
                'camera_rule':b['camera_rule'],'physical_result':b['physical_result'],
                'world_mutation':False,
                'status':'AUTHORIZED_NOT_YET_PLAYED'}

    def confirm_playback(self,token,*,started:bool,played_by_authorized_runtime:bool):
        item=self.pending.pop(token,None)
        if item is None:raise GuardError('Unknown/expired playback token')
        if not started or not played_by_authorized_runtime:
            return {'played':False,'beat_id':item['beat_id'],'reason':'unity_did_not_confirm'}
        beat_id=item['beat_id']
        self.counts[beat_id]+=1
        self.last_played[beat_id]=item['time']
        record={'beat_id':beat_id,'authorized_and_played':True,'world_mutation':False}
        self.playback_log.append(record)
        return {'played':True,'beat_id':beat_id,'world_mutation':False}
