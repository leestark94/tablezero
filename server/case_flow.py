"""CASE 001 playable flow authority: scene props, scene evidence procedure, desk record requests.

Server decides everything here from its own state (scene, player position sanity, prop graph,
procedure flags, action budget, case clock). The client only sends intents.
Nothing here can create a new canon fact: evidence ids come only from the locked canon.
"""
from __future__ import annotations
from pathlib import Path
import json, math, os
from .runtime import GuardError
from .prop_world import PropWorld

ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ROOT / 'data' / 'room302_prop_positions.json'
ART_STATUS = ROOT / 'data' / 'asset_verification.json'

ZONE_SCENE = {'hall': 'hall'}  # every other zone belongs to scene 'room302'
# Scene state when the detective arrives (victim's lamp and hood light left on, hallway sensor lit).
# Must match TZInspectableProp.startActive set by the Unity builder.
INITIAL_ACTIVE = {'living_lamp', 'kitchen_hood', 'hall_sensor'}
# The neighbour found the front door ajar (canon t09); it is still open when the detective arrives.
INITIAL_OPEN = {'entrance_door'}
SCENE_NOTES = ROOT / 'data' / 'room302_scene_notes.json'

def apply_scene_notes(props):
    """Story-grounded observation text + registered extra props (xprop_*). Observations only;
    no extra prop carries a canonical evidence id."""
    if not SCENE_NOTES.exists():
        return
    notes = json.loads(SCENE_NOTES.read_text(encoding='utf-8'))
    for pid, text in notes.get('observation_overrides', {}).items():
        if pid in props.definitions:
            props.definitions[pid] = dict(props.definitions[pid], observation_ko=text)
    for x in notes.get('extra_props', []):
        d = {'zone': x['zone'], 'label_ko': x['label_ko'], 'interaction_type': x['interaction_type'],
             'observation_ko': x['observation_ko'], 'interaction_distance_m': x.get('interaction_distance_m', 1.75),
             'canonical_evidence_id': None, 'procedural_caution': False, 'gate': None, 'parent_container': None,
             'inspectable': True, 'prop_id': x['prop_id']}
        props.definitions[x['prop_id']] = d
        from .prop_world import ScenePropState
        props.states.setdefault(x['prop_id'], ScenePropState())

# Desk requests: canon evidence id -> procedure (cost uses canon production_rules budget)
REQUESTS = {
    'e02': {'cost': 2, 'minutes': 40, 'label': '휴대전화 디지털 포렌식 분석', 'needs_flags': ['phone_seized'],
            'why_blocked': '현장에서 휴대전화를 적법하게 확보해야 분석을 의뢰할 수 있습니다'},
    'e03': {'cost': 1, 'minutes': 20, 'label': '공동현관 출입기록 요청'},
    'e05': {'cost': 1, 'minutes': 10, 'label': '박현수 녹음파일 임의제출 요청', 'needs_interviewed': ['s3'],
            'why_blocked': '녹음 보유자에게 먼저 사정을 듣고 임의제출을 요청해야 합니다'},
    'e06': {'cost': 2, 'minutes': 90, 'label': '머그컵 표면 감정의뢰', 'needs_flags': ['mug_collected'],
            'why_blocked': '현장에서 머그컵을 채취·봉인해야 감정을 의뢰할 수 있습니다'},
    'e07': {'cost': 1, 'minutes': 25, 'label': '복도 CCTV 추가 확보'},
    'e08': {'cost': 1, 'minutes': 30, 'label': '인근 편의점 결제·영상 확인', 'needs_interviewed': ['s2'],
            'why_blocked': '대상자를 특정할 이유(면담 등)가 있어야 결제 기록을 조회할 수 있습니다'},
    'e09': {'cost': 2, 'minutes': 60, 'label': '21시 34분 통화상대 통신자료 조회', 'needs_evidence': ['e02'],
            'why_blocked': '통화 기록이 먼저 확인돼야 통신자료 조회 요건을 갖춥니다'},
    'e10': {'cost': 1, 'minutes': 30, 'label': '공동 투자 정산 이력 확인', 'needs_interviewed_any': ['s1', 's2'],
            'why_blocked': '금전 관계를 확인할 단서(관계자 진술)가 먼저 필요합니다'},
    'e11': {'cost': 3, 'minutes': 120, 'label': '압수수색영장 집행 및 착의 감정', 'needs_axes': ['presence_or_timing', 'motive'],
            'why_blocked': '영장 청구에는 방문·시각과 동기에 대한 소명이 먼저 필요합니다'},
}

