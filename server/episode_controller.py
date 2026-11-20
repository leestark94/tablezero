"""Runnable CASE001 reference controller connecting V06 truth, V07 beats and V08 endings.
No scene meshes or premium cinematics are claimed here. All exposed data are public projections.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import json, time, uuid
from .runtime import World, GuardError
from .beat_director import BeatDirector, TrustedSignal, AssetManifest
from .dialogue_quality import clean_line, lint_line
from .outcomes import OutcomeDirector
from .providers import ProviderGate, PreviewProvider

SCENES=frozenset(['hall','room302','interview','desk'])
SCENE_TRANSITIONS={
 'hall':{'room302','desk'},
 'room302':{'hall','desk'},
 'desk':{'hall','interview','room302'},
 'interview':{'desk'}
}

@dataclass
class EpisodeState:
    scene:str='hall'
    act:str='arrival'
    started_at:float=field(default_factory=time.monotonic)
    interviewed:set[str]=field(default_factory=set)
    interview_active:str|None=None
    claimed_items:set[str]=field(default_factory=set)
    authorized_events:set[str]=field(default_factory=set)
    acquired_chain:dict[str,list[str]]=field(default_factory=dict)
    closed:bool=False
    case_clock_minutes:int=22*60+7
    persons_in_custody:set[str]=field(default_factory=set)
    open_meetings:set[str]=field(default_factory=set)
    shot_history:list[str]=field(default_factory=list)
    cue_history:list[dict]=field(default_factory=list)
    # Each arrival is not a forced cutscene: active control and subtitle timing are client-driven

class EpisodeController:
    def __init__(self, provider=None, world=None):
        self.world=world or World()
        self.director=BeatDirector(self.world)
        self.outcomes=OutcomeDirector(self.world)
        self.provider=ProviderGate(provider or PreviewProvider())
        self.state=EpisodeState()
        self.logs:list[dict]=[]
        self.session_id=uuid.uuid4().hex
        # e01 is obtained at start by CASE001; must still be considered in player flow
        for item in self.world._canon['evidence']:
            if item.get('access')=='obtained_at_start':
                self.world.expose_evidence(item['id'])
                self.state.acquired_chain[item['id']]=['existing_record','case_file']

    def transition(self, scene:str):
        if self.state.closed:raise GuardError('The submitted report has closed this session')
        if scene not in SCENES or scene not in SCENE_TRANSITIONS[self.state.scene]:
            raise GuardError('Invalid scene transition')
        if self.state.interview_active:raise GuardError('Finish interview before leaving')
        previous=self.state.scene
        self.state.scene=scene
        self._log('scene_changed',{'from':previous,'to':scene})
        return self.public_state()

    def set_act(self, act):
        choices={'arrival','exploration','first_contact','pressure','redirection','aftershock'}
        if act not in choices:raise GuardError('Invalid story act')
        order=['arrival','exploration','first_contact','pressure','redirection','aftershock']
        if order.index(act)<order.index(self.state.act):raise GuardError('Act cannot rewind')
        self.state.act=act

    def acquire(self, evidence_id:str, *, authorized:bool=False, photo_logged:bool=False, sealed:bool=False):
        if self.state.closed:raise GuardError('Case closed')
        item=next((v for v in self.world._canon['evidence'] if v['id']==evidence_id),None)
        if not item:raise GuardError('Unknown item')
        # In live game this is driven by signed server-side action authorization; never use client boolean alone
        if not authorized:raise GuardError('Server authorization required')
        if evidence_id in self.world.available_evidence:return {'duplicate':True}
        if item['access']=='obtained_at_start':raise GuardError('Starting record already present')
        if evidence_id in ('e04',) and self.state.scene!='room302':
            raise GuardError('Physical evidence requires scene')
        if not photo_logged:raise GuardError('Evidence provenance/photo record required')
        if item['access'] in ('scene_collect','warrant_after_sufficient_cause') and not sealed:
            raise GuardError('Physical evidence requires packaging/chain log')
        self.world.expose_evidence(evidence_id)
        chain=['authorization','photo','acquisition']+(['sealed'] if sealed else [])
        self.state.acquired_chain[evidence_id]=chain
        self._log('evidence_acquired',{'id':evidence_id,'chain':chain})
        return {'acquired':True,'id':evidence_id,'chain':chain}

    def start_interview(self, suspect_id):
        if self.state.scene!='interview' or self.state.interview_active:
            raise GuardError('Interview scene not ready')
        if suspect_id not in self.world.suspects:raise GuardError('Unknown actor')
        self.state.interview_active=suspect_id
        self.state.interviewed.add(suspect_id)
        self._log('interview_started',{'actor':suspect_id})
        return {'actor_id':suspect_id,'opened':True}

    def question(self, text, presented_evidence=None):
        if self.state.scene!='interview' or not self.state.interview_active:
            raise GuardError('No active interview')
        question=clean_line(text,max_chars=500)
        actor=self.state.interview_active
        if presented_evidence is not None and presented_evidence not in self.world.available_evidence:
            raise GuardError('Cannot present evidence not acquired')
        ctx=self.world.prompt_context(actor,question,presented_evidence)
        provider_info=self.provider.run(ctx)
        reply=self.world.validate_reply(actor,provider_info['result'])
        problems=lint_line(reply['utterance'],[x['utterance'] for x in self.world.claims if x['suspect_id']==actor],for_llm=True)
        # For production fail closed on destructive naturalness problems; minor repetition should be staged retry
        blockers={'stock_ai_dialogue','melodramatic_exposition','forbidden_guilt_meter','prompt_injection_literal','repeated_line','too_long_for_one_utterance'}
        if blockers.intersection(problems):raise GuardError('Dialogue failed style/safety gate: '+','.join(problems))
        reply['utterance']=clean_line(reply['utterance'])
        accepted=self.world.accept_reply(actor,reply)
        self._log('interview_reply',{'actor':actor,'reply_mode':reply['reply_mode'],
            'provider':provider_info['provider'],'latency_ms':provider_info['latency_ms'],
            'has_proposed_action':bool(accepted['action_proposal'])})
        return {'line':accepted['utterance'],'reply_mode':accepted['reply_mode'],
            'motion_proposal':accepted['motion_proposal'],
            'action_proposal':accepted['action_proposal'],
            'provider':provider_info['provider'],'latency_ms':provider_info['latency_ms'],
            'style_notes':problems,'claimed_facts_verified':False}

    def advance_case_clock(self, minutes:int, *, approved:bool=False):
        if not approved or not isinstance(minutes,int) or minutes<0 or minutes>90:
            raise GuardError('Clock advance requires authorized bounded game action')
        self.state.case_clock_minutes+=minutes
    def resolve_action(self, kind, target=None, *, approved=False):
        actor=self.state.interview_active
        if not actor:raise GuardError('Action requires active NPC')
        if not approved:raise GuardError('World authority must approve')
        rules=self.world._canon.get('autonomy',{}).get('action_windows',{}).get(kind,{})
        if 'min_case_clock' in rules:
            hour,minute=(int(n) for n in rules['min_case_clock'].split(':'))
            if self.state.case_clock_minutes<hour*60+minute:
                raise GuardError('Contact not yet possible in case timeline')
        if rules.get('requires_not_in_custody') and actor in self.state.persons_in_custody:
            raise GuardError('Actor cannot contact while in custody')
        if rules.get('requires_open_meeting') and actor not in self.state.open_meetings:
            raise GuardError('No optional meeting open')
        event=self.world.action(actor,kind,target,approved=True)
        self._log('world_event_committed',{'id':event,'kind':kind})
        return {'event_id':event,'world_changed':True}

    def finish_interview(self):
        if not self.state.interview_active:raise GuardError('No interview')
        self._log('interview_ended',{'actor':self.state.interview_active})
        self.state.interview_active=None

    def cinematic(self,signal:TrustedSignal, manifest:AssetManifest|None=None, *, now=None):
        if signal.scene!=self.state.scene:raise GuardError('Signal scene mismatch')
        # Only server-validated signal accepted; never trust client-crafted flags in production
        decision=self.director.choose_and_authorize(signal,manifest,now=now)
        if decision.get('approved'):
            self.state.cue_history.append({'id':decision['playback']['beat_id'],'at':time.monotonic()})
        return decision

    def file_report(self, accused_id, submitted_evidence, *, chain_defects=(), final=False):
        if self.state.scene!='desk' or self.state.interview_active:
            raise GuardError('Report must be filed from investigation desk')
        if not final:raise GuardError('Explicit final confirmation required')
        outcome=self.outcomes.submit(accused_id,submitted_evidence,chain_defects=chain_defects)
        self.state.closed=not outcome.can_continue
        self._log('report_submitted',{'accepted':outcome.report_accepted,'missing_axis_count':len(outcome.missing_axes)})
        return OutcomeDirector.public_projection(outcome,self.outcomes.reaction(outcome,accused_id))

    def public_state(self):
        p=self.world.projection()
        # Safe public status, never raw suspect context or entire canon
        return {'case_id':p['case_id'],'title':p['title'],'scene':self.state.scene,
                'act':self.state.act,'active_interview':self.state.interview_active,
                'evidence_ids':p['evidence_ids'],'visible_events':p['events'],
                'statements':p['statements'],'known_people':[{'id':sid,'name':self.world.suspects[sid]['name']} for sid in sorted(self.state.interviewed)], 'case_closed':self.state.closed}

    def _log(self,kind,data):
        self.logs.append({'type':kind,'time_monotonic':time.monotonic(),**data})
