"""Reference-only smoke walkthrough: NEVER represents a 3D game, licensed AI, or a shipped build."""
from __future__ import annotations
import json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from server.episode_controller import EpisodeController
from server.interview_service import InterviewService
from server.prop_world import PropWorld
from server.providers import PreviewProvider
from server.v11_cinematic_gate import CinematicGate

def execute():
    p=PropWorld();c=EpisodeController(provider=PreviewProvider());g=CinematicGate()
    steps=[]
    steps.append({'case_scene_before':c.state.scene,'evidence_initial':sorted(c.world.available_evidence),'ai_provider':'SCRIPTED_PREVIEW_NOT_AI'})
    c.transition('room302')
    r=p.interact('kitchen_fridge_door','open',action_id=uuid.uuid4().hex,authorized=True,asset_ready=True)
    steps.append({'action':'OPEN FRIDGE / LOGIC ONLY','opened':r['opened']})
    r=p.interact('kitchen_fridge_bottle','inspect',action_id=uuid.uuid4().hex,authorized=True,asset_ready=True)
    steps.append({'action':'INSPECT BOTTLE / LOGIC ONLY','observation':r['observation'],'evidence_acquired':r['evidence_acquired']})
    c.transition('desk');c.transition('interview')
    service=InterviewService(c);service.begin('s2')
    out=service.ask('그날 전화한 사실은 맞아요?',input_mode='typed',action_id=uuid.uuid4().hex)
    steps.append({'action':'TEXT TURN / PREVIEW ONLY','text':out.suspect_text,'latency_ms':out.latency_ms,'interview_seconds_left':out.seconds_left,'provider':out.provider})
    denied=g.request('V11_PLAYER_TABLE_STRIKE',scene='interview',flags=['pressure_tactic_approved'],verified_asset_ids=[],safe_window=True)
    steps.append({'action':'CINEMATIC GATE','approved':denied['approved'],'reason':denied['reason']})
    return {'status':'LOGIC_REFERENCE_ONLY_NO_UNITY_NO_LIVE_MODEL','steps':steps,
            'private_canon_not_serialized': 'culprit_id' not in json.dumps(steps)}
if __name__=='__main__':print(json.dumps(execute(),ensure_ascii=False,indent=2))