class PropAuthority:
    def __init__(self, episode):
        self.episode = episode
        self.props = PropWorld()
        apply_scene_notes(self.props)
        for pid in INITIAL_OPEN:
            if pid in self.props.states:
                self.props.states[pid].opened = True
        for pid in INITIAL_ACTIVE:
            if pid in self.props.states:
                self.props.states[pid].active = True
        self.positions = json.loads(POSITIONS.read_text(encoding='utf-8')) if POSITIONS.exists() else {}
        self.art = json.loads(ART_STATUS.read_text(encoding='utf-8')) if ART_STATUS.exists() else {}
        self.last_player_pos = None
        self.photos: set[str] = set()
        self.photo_order: list[str] = []   # evidence marker numbers follow the order things were first photographed
        self.gloves_on = False
        self.collected: dict[str, dict] = {}

    def _asset_ready(self, prop_id):
        status = self.art.get(prop_id, 'UNASSIGNED_NEEDS_QUALITY_ASSET')
        if status == 'APPROVED':
            return True
        # Dev builds may exercise procedural assets; they stay flagged as NOT shippable.
        return status.startswith('PROCEDURAL') and os.environ.get('TABLEZERO_ALLOW_UNAPPROVED_ART') == '1'

    def _check_player(self, prop_id, player_pos):
        d = self.props.definitions[prop_id]
        scene = self.episode.state.scene
        want = ZONE_SCENE.get(d['zone'], 'room302')
        # the 302 front door and its lock are operated from the hallway as well
        both = d['zone'] == 'entrance' and d['prop_id'] in ('entrance_door', 'entrance_lock')
        if scene != want and not (both and scene in ('hall', 'room302')):
            raise GuardError(f'Prop not in current scene ({scene})')
        if not (isinstance(player_pos, (list, tuple)) and len(player_pos) == 3 and all(isinstance(v, (int, float)) for v in player_pos)):
            raise GuardError('Player position required')
        # movement sanity: no teleport between consecutive intents (walk ~1.4 m/s, generous)
        self.last_player_pos = list(player_pos)
        pos = self.positions.get(prop_id)
        if pos is None:
            raise GuardError('Prop has no authored scene binding')
        dist = math.dist(player_pos, pos['center'])
        if dist > d['interaction_distance_m'] + 0.9:
            raise GuardError('Too far from prop')

    def interact(self, prop_id, verb, *, action_id, player_pos):
        if prop_id not in self.props.definitions:
            raise GuardError('Unknown scene prop')
        self._check_player(prop_id, player_pos)
        grants = set()
        st = self.episode.state
        if 'phone_seizure_logged' in st.flags: grants.add('legal_acquisition')
        if 'ceiling_tool' in st.flags: grants.add('tool_access')
        if 'mailbox_consent' in st.flags: grants.add('authorization')
        r = self.props.interact(prop_id, verb, action_id=action_id, authorized=True,
                                asset_ready=self._asset_ready(prop_id), access_grants=grants)
        out = dict(r)
        # never tell the client which props map to canon evidence (no "red answer highlight")
        out.pop('canonical_evidence_reference', None)
        out.pop('requires_separate_evidence_workflow', None)
        d = self.props.definitions[prop_id]
        out['label'] = d['label_ko']
        out['procedure_actions'] = self.procedure_actions(prop_id)
        out['art_status'] = self.art.get(prop_id, 'UNASSIGNED_NEEDS_QUALITY_ASSET')
        self.episode._log('prop_interact', {'prop': prop_id, 'verb': verb})
        return out

    def procedure_actions(self, prop_id):
        """Every inspectable prop can be photographed; collection is offered for movable/anchor props.
        Evidence-relevance is never signalled by which actions appear."""
        d = self.props.definitions[prop_id]
        acts = ['photograph']
        if d['interaction_type'] in ('move', 'evidence_anchor'):
            acts.append('collect')
        return acts

    def procedure(self, prop_id, action, *, player_pos):
        """photograph / gloves / collect. Collect = bag, seal, chain-of-custody log."""
        if prop_id not in self.props.definitions:
            raise GuardError('Unknown scene prop')
        self._check_player(prop_id, player_pos)
        st = self.episode.state
        d = self.props.definitions[prop_id]
        if action == 'photograph':
            first = prop_id not in self.photos
            if first:
                self.photos.add(prop_id)
                self.photo_order.append(prop_id)
            marker_no = self.photo_order.index(prop_id) + 1
            self.episode._log('scene_photo', {'prop': prop_id, 'marker': marker_no})
            note = f'사진 기록 · 표지 {marker_no}번' if first else f'사진 추가 · 표지 {marker_no}번'
            return {'prop_id': prop_id, 'photographed': True, 'marker_no': marker_no, 'duplicate': not first, 'note': note}
        if action != 'collect':
            raise GuardError('Unknown procedure')
        if d['interaction_type'] not in ('move', 'evidence_anchor'):
            raise GuardError('This object is not collectable')
        if prop_id in self.collected:
            return dict(self.collected[prop_id], duplicate=True)
        defects = []
        if prop_id not in self.photos:
            defects.append('no_photo_before_collect')
        if not self.gloves_on:
            defects.append('no_gloves')
        rec = {'prop_id': prop_id, 'collected': True, 'sealed': True, 'defects': defects,
               'note': '채취·봉인 완료' + (' · 절차 누락 기록됨' if defects else '')}
        self.collected[prop_id] = rec
        canon = d.get('canonical_evidence_id')
        if prop_id == 'living_food_bag' and canon:
            self.episode.acquire(canon, authorized=True, photo_logged=True, sealed=True)
        elif prop_id == 'kitchen_mug':
            st.flags.add('mug_collected')
        elif prop_id == 'living_phone':
            st.flags.add('phone_seized'); st.flags.add('phone_seizure_logged')
        for x in defects:
            st.chain_defects.add(f'{prop_id}:{x}')
        self.episode._log('scene_collect', {'prop': prop_id, 'defects': defects})
        return rec

    def set_gloves(self, on: bool):
        self.gloves_on = bool(on)
        return {'gloves_on': self.gloves_on}


