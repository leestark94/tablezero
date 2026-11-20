"""TABLE//ZERO authoritative reference runtime; demo-safe, no model API required.
Never serialize the locked case canon or suspect private records to the client.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import copy, json, hashlib, time

CANON_PATH = Path(__file__).resolve().parents[1] / 'reference' / 'CASE001_CANON_LOCKED.json'
CATALOG_PATH = Path(__file__).resolve().parents[1] / 'data' / 'cinematic_catalog_82.json'
MODES = {'answer','deny','partial_admission','counter','angry','silence','request_counsel','uncertain'}
ALLOWED_MOTIONS = {'still','cup_touch','hand_stop','look_down','table_slam','lean_back','finger_tap','deep_breath','shift_chair','avoid_gaze','cross_arms','lean_forward','back_in_chair','exhale','chair_shift','jaw_tight'}
ACTIONS = {'stay_quiet','prepare_statement','request_counsel','cancel_optional_meeting','contact_acquaintance','request_interview'}

@dataclass
class Event:
    event_id: str
    kind: str
    actor: str
    target: str | None
    timestamp: float
    visible_to: set[str]
    payload: dict = field(default_factory=dict)

class GuardError(ValueError): pass

class World:
    def __init__(self, canon=None):
        self._canon = copy.deepcopy(canon if canon is not None else json.loads(CANON_PATH.read_text(encoding='utf-8')))
        self._canonical_hash = self._hash(self._canon)
        self.suspects = {s['id']: copy.deepcopy(s) for s in self._canon['suspects']}
        self.public_events: list[Event] = []
        self.events: list[Event] = []
        self.claims: list[dict] = []
        self.knowledge: dict[str,set[str]] = {k:set() for k in self.suspects}
        self.available_evidence:set[str] = set()
        # What each suspect has actually been SHOWN (subset of available_evidence). Knowledge isolation.
        self.presented_to:dict[str,set[str]] = {k:set() for k in self.suspects}
        # Per-suspect interview transcript (server memory; replayed only to that suspect)
        self.transcripts:dict[str,list[dict]] = {k:[] for k in self.suspects}
        self.motions = set(ALLOWED_MOTIONS)
        self._seq = 0
        self._last_director:dict[tuple[str,str],float] = {}
        self.catalog = {x['id']:x for x in json.loads(CATALOG_PATH.read_text(encoding='utf-8'))}

    @staticmethod
    def _hash(obj): return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

    def assert_canon_unchanged(self):
        if self._hash(self._canon) != self._canonical_hash: raise GuardError('Canonical truth changed')

    def record(self,kind,actor,target=None,visible_to=None,payload=None):
        self._seq += 1
        e=Event(f'we-{self._seq:06d}',kind,actor,target,time.time(),set(visible_to or []),payload or {})
        self.events.append(e)
        return e

    def reveal(self,event_id,viewer):
        e=next((x for x in self.events if x.event_id==event_id),None)
        if not e: raise GuardError('Event not found')
        e.visible_to.add(viewer)
        if viewer in self.knowledge:self.knowledge[viewer].add(event_id)

    def expose_evidence(self,evidence_id):
        if evidence_id not in {x['id'] for x in self._canon['evidence']}: raise GuardError('Unknown evidence')
        self.available_evidence.add(evidence_id)

    def prompt_context(self,suspect_id,question,presented_evidence=None):
        if suspect_id not in self.suspects: raise GuardError('Unknown suspect')
        if presented_evidence is not None and presented_evidence not in self.available_evidence:raise GuardError('Evidence not acquired')
        # Deliberately no culprit_id, truth events, other suspects' hidden memory or detective inventory.
        s=self.suspects[suspect_id]
        safe_profile={k:v for k,v in s.items() if k in ('id','name','role','temperament','personality','speech_style','public_profile','concealment','goals')}
        known=[{'id':e.event_id,'kind':e.kind,'actor':e.actor,'target':e.target,'payload':e.payload}
               for e in self.events if suspect_id in e.visible_to]
        own_claims=[c for c in self.claims if c['suspect_id']==suspect_id]
        past=[{'utterance':c['utterance'],'mode':c['mode']} for c in own_claims][-12:]
        earlier=[{'utterance':c['utterance'],'mode':c['mode']} for c in own_claims[:-12]][:10]
        presented=None
        if presented_evidence is not None:
            source=next(x for x in self._canon['evidence'] if x['id']==presented_evidence)
            presented={key:source[key] for key in ('id','name','detail','limitations') if key in source}
        return {'character':safe_profile,'question':question[:1000], 'presented_evidence_id':presented_evidence,
                'presented_evidence_public_details':presented,'earlier_own_statements':earlier,
                'known_events':known,
                'private_memories':[{'id':e['id'],'at':e.get('at'),'event':e.get('event')} for e in self._canon['truth_events'] if e['id'] in set(s.get('private_fact_ids',[]))],
                'own_starting_claims':[{'id':c['id'],'text':c['text']} for c in self._canon['claims'] if c['id'] in set(s.get('starting_claim_ids',[]))],
                'previous_statements':past,'approved_motions':sorted(set(s.get('possible_motions',[])) & self.motions),
                'instruction':'Speak natural Korean; never treat a guess as case truth. Only propose an action.'}

    def validate_reply(self,suspect_id,reply):
        if suspect_id not in self.suspects:raise GuardError('Unknown suspect')
        if not isinstance(reply,dict):raise GuardError('Invalid response type')
        required={'utterance','reply_mode','motion_id','asserted_claim_ids','new_unsupported_assertion','request_external_action'}
        if set(reply)!=required:raise GuardError('Reply must match exact contract')
        if not isinstance(reply['utterance'],str) or len(reply['utterance'])>1200:raise GuardError('Invalid utterance')
        if reply['reply_mode'] not in MODES:raise GuardError('Invalid reply mode')
        if reply['motion_id'] not in self.motions or reply['motion_id'] not in set(self.suspects[suspect_id].get('possible_motions',[])):raise GuardError('Unavailable animation')
        if not isinstance(reply['asserted_claim_ids'],list):raise GuardError('Invalid claims')
        owned={c['id'] for c in self._canon['claims'] if c.get('suspect_id')==suspect_id or c.get('speaker_id')==suspect_id or c.get('speaker')==suspect_id}
        if any(not isinstance(cid,str) or cid not in owned for cid in reply['asserted_claim_ids']):raise GuardError('Claim not owned by speaker')
        if reply['new_unsupported_assertion'] is not None and (not isinstance(reply['new_unsupported_assertion'],str) or len(reply['new_unsupported_assertion'])>500):raise GuardError('Invalid unsupported assertion')
        if reply['request_external_action'] is not None and reply['request_external_action'] not in ACTIONS:raise GuardError('Unknown action proposal')
        return reply

    def accept_reply(self,suspect_id,reply):
        r=self.validate_reply(suspect_id,reply)
        entry={'suspect_id':suspect_id,'utterance':r['utterance'],'mode':r['reply_mode'],
               'asserted_claim_ids':r['asserted_claim_ids'], 'unsupported_unverified':r['new_unsupported_assertion']}
        self.claims.append(entry)
        # No autonomous action executed from speech. Director approves and executes separately.
        return {'utterance':r['utterance'],'reply_mode':r['reply_mode'],'motion_proposal':r['motion_id'],
                'action_proposal':r['request_external_action'],'claim_log_id':len(self.claims),'claims_verified':False}

    def action(self,actor,kind,target=None,approved=False,payload=None):
        if not approved:raise GuardError('Server must approve action')
        if actor not in self.suspects or kind not in ACTIONS:raise GuardError('Invalid actor/action')
        if kind=='contact_acquaintance':
            if not target or target not in self.suspects or target==actor:raise GuardError('Invalid contact')
            # The canonical relationship graph is the authority; never allow arbitrary contacts.
            edges=self._canon.get('autonomy',{}).get('communication_edges',[])
            def edge_ok(e):
                if isinstance(e,dict):
                    a=e.get('from') or e.get('source') or e.get('actor_id'); b=e.get('to') or e.get('target') or e.get('target_id')
                    return (a==actor and b==target) or (e.get('bidirectional') and a==target and b==actor)
                return False
            if not any(edge_ok(e) for e in edges):raise GuardError('Contact not canon-authorized')
            e=self.record(kind,actor,target,{actor,target},{'contact_occurred':True,**(payload or {})})
        else:
            e=self.record(kind,actor,target,{actor}, {'approved':True,**(payload or {})})
        for p in e.visible_to:self.knowledge[p].add(e.event_id)
        return e.event_id

    def director(self,actor,event_id,now=None,flags=None,available_clips=None):
        if event_id not in self.catalog:raise GuardError('Unknown cinematic')
        event=self.catalog[event_id]; now=time.monotonic() if now is None else now
        flags=set(flags or [])
        if not set(event['requires']).issubset(flags):return {'play':False,'reason':'preconditions'}
        if available_clips is not None and event['animation'] not in available_clips:return {'play':False,'reason':'missing_animation'}
        key=(actor,event_id)
        if now-self._last_director.get(key,float('-inf'))<event['cooldown_s']:return {'play':False,'reason':'cooldown'}
        self._last_director[key]=now
        return {'play':True,'id':event_id,'animation':event['animation'],'sfx':event['sfx'],
                'camera_impulse':min(event['camera_impulse'],0.15),'physics_event':event['physics_event'],
                'subtitle':event['subtitle']}

    def evaluate_report(self, accused_id, submitted_evidence):
        """Game-only evidence-axis sufficiency; not a legal guilt determination."""
        if accused_id not in self.suspects: raise GuardError('Unknown accused person')
        if not isinstance(submitted_evidence,(list,set,tuple)): raise GuardError('Invalid evidence list')
        submitted=set(submitted_evidence)
        if not submitted.issubset(self.available_evidence): raise GuardError('Evidence not acquired')
        logic=self._canon['case_result_logic']
        axes={}
        for axis in logic['must_prove']:
            key=axis+'_evidence_sets'
            axes[axis]=any(set(s).issubset(submitted) for s in logic[key])
        return {'accused_id':accused_id,'axes':axes,'sufficient_for_game_report':
                accused_id==logic['identity'] and all(axes.values()),
                'disclaimer':'게임 내부 입증 기준이며 실제 형사재판의 판결이 아닙니다.'}

    def projection(self,viewer='detective'):
        self.assert_canon_unchanged()
        return {'case_id':self._canon['case_id'],'title':self._canon['title'],
                'evidence_ids':sorted(self.available_evidence),
                'events':[{'event_id':e.event_id,'kind':e.kind,'actor':e.actor,'target':e.target}
                          for e in self.events if viewer in e.visible_to],
                'statements':[{'suspect_id':x['suspect_id'],'utterance':x['utterance'],'verified':False} for x in self.claims]}
