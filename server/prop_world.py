"""CASE001 scene prop interaction authority, independent of Unity rendering.
Not a legal evidence acquisition engine. A prop observation cannot become a VerifiedFact
or an acquired evidence ID without the existing EpisodeController.acquire() workflow.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import json
from .runtime import GuardError
MANIFEST=Path(__file__).resolve().parents[1]/'data'/'room302_interaction_manifest.json'
VALID_VERBS={'inspect','open','close','move','activate','deactivate'}

@dataclass
class ScenePropState:
    opened:bool=False
    active:bool=False
    inspected:int=0
    moved:bool=False

class PropWorld:
    """Authoring-level contract, not a gameplay security boundary.
    Production must issue signed/validated interaction requests using the server's
    actual player location, scene, access permissions and line of sight. `authorized`
    here must NEVER map directly to a trustable client JSON boolean.
    """
    def __init__(self,manifest=None):
        manifest=manifest or json.loads(MANIFEST.read_text(encoding='utf-8'))
        self.definitions={p['prop_id']:p for p in manifest['props']}
        if len(self.definitions)!=len(manifest['props']):raise GuardError('Duplicate prop IDs')
        self.states={pid:ScenePropState() for pid in self.definitions}
        self.log:list[dict]=[]
        self._transactions:dict[str,dict]={}

    def _get(self,prop_id):
        if prop_id not in self.definitions: raise GuardError('Unknown scene prop')
        return self.definitions[prop_id],self.states[prop_id]

    def public_target(self,prop_id, *, zone, visible=True):
        p,s=self._get(prop_id)
        if p['zone']!=zone or not visible:return None
        parent=p.get('parent_container')
        if parent and not self.states[parent].opened:return None
        return {'prop_id':prop_id,'label':p['label_ko'],
                'available_actions':self.allowed_actions(prop_id),
                'procedural_caution':p['procedural_caution']}

    def allowed_actions(self,prop_id):
        p,s=self._get(prop_id)
        kinds={'inspect':['inspect'],'move':['inspect','move'],
               'evidence_anchor':['inspect'],
               'container':['inspect','close' if s.opened else 'open'],
               'door':['inspect','close' if s.opened else 'open'],
               'switch':['inspect','deactivate' if s.active else 'activate']}
        return kinds[p['interaction_type']]

    def interact(self,prop_id,verb,*,action_id,authorized=False,asset_ready=False,
                 access_grants=()):
        if not authorized:raise GuardError('Scene server authorization required')
        if not isinstance(action_id,str) or not 12<=len(action_id)<=120:
            raise GuardError('action_id required for idempotency')
        if action_id in self._transactions:
            old=self._transactions[action_id]
            if (old['prop_id'],old['verb'])!=(prop_id,verb):raise GuardError('Action ID collision')
            return old['response']
        p,s=self._get(prop_id)
        if not asset_ready: raise GuardError('Authored mesh/rig not verified')
        parent=p.get('parent_container')
        if parent and not self.states[parent].opened:raise GuardError('Open parent container first')
        if p.get('gate') and p['gate'] not in set(access_grants):
            # Observation still allowed; accessing a restricted fixture/object is not
            if verb!='inspect':raise GuardError('Explicit procedural/tool permission required')
        if verb not in VALID_VERBS or verb not in self.allowed_actions(prop_id):
            raise GuardError('Verb not allowed for prop state')
        if verb=='open':s.opened=True
        elif verb=='close':s.opened=False
        elif verb=='move':s.moved=True
        elif verb=='activate':s.active=True
        elif verb=='deactivate':s.active=False
        if verb=='inspect':s.inspected+=1
        # Any mundane prop can be a player lead, but never implies a new canon fact
        response={'prop_id':prop_id,'verb':verb,
                  'observation':p['observation_ko'] if verb=='inspect' else '',
                  'canonical_evidence_reference':p.get('canonical_evidence_id'),
                  'evidence_acquired':False,'verified_fact_created':False,
                  'opened':s.opened,'active':s.active,'moved':s.moved,
                  'requires_separate_evidence_workflow':bool(p.get('canonical_evidence_id'))}
        self._transactions[action_id]={'prop_id':prop_id,'verb':verb,'response':response}
        self.log.append({'action_id':action_id,'prop_id':prop_id,'verb':verb})
        return response

    def audit(self, scene_ids,verified_ids):
        """Comparison of authored scene bindings with the interaction contract.
        `scene_ids` is collected by a Unity Editor scanner; `verified_ids` only after
        someone checked mesh/pivot/collider/hand contact/visibility in Play Mode.
        """
        ids=set(self.definitions);scene=set(scene_ids);verified=set(verified_ids)
        return {'declared':len(ids),'scene_bound':len(ids&scene),
                'quality_verified':len(ids&verified),
                'missing_scene_bindings':sorted(ids-scene),
                'unexpected_scene_bindings':sorted(scene-ids),
                'bound_but_unverified':sorted((ids&scene)-verified),
                'ship_blocked':bool(ids-scene or scene-ids or (ids&scene)-verified)}
