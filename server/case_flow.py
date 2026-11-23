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
    'V21-E02': {'cost': 1, 'minutes': 30, 'label': '공동현관·복도 CCTV 원본 확보', 'sealed': False},
    'V21-E03': {'cost': 1, 'minutes': 15, 'label': '112 신고 녹취 확인'},
    'V21-E04': {'cost': 1, 'minutes': 20, 'label': '복도 환경음 녹음 임의제출 요청', 'needs_interviewed': ['s3'],
                'why_blocked': '녹음 보유자에게 먼저 사정을 듣고 동의를 구해야 합니다'},
    'V21-E05': {'cost': 1, 'minutes': 40, 'label': '피해자 왼팔 의료 소견 확인'},
    'V21-E07': {'cost': 2, 'minutes': 90, 'label': '피해자 휴대전화 디지털 포렌식', 'needs_flags': ['phone_seized'], 'sealed': True,
                'why_blocked': '현장에서 휴대전화를 적법하게 확보해야 분석을 의뢰할 수 있습니다'},
    'V21-E09': {'cost': 2, 'minutes': 120, 'label': '두 부상군 의학적 구별 감정', 'needs_evidence': ['V21-E17'],
                'why_blocked': '구급·병원 기록이 먼저 확보돼야 감정을 의뢰할 수 있습니다'},
    'V21-E10': {'cost': 1, 'minutes': 90, 'label': '정정서·구버전 배송자료 원본 대조'},
    'V21-E11': {'cost': 2, 'minutes': 60, 'label': '공방 계좌·480만원 이체 원본 조회', 'needs_interviewed_any': ['s1', 's2'],
                'why_blocked': '금전 관계를 확인할 단서(관계자 진술)가 먼저 필요합니다'},
    'V21-E12': {'cost': 2, 'minutes': 60, 'label': '21:28 메시지 원본 확인', 'needs_interviewed_any': ['s1', 's3'],
                'why_blocked': '메시지 송수신 당사자에게 먼저 사정을 들어야 합니다'},
    'V21-E13': {'cost': 1, 'minutes': 30, 'label': '강도현 근무지 출입·점검 기록 확인', 'needs_interviewed': ['s1'],
                'why_blocked': '대상자 진술(근무지)이 먼저 있어야 조회 범위를 정할 수 있습니다'},
    'V21-E14': {'cost': 1, 'minutes': 30, 'label': '인근 편의점 결제·영상 확인', 'needs_interviewed': ['s2'],
                'why_blocked': '대상자를 특정할 이유(면담 등)가 있어야 결제 기록을 조회할 수 있습니다'},
    'V21-E15': {'cost': 1, 'minutes': 120, 'label': '탁자·의자·혈흔 현장 재구성 감정'},
    'V21-E16': {'cost': 3, 'minutes': 120, 'label': '압수수색영장 집행·서류 파편/의복 감정', 'sealed': True,
                'needs_axes': ['presence_or_timing', 'motive'],
                'why_blocked': '영장 청구에는 방문·시각과 동기에 대한 소명이 먼저 필요합니다'},
    'V21-E18': {'cost': 2, 'minutes': 60, 'label': '피해자 당일 방문 약속 메시지 확인', 'needs_evidence': ['V21-E07'],
                'why_blocked': '피해자 휴대전화 분석이 먼저 돼야 합니다'},
    'V21-E19': {'cost': 2, 'minutes': 90, 'label': '머그컵 표면 감정의뢰', 'needs_flags': ['mug_collected'], 'sealed': True,
                'why_blocked': '현장에서 머그컵을 채취·봉인해야 감정을 의뢰할 수 있습니다'},
}

PROP_EVIDENCE = {'living_food_bag': 'V21-E01', 'living_phone': 'V21-E06', 'living_photo_frame': 'V21-E08'}
PROP_LABEL_KO = {'living_food_bag': '배달 음식 봉투·영수증', 'living_phone': '피해자 휴대전화', 'living_photo_frame': '깨진 사진 액자',
                 'kitchen_mug': '머그컵', 'xprop_delivery_receipt': '배달 영수증'}