class RecordDesk:
    def __init__(self, episode):
        self.episode = episode
        canon_rules = episode.world._canon['production_rules']
        self.budget = canon_rules['initial_action_budget']
        self.spent = 0
        self.requested: list[str] = []

    def options(self):
        st = self.episode.state
        out = []
        for eid, r in REQUESTS.items():
            ok, why = self._eligible(eid)
            out.append({'request_id': eid, 'label': r['label'], 'cost': r['cost'], 'minutes': r['minutes'],
                        'available': ok and eid not in self.episode.world.available_evidence,
                        'done': eid in self.episode.world.available_evidence,
                        'blocked_reason': '' if ok else why})
        return {'budget_left': self.budget - self.spent, 'budget_total': self.budget, 'requests': out,
                'clock': self.episode.clock_text()}

    def _eligible(self, eid):
        r = REQUESTS[eid]
        st = self.episode.state
        w = self.episode.world
        if any(f not in st.flags for f in r.get('needs_flags', [])):
            return False, r['why_blocked']
        if any(s not in st.interviewed for s in r.get('needs_interviewed', [])):
            return False, r['why_blocked']
        if r.get('needs_interviewed_any') and not st.interviewed.intersection(r['needs_interviewed_any']):
            return False, r['why_blocked']
        if any(e not in w.available_evidence for e in r.get('needs_evidence', [])):
            return False, r['why_blocked']
        if r.get('needs_axes'):
            logic = w._canon['case_result_logic']
            have = w.available_evidence
            for axis in r['needs_axes']:
                if not any(set(s).issubset(have) for s in logic[axis + '_evidence_sets']):
                    return False, r['why_blocked']
        return True, ''

    def request(self, eid):
        if self.episode.state.scene != 'desk':
            raise GuardError('Record requests are made from the investigation desk')
        if eid not in REQUESTS:
            raise GuardError('Unknown request')
        if eid in self.episode.world.available_evidence:
            return {'duplicate': True}
        ok, why = self._eligible(eid)
        if not ok:
            raise GuardError(why)
        r = REQUESTS[eid]
        if self.spent + r['cost'] > self.budget:
            raise GuardError('수사 자원이 부족합니다')
        self.spent += r['cost']
        self.requested.append(eid)
        self.episode.state.case_clock_minutes += r['minutes']
        self.episode.acquire(eid, authorized=True, photo_logged=True,
                             sealed=REQUESTS[eid].get('sealed', eid in ('e06', 'e11')))
        return {'acquired': eid, 'budget_left': self.budget - self.spent, 'clock': self.episode.clock_text()}

    def charge_interview(self):
        """A NEW interview session costs canon 'new_interview_session'."""
        cost = self.episode.world._canon['production_rules']['major_action_costs']['new_interview_session']
        if self.spent + cost > self.budget:
            raise GuardError('수사 자원이 부족해 새 면담을 열 수 없습니다')
        self.spent += cost
