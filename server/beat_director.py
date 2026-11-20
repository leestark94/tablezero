"""TABLE//ZERO Korean cinematic beat arbitration (reference code, server only).

This does not call an LLM, modify CASE canon, invent evidence or execute Unity animations.
A choice becomes an executable performance only after authoritative state and asset checks.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional
import json
import time

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / 'data' / 'case001_director_beats.json'
TRIGGERS = {'enter','ambient','inspect','collect','present','question','reply','start_interview','end_interview',
            'witness_start','world_event','leave'}
SCENES = {'hall','room302','interview','desk'}
SCENE_KINDS = {'scene','evidence','interview','witness','ambient_surprise','procedural_interrupt','world_event_echo'}

@dataclass(frozen=True)
class TrustedSignal:
    """Construct server-side only. Flags/intent/reply mode must not be client-authored.
    Example: question_intent is a server-validated classification, NOT a keyword guessed on client.
    """
    scene: str
    trigger: str
    actor_id: str = 'any'
    flags: frozenset[str] = field(default_factory=frozenset)
    question_intent: str = ''
    reply_mode: str = ''
    act: str = ''

@dataclass(frozen=True)
class AssetManifest:
    """Read from verified Unity scene binding inventory, NEVER from LLM output."""
    cue_ids: frozenset[str] = field(default_factory=frozenset)
    gestures: frozenset[str] = field(default_factory=frozenset)
    sounds: frozenset[str] = field(default_factory=frozenset)
    props: frozenset[str] = field(default_factory=frozenset)
    verified_in_playmode: bool = False

    @staticmethod
    def for_reference_test(beat: dict) -> 'AssetManifest':
        """Unit testing ONLY: synthetic bindings, NOT Unity assets."""
        p=beat['performance']
        return AssetManifest(frozenset([beat['original_v06_cue']]),frozenset([p['gesture']]),
                             frozenset([p['sound']]),frozenset([p['prop']]),False)

class BeatValidationError(ValueError): pass

class BeatDirector:
    def __init__(self, world, catalog_path: str|Path = DEFAULT_CATALOG):
        self.world = world
        data=json.loads(Path(catalog_path).read_text(encoding='utf-8'))
        self.beats = data['beats']
        self.by_id={b['id']: b for b in self.beats}
        if len(self.by_id) != len(self.beats):raise BeatValidationError('Duplicate beat ID')
        catalog_ids=set(self.world.catalog)
        evidence_ids={e['id'] for e in self.world._canon['evidence']}
        for b in self.beats:
            if b['trigger'] not in TRIGGERS or b['scene'] not in SCENES or b['kind'] not in SCENE_KINDS:
                raise BeatValidationError(f'Unknown scene/trigger/kind for {b["id"]}')
            if b['original_v06_cue'] not in catalog_ids:raise BeatValidationError('Missing base cue '+b['id'])
            if not set(b['requires_evidence_ids']).issubset(evidence_ids):raise BeatValidationError('Foreign evidence '+b['id'])
            if b.get('world_mutation')!='NEVER_FROM_CUE' or b.get('evidence_creation')!='NONE':
                raise BeatValidationError('Never create game truth from presentation')
            if b['kind']=='world_event_echo' and not b['requires_visible_world_event']:
                raise BeatValidationError('World echo must be event anchored')
        self.last_played:dict[str,float]={}
        self.counts:dict[str,int]={}
        self.last_surprise_time=-float('inf')
        self.audit:list[dict]=[]

    def visible_world_events(self, viewer='detective')->set[str]:
        return {e.kind for e in self.world.events if viewer in e.visible_to}

    def reasons(self, beat:dict, signal:TrustedSignal, now:float) -> list[str]:
        reasons=[]
        if beat['trigger']!=signal.trigger or beat['scene']!=signal.scene: reasons.append('trigger_scene')
        if beat['actor_id']!='any' and beat['actor_id']!=signal.actor_id: reasons.append('actor')
        if signal.act and beat['act']!=signal.act: reasons.append('act')
        if not set(beat['requires_flags']).issubset(signal.flags): reasons.append('flags')
        if set(beat['forbids_flags']) & signal.flags: reasons.append('forbidden_flags')
        if not set(beat['requires_evidence_ids']).issubset(self.world.available_evidence): reasons.append('missing_evidence')
        if beat['requires_visible_world_event'] and beat['requires_visible_world_event'] not in self.visible_world_events():
            reasons.append('unobserved_world_event')
        if beat['required_reply_modes'] and signal.reply_mode not in beat['required_reply_modes']:
            reasons.append('reply_mode')
        if beat['question_intent'] and signal.question_intent!=beat['question_intent']:
            reasons.append('question_intent')
        if self.counts.get(beat['id'],0)>=beat['max_per_session']: reasons.append('repeat_limit')
        if now-self.last_played.get(beat['id'],-float('inf'))<beat['cooldown_s']:
            reasons.append('cooldown')
        if beat['kind']=='ambient_surprise' and now-self.last_surprise_time<120:
            reasons.append('surprise_density')
        if beat['original_v06_cue']=='interview.table_slam':
            actor=self.world.suspects.get(signal.actor_id)
            if actor is None or 'table_slam' not in actor.get('possible_motions',[]):
                reasons.append('actor_not_authorized_for_slam')
        return reasons

    def candidates(self, signal:TrustedSignal, now:float|None=None) -> list[dict]:
        now=time.monotonic() if now is None else now
        if signal.trigger not in TRIGGERS or signal.scene not in SCENES:
            raise BeatValidationError('Illegal server signal')
        valid=[b for b in self.beats if not self.reasons(b,signal,now)]
        # Player-facing hints are not baked into random props or elevated by AI emotional scores.
        valid.sort(key=lambda b:(-b['priority'],b['id']))
        return valid

    def authorize(self, beat_id:str, signal:TrustedSignal, manifest:AssetManifest|None, now:float|None=None)->dict:
        now=time.monotonic() if now is None else now
        if beat_id not in self.by_id:raise BeatValidationError('Unknown beat')
        b=self.by_id[beat_id]
        reasons=self.reasons(b,signal,now)
        if manifest is None:
            reasons.append('no_scene_asset_manifest')
        else:
            p=b['performance']
            if b['original_v06_cue'] not in manifest.cue_ids:reasons.append('missing_unity_cue')
            if p['gesture'] not in manifest.gestures:reasons.append('missing_authored_gesture')
            if p['sound'] not in manifest.sounds:reasons.append('missing_recorded_sound')
            if p['prop'] not in manifest.props:reasons.append('missing_physics_prop_or_explicit_none_binding')
        if reasons:
            result={'approved':False,'id':beat_id,'reasons':sorted(set(reasons))}
            self.audit.append(result)
            return result
        self.last_played[beat_id]=now
        self.counts[beat_id]=self.counts.get(beat_id,0)+1
        if b['kind']=='ambient_surprise':self.last_surprise_time=now
        # No Korean narrative secrets, sample AI utterances, evidence ids, or canon in the payload.
        return {'approved':True,'playback':{
            'beat_id':beat_id,
            'legacy_cue':b['original_v06_cue'],
            'gesture_binding':b['performance']['gesture'],
            'sound_binding':b['performance']['sound'],
            'prop_binding':b['performance']['prop'],
            'camera_style':b['performance']['camera'],
            'duration_s':b['performance']['duration_s'],
            'contact_animation_event':b['performance']['animation_contact_event'],
            'reduced_motion_required':True},
            'status':'PLAYMODE_VERIFIED' if manifest.verified_in_playmode else 'ASSET_MANIFEST_ACCEPTED_NOT_PLAYMODE_VERIFIED'}

    def choose_and_authorize(self,signal:TrustedSignal,manifest:AssetManifest|None,now:float|None=None):
        now=time.monotonic() if now is None else now
        candidates=self.candidates(signal,now)
        if not candidates:return {'approved':False,'reason':'no_eligible_story_beat'}
        results=[]
        for b in candidates:
            r=self.authorize(b['id'],signal,manifest,now)
            if r['approved']:return r
            results.append({'id':b['id'],'reasons':r['reasons']})
        return {'approved':False,'reason':'no_bound_assets','blocked':results}