WHY_KO = {'Physical evidence requires scene': '302호 안에서만 채취할 수 있습니다',
          'Evidence provenance/photo record required': '먼저 사진 촬영(C)으로 현장 기록을 남기세요',
          'Physical evidence requires packaging/chain log': '봉인 절차가 필요합니다', 'Unknown item': '등록되지 않은 물건입니다',
          'Starting record already present': '이미 확보된 기록입니다', 'Case closed': '이미 종결된 사건입니다'}


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
        self.observed: dict[str, dict] = {}       # prop_id -> {point_id: record}
        self.hint_level: dict[str, int] = {}

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
        # V21 canon ids (the interaction manifest still carries pre-V21 ids such as e04, which are not evidence in this case)
        v21 = PROP_EVIDENCE.get(prop_id)
        if v21:
            try:
                self.episode.acquire(v21, authorized=True, photo_logged=True, sealed=True)
            except GuardError as e:
                # never leave a half-collected item: undo, tell the player what is missing and how to fix it
                self.collected.pop(prop_id, None)
                raise GuardError('채취하지 못했습니다: ' + self._why_ko(str(e)))
        if prop_id == 'living_phone':
            st.flags.add('phone_seized'); st.flags.add('phone_seizure_logged')
        elif prop_id == 'kitchen_mug':
            st.flags.add('mug_collected')
        for x in defects:
            st.chain_defects.add(f'{prop_id}:{x}')
        self.episode._log('scene_collect', {'prop': prop_id, 'defects': defects})
        return rec

    @staticmethod
    def _why_ko(msg):
        return WHY_KO.get(msg, '조건이 맞지 않습니다')

    def custody(self):
        """Player-facing chain of custody: physical items taken from the scene, kept apart from verified facts."""
        out = []
        for pid, rec in self.collected.items():
            ev = PROP_EVIDENCE.get(pid)
            out.append({'prop_id': pid, 'label': PROP_LABEL_KO.get(pid, pid), 'sealed': rec.get('sealed', False),
                        'photographed': pid in self.photos, 'defects': list(rec.get('defects', [])),
                        'status': '봉인 · 현장 기록 확보' if ev else '봉인 · 감식 의뢰 대기',
                        'evidence_id': ev})
        return out

    # ------------------------------------------------------------------ close observation (hands-on examine)
    def _points(self, prop_id):
        import json as _json, os as _os
        path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'data', 'room302_observation_points.json')
        if not hasattr(PropAuthority, '_POINTS'):
            PropAuthority._POINTS = _json.load(open(path, encoding='utf-8'))['props']
        d = self.props.definitions[prop_id]
        cfg = PropAuthority._POINTS.get(prop_id)
        if cfg: return cfg
        # every other prop gets one short, relevance-neutral point from its own manifest line (no 'this matters' signal)
        return {'label': d['label_ko'], 'intro': '', 'points': [{'id': 'general', 'label': '살펴보기', 'face': 'any', 'text': d.get('observation_ko', ''), 'limit': ''}], 'hints': []}

    def observation_info(self, prop_id, *, player_pos):
        if prop_id not in self.props.definitions: raise GuardError('Unknown scene prop')
        self._check_player(prop_id, player_pos)
        cfg = self._points(prop_id); seen = self.observed.get(prop_id, {})
        return {'prop_id': prop_id, 'label': cfg['label'], 'intro': cfg['intro'], 'total': len(cfg['points']), 'done': len(seen),
                'points': [{'id': p['id'], 'label': p['label'] if p['id'] in seen else '', 'face': p['face'], 'observed': p['id'] in seen} for p in cfg['points']],
                'photographed': prop_id in self.photos}

    def observe(self, prop_id, point_id, *, player_pos):
        if prop_id not in self.props.definitions: raise GuardError('Unknown scene prop')
        self._check_player(prop_id, player_pos)
        cfg = self._points(prop_id)
        pt = next((p for p in cfg['points'] if p['id'] == point_id), None)
        if not pt: raise GuardError('이 물건에는 그런 관찰 지점이 없습니다')
        seen = self.observed.setdefault(prop_id, {})
        first = point_id not in seen
        if first:
            seen[point_id] = {'prop_id': prop_id, 'prop_label': cfg['label'], 'point_id': point_id, 'label': pt['label'], 'text': pt['text'], 'limit': pt['limit'],
                              'clock': self.episode.clock_text(), 'photographed_first': prop_id in self.photos}
            self.episode._log('scene_observe', {'prop': prop_id, 'point': point_id})
        done = len(seen)
        note = '' if prop_id in self.photos else '먼저 현장 사진(C)으로 원위치를 남겨 두면 위치 기록이 보존됩니다'
        return {'point': point_id, 'label': pt['label'], 'text': pt['text'], 'limit': pt['limit'], 'first': first, 'done': done, 'total': len(cfg['points']),
                'complete': done >= len(cfg['points']), 'note': note}

    def hint(self, prop_id, *, player_pos):
        if prop_id not in self.props.definitions: raise GuardError('Unknown scene prop')
        self._check_player(prop_id, player_pos)
        cfg = self._points(prop_id); hints = cfg.get('hints', [])
        seen = len(self.observed.get(prop_id, {}))
        if seen >= len(cfg['points']): return {'hint': '이 물건에서 볼 수 있는 곳은 모두 기록했습니다', 'level': 0}
        lvl = min(self.hint_level.get(prop_id, 0), max(0, len(hints) - 1)) if hints else 0
        self.hint_level[prop_id] = self.hint_level.get(prop_id, 0) + 1
        return {'hint': hints[lvl] if hints else '아직 보지 않은 곳이 있습니다', 'level': lvl + 1}

    def scene_observations(self):
        out = []
        for pid, pts in self.observed.items(): out.extend(pts.values())
        return out

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
                             sealed=REQUESTS[eid].get('sealed', False))
        return {'acquired': eid, 'budget_left': self.budget - self.spent, 'clock': self.episode.clock_text()}

    def charge_interview(self):
        """A NEW interview session costs canon 'new_interview_session'."""
        cost = self.episode.world._canon['production_rules']['major_action_costs']['new_interview_session']
        if self.spent + cost > self.budget:
            raise GuardError('수사 자원이 부족해 새 면담을 열 수 없습니다')
        self.spent += cost
