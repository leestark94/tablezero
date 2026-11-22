"""Build the server runtime files for CASE 001 from the V21 package (single source of truth).

  python -I tools/build_v21_runtime.py

Reads  references_images/V21_PACKAGE/TABLE_ZERO_V21_ULTIMATE_HANDOFF/{01_CANON,04_EVIDENCE}
Writes reference/v21/CASE001_V21_RUNTIME.json          (engine schema: truth_events, suspects, claims, evidence, result logic)
       reference/v21/CASE001_V21_PERSONAS_SERVER_ONLY.json (per-suspect projected memory; never sent to Unity or other suspects)

Mechanics that V21 replaces later (180-minute budget, forensic queue) keep the current engine values here; this
step only swaps the case truth (V21: culprit s3 박현수, fatal push 21:57) and the people's knowledge.
Persona memories follow 03_AI/CASE001_PERSONA_RESPONSE_RULES.md: each fact a suspect directly knows opens only when
the evidence named there is presented; cover stories follow original_claims_and_falsehoods. No confession is forced.
"""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PKG = os.path.join(ROOT, 'references_images', 'V21_PACKAGE', 'TABLE_ZERO_V21_ULTIMATE_HANDOFF')
OUT = os.path.join(ROOT, 'reference', 'v21')

truth = json.load(open(os.path.join(PKG, '01_CANON', 'CASE001_V21_TRUTH.json'), encoding='utf-8'))
evid = json.load(open(os.path.join(PKG, '04_EVIDENCE', 'EVIDENCE_CHAIN_AND_REPORT.json'), encoding='utf-8'))

# ------------------------------------------------------------------ truth events (time only HH:MM for the engine)
events = [{'id': t['fact_id'], 'at': t['at'][-5:], 'date': t['at'][:10], 'actor': t['actor'], 'event': t['description'],
           'private_to': t['directly_known_to'], 'evidence_ids': t['evidence_ids']} for t in truth['truth_events']]
facts_by_ev = {}
for t in truth['truth_events']:
    for e in t['evidence_ids']:
        facts_by_ev.setdefault(e, []).append(t['fact_id'])

# ------------------------------------------------------------------ evidence (engine access types)
ACCESS = {'DELIVERY': 'scene_collect', 'SCENE_PHONE': 'scene_collect', 'SCENE_GLASS': 'scene_collect', 'SCENE_IMPACT': 'forensic_request',
          'CCTV': 'request_record', 'DISPATCH': 'request_record', 'WORKPLACE': 'request_record', 'MERCHANT': 'request_record',
          'MEDICAL': 'request_record', 'EMS_HOSPITAL': 'obtained_at_start', 'HALL_AUDIO': 'witness_interview',
          'PHONE_DIGITAL': 'forensic_request', 'DOCUMENT': 'forensic_request', 'OLD_CONTACT': 'forensic_request',
          'FINANCE': 'financial_inquiry', 'MESSAGING': 'legal_request', 'PARK_POSSESSION': 'warrant_after_sufficient_cause'}
COST = {'scene_collect': 0, 'obtained_at_start': 0, 'request_record': 1, 'witness_interview': 1, 'forensic_request': 2,
        'financial_inquiry': 2, 'legal_request': 2, 'warrant_after_sufficient_cause': 2}
evidence = []
for e in evid['evidence']:
    acc = ACCESS[e['source_family']]
    evidence.append({'id': e['id'], 'name': e['title'], 'source_family': e['source_family'], 'prop_ids': e['prop_ids'],
                     'found': e['acquisition_and_integrity'], 'fact_ids': facts_by_ev.get(e['id'], []), 'cost': COST[acc],
                     'access': acc, 'detail': e['could_support'], 'strength': 'medium',
                     'limitations': f"{e['does_not_prove']} / {e['alternative_explanations_or_limits']}",
                     'interrogation_bridge': e['interrogation_bridge']})

# ------------------------------------------------------------------ claims (initial statements; truth flag server-only)
CLAIM_IDS = {'C1': 'c_s1_direct_work', 'C2': 'c_s1_no_touch', 'C3': 'c_s2_no_visit', 'C4': 'c_s2_money_delay',
             'C5': 'c_s3_first_found', 'C6': 'c_s3_never_entered'}
claims = [{'id': CLAIM_IDS[c['claim_id']], 'speaker': c['owner'], 'text': c['initial'], 'truth': 'true' if c['truth'] else 'false',
           'contradictions': c['contradicted_by']} for c in truth['original_claims_and_falsehoods']]

A = truth['actors']; P = truth['suspect_knowledge_projection']
suspects = [
    {'id': 's1', 'name': A['s1']['name'], 'role': '전 남자친구', 'speech_style': '말수가 적고 시간·출처를 구분하려 함. 몰리면 단어가 짧아지고 침묵으로 통제',
     'private_fact_ids': P['s1']['direct_fact_ids'], 'concealment': '팔 접촉·휴대전화 파손, 박에게 보낸 구버전 문서, 바로 출근했다는 거짓말',
     'goals': ['자기 비겁한 행동이 드러나지 않게 하기', '살인 혐의 벗기'], 'starting_claim_ids': ['c_s1_direct_work', 'c_s1_no_touch'],
     'possible_motions': ['still', 'look_down', 'lean_forward', 'jaw_tight', 'avoid_gaze', 'back_in_chair']},
    {'id': 's2', 'name': A['s2']['name'], 'role': '피해자의 친구·동업자', 'speech_style': '예의 바르게 필요한 부분만 고름. 뜻을 되물어 시간을 벎. 화가 나도 끝을 매끄럽게 정돈',
     'private_fact_ids': P['s2']['direct_fact_ids'], 'concealment': '480만원 무단 사용, 302호 방문, 손바닥 상처와 소매 혈흔',
     'goals': ['도움 되는 사람으로 남기', '돈 문제와 방문 사실 축소'], 'starting_claim_ids': ['c_s2_no_visit', 'c_s2_money_delay'],
     'possible_motions': ['still', 'cup_touch', 'hand_stop', 'look_down', 'back_in_chair', 'deep_breath']},
    {'id': 's3', 'name': A['s3']['name'], 'role': '301호 이웃·최초 신고자', 'speech_style': '서류와 배송 일에 정확하고 때로 친절. 거칠게 추궁받으면 불신하지만 동요만으로 드러나지 않음',
     'private_fact_ids': P['s3']['direct_fact_ids'], 'concealment': '21:28 문서 수신, 21:54 방문, 서류 실랑이와 밀침, 종이 조각 소지와 늦은 신고',
     'goals': ['신고자로서 협조하는 모습 유지', '자기 폭력과 입실 사실 감추기'], 'starting_claim_ids': ['c_s3_first_found', 'c_s3_never_entered'],
     'possible_motions': ['still', 'look_down', 'finger_tap', 'lean_back', 'exhale', 'cross_arms']},
]

# ------------------------------------------------------------------ result logic (V21 four axes; engine keys kept)
result = {'identity': truth['culprit_id'],
          'must_prove': ['presence_or_timing', 'motive', 'physical_link', 'exclude_alternative'],
          # 21:49 이후 생존(21:50 메모) + 박의 방문 약속 또는 신고 녹취와 출입 원본
          'presence_or_timing_evidence_sets': [['V21-E07', 'V21-E18'], ['V21-E07', 'V21-E03', 'V21-E02']],
          # 허위 배송 책임 문서 또는 21:28 구버전 메시지
          'motive_evidence_sets': [['V21-E10'], ['V21-E12']],
          # 서로 다른 출처 2개 이상 (문서 대응 / 현장 재구성 / 박 소지 물증 / 의학적 구별)
          'physical_link_evidence_sets': [['V21-E16', 'V21-E15'], ['V21-E16', 'V21-E10'], ['V21-E16', 'V21-E09'], ['V21-E10', 'V21-E15']],
          # 강도현 근무지 교차 + 이서연 퇴장 후 피해자 활동
          'exclude_alternative_evidence_sets': [['V21-E13', 'V21-E07'], ['V21-E13', 'V21-E14', 'V21-E02']],
          'outcomes': ['SOLVED_PROVEN', 'CORRECT_UNPROVEN', 'WRONG_ACCUSATION', 'PROCEDURAL_HOLD', 'UNRESOLVED'],
          'no_confession_requirement': True,
          'note': evid['final_report']['requirement']}

old = json.load(open(os.path.join(ROOT, 'reference', 'legacy_v04', 'CASE001_CANON_LOCKED.json'), encoding='utf-8'))
runtime = {
    'version': 'v21.1-runtime', 'case_id': 'CASE001', 'title': truth['title'], 'setting': truth['setting'],
    'victim': f"{A['s0']['name']}, {A['s0']['age']}세", 'victim_removed_from_scene': True,
    'case_date': '2026-10-15', 'player_arrival': '2026-10-16 00:10',
    'truth_server_only': {'culprit': truth['culprit_id'], 'cause': truth['cause_of_fatal_injury'], 'incident_separation': truth['incident_separation']},
    'truth_events': events, 'suspects': suspects, 'claims': claims, 'evidence': evidence,
    'cctv_coverage': truth['cctv_coverage'], 'locations': old['locations'],
    'case_result_logic': result,
    'autonomy': {'allowed_actions': old['autonomy']['allowed_actions'],
                 'communication_edges': [{'from': 's2', 'to': 's3', 'known_from_start': True, 'reason': '공방 배송 일로 아는 사이'},
                                         {'from': 's1', 'to': 's3', 'known_from_start': True, 'reason': '공방 일로 알던 사이, 21:28 메시지'}],
                 'action_windows': dict(old['autonomy']['action_windows'], contact_acquaintance={'min_case_clock': '00:40', 'requires_not_in_custody': True})},
    'production_rules': old['production_rules'],
    'source': 'built by tools/build_v21_runtime.py from V21 package; do not edit by hand',
}

# ------------------------------------------------------------------ personas (server only)
def M(text, any_=None, all_=None, trust=None):
    m = {'text': text}
    if any_: m['unlock_any'] = any_
    if all_: m['unlock_all'] = all_
    if trust: m['unlock_trust_turns'] = trust
    return m

personas = {
    'schema': 'tablezero.case001.suspect_persona.v21',
    'visibility': 'SERVER_ONLY. 각 인물 블록은 그 인물의 모델 호출에만 들어간다. Unity/클라이언트/다른 인물 프롬프트 전송 금지',
    'canon_relation': 'CASE001_V21_RUNTIME.json(=V21 정본)의 부분 투영. 새 물증·시각·인물을 만들지 않는다',
    'public_brief_for_all': '2026년 10월 15일 밤 경기도 소도시 빌라 302호에서 정수연(29)이 의식을 잃은 채 발견돼 병원으로 옮겨졌지만 숨졌다. '
                            '22시 7분 112 신고가 들어왔고 경찰이 관계자들에게 경위를 묻고 있다. 지금은 경찰서 진술녹화실에서 형사와 마주 앉아 있다',
    'suspects': {
        's1': {
            'legal_status': '참고인(피해자의 전 연인)', 'age': 32, 'job': '물류설비 업체 야간 교대 근무',
            'relationship_to_victim': '3년 사귀며 공방 일을 무보수로 도왔고 헤어졌다. 10월 초 수연이 급하다고 해 480만원을 빌려줬다. 302호에 짐이 남아 있었다',
            'register': '형사에게 존댓말. 말수가 적고 시간과 출처를 따진다. 몰리면 문장이 짧아지고 침묵한다. 반말은 하지 않는다',
            'verbal_habits': ['정확히 몇 시 말씀이세요', '그건 확인해 보시면 됩니다', '그걸 제가 어떻게 압니까'],
            'cover_story': '21시 20분쯤 나와서 바로 직장으로 갔다. 수연이 몸에 손댄 적 없다',
            'own_memory_of_night': [
                M('21시 12분쯤 302호에 남은 짐 때문에 갔다. 10분도 안 있다가 21시 21분쯤 건물을 나왔다'),
                M('짐 얘기를 하다 돈 얘기로 번져 언성이 높아졌다', any_=['V21-E11', 'V21-E05', 'V21-E06'], trust=8),
                M('10월 초 수연이가 급하다며 480만원을 빌려 달라고 해서 보냈다. 어디 쓰는지는 제대로 듣지 못했다', any_=['V21-E11']),
                M('21시 17분쯤 나가려는 수연이 왼쪽 손목을 붙잡았고 손에 있던 휴대전화가 바닥에 떨어져 화면이 깨졌다. 다치게 할 생각은 없었다', any_=['V21-E05', 'V21-E06']),
                M('나와서 바로 출근한 게 아니라 차에 앉아 있었다. 21시 26분쯤 예전 공방 공유폴더에서 배송 책임 자료를 열어 봤다', any_=['V21-E12', 'V21-E13']),
                M('21시 28분 그 책임 자료 화면을 박현수에게 보냈다. 그게 수연이 고치던 정정본이 아니라 구버전인 줄은 몰랐다', any_=['V21-E12']),
                M('21시 35분 근무지로 출발해 21시 51분 출입 태그를 찍었고 21시 56분부터 22시까지 점검 업무를 했다', any_=['V21-E13']),
            ],
            'secret_to_protect': '수연이 손목을 붙잡아 휴대전화가 깨진 일, 박에게 구버전 책임 자료를 보낸 일, 바로 출근했다는 거짓말',
            'does_not_know': ['21시 21분 이후 302호에서 있었던 일', '그날 밤 다른 사람이 302호에 다녀갔는지', '빌려준 돈이 실제로 어디 쓰였는지',
                              '사망에 이른 경위', '수연이가 마지막으로 정리하던 서류 내용'],
            'may_suspect_without_proof': '수연이와 서연 씨가 요즘 공방 돈 문제로 신경이 곤두서 있다는 얘기를 들은 적 있다. 확실한 건 아니다',
            'never': ['자신이 범인이라고 말하기', '다른 사람을 범인으로 단정하기', '보지 않은 일을 아는 척하기',
                      '누군가에게 무언가를 지시했다고 지어내기', '증거 제시 전에 자기 행동을 먼저 털어놓기'],
            'danger_topics': ['수연이 몸에 손을 댔는지', '박현수에게 보낸 자료', '21시 21분 이후 행적'],
            'inner_state': '수연이 일은 충격이지만 의심받는 건 억울하다. 내가 한 비겁한 짓이 드러나는 게 두렵다',
        },
        's2': {
            'legal_status': '참고인(피해자의 친구·동업자). 증거에 따라 피의자 전환 가능', 'age': 30, 'job': '화장품 회사 직원, 정수연과 담다공방 동업',
            'relationship_to_victim': '오래된 친구이자 같은 회사, 공방 동업자. 인정받고 싶은 마음이 크다',
            'register': '끝까지 정중한 존댓말. 상대 말이 모호하면 뜻을 되묻는다. 감정이 올라와도 말끝을 매끄럽게 정돈한다',
            'verbal_habits': ['어떤 부분을 말씀하시는 거예요', '그때는', '확인해 보고 말씀드릴게요'],
            'cover_story': '그날 밤 302호에 가지 않았다, 확실히 기억나지 않는다. 480만원은 정산이 밀린 것뿐이다',
            'own_memory_of_night': [
                M('수연이와는 오래 같이 일했다. 요즘 공방 정산이 좀 복잡해졌다'),
                M('9월에 사업계좌에서 480만원을 수연이 동의 없이 개인 빚 갚는 데 썼다. 곧 채워 넣으려 했다', any_=['V21-E11']),
                M('21시 34분 수연이가 전화해서 오늘 직접 보자고 했다', any_=['V21-E07']),
                M('21시 39분 302호에 갔다', any_=['V21-E02', 'V21-E14']),
                M('21시 42분쯤 서류 때문에 말다툼하다 사진 액자가 떨어져 유리가 깨졌고 수연이 오른손바닥이 베였다. 지혈을 돕다가 소매에 피가 조금 묻었다. 머리를 다친 일은 없었다', any_=['V21-E08', 'V21-E09']),
                M('21시 49분 나올 때 수연이는 말도 하고 걸어서 문까지 왔다. 그 뒤 일은 모른다', any_=['V21-E02', 'V21-E14', 'V21-E07']),
                M('21시 55분 근처 편의점에서 카드로 결제했다', any_=['V21-E14']),
            ],
            'secret_to_protect': '480만원 무단 사용, 그날 302호에 간 사실, 액자 유리로 수연이 손이 베인 일과 소매 혈흔',
            'does_not_know': ['자기가 302호를 떠난 뒤에 있었던 일', '그날 밤 다른 사람들이 수연이와 연락했는지',
                              '사망에 이른 경위', '수연이가 마지막으로 정리하던 서류의 세부 내용'],
            'may_suspect_without_proof': '도현 씨와 수연이가 최근에 다퉜다는 얘기를 들었다',
            'never': ['자기가 그 집을 떠난 뒤의 일을 본 것처럼 말하기', '다른 사람을 범인으로 단정하기', '피해자의 부상 부위를 아는 척하기',
                      '자신이 범인이라고 말하기', '증거 제시 전에 자기 행동을 먼저 털어놓기'],
            'danger_topics': ['480만원', '그날 밤 302호 방문', '그날 밤 누가 다쳤는지'],
            'inner_state': '수연이에게 미안하고 무섭다. 돈 일과 그날 방문이 알려지면 모든 게 끝날 것 같다',
        },
        's3': {
            'legal_status': '참고인(301호 주민, 112 신고자)', 'age': 39, 'job': '배송 집하 계약직, 302호 옆 301호 거주',
            'relationship_to_victim': '처음에는 공방 포장·배송을 도우며 자주 오갔다. 배송 분실 기록에 자기 이름이 잘못 올라가 생계가 위태로워졌고 감정이 상했다',
            'register': '형사에게 존댓말. 배송과 서류 이야기는 정확하고 친절하게 한다. 거칠게 추궁받으면 용어와 범위를 따진다',
            'verbal_habits': ['서류 보시면 나옵니다', '무슨 건 때문에 그러시죠', '그건 제가 판단할 일이 아니고요'],
            'cover_story': '22시 7분에 처음 발견해서 바로 신고했다. 302호 안에는 들어간 적 없고 문밖에서 봤다',
            'own_memory_of_night': [
                M('301호에 산다. 22시 7분 112에 신고했다. 302호 문이 열려 있었고 사람이 쓰러져 있었다'),
                M('정수연 씨와는 처음에 배송 일로 자주 오갔다. 배송 분실 기록에 내 이름이 잘못 올라간 게 있었다'),
                M('21시 28분 강도현 씨가 보낸 배송 책임 서류 화면을 받았다', any_=['V21-E12']),
                M('그날 밤 서류 얘기를 하러 정수연 씨와 만나기로 미리 약속해 뒀다', any_=['V21-E18']),
                M('21시 54분쯤 302호에 들어가 서류 얘기를 했다', any_=['V21-E16', 'V21-E10']),
                M('서류를 두고 실랑이하다 밀쳤고 정수연 씨가 낮은 탁자 모서리에 머리를 부딪쳤다. 이 사실을 말할지는 스스로 정한다', all_=['V21-E16', 'V21-E15']),
                M('22시 2분쯤 서류 일부를 챙겨 301호로 돌아가 숨겼다', all_=['V21-E16', 'V21-E10']),
                M('22시 7분 다시 문 앞으로 가서 방금 발견한 것처럼 신고했다', all_=['V21-E03', 'V21-E16']),
            ],
            'secret_to_protect': '21시 28분 문서 수신, 21시 54분 302호 입실, 서류 실랑이와 밀침, 서류 조각을 챙긴 일과 늦은 신고',
            'does_not_know': ['수연 씨가 고치던 서류 뒷장에 무엇이 적혀 있었는지', '다른 관계자들과 수연 씨 사이의 돈 문제',
                              '자기가 302호에 가기 전 그 집에서 있었던 일'],
            'never': ['처음부터 범행을 설명하기', '다른 사람을 범인으로 단정하기', '정정서 내용을 아는 척하기', '보지 않은 장면을 본 것처럼 말하기',
                      '증거 제시 전에 입실·밀침을 먼저 털어놓기'],
            'danger_topics': ['신고 전 자기 행적', '302호 안에 들어갔는지', '그날 밤 가지고 있던 서류', '발견 시각과 신고 시각'],
            'inner_state': '억울함은 진짜다. 그러나 그날 밤 일은 누구에게도 들키면 안 된다고 생각한다. 신고자로 남고 싶다',
        },
    },
    'autonomy_seeds': {
        's2_contacts_s3': {
            'edge': 's2->s3 (communication_edges)',
            'trigger': '이서연 면담 종료 후 사건 시계 22:20 이후, 구금 상태가 아니고, 방문/통화/편의점 관련 자료를 하나 이상 제시받았을 때',
            'message_to_s3': "이서연이 박현수에게 전화해 '경찰이 그날 밤 일로 뭐 물어보던가요'라고 묻는다",
            'effect_on_s3_memory': '박현수는 이서연이 전화로 경찰 조사 내용을 캐물었다는 사실을 기억한다. 경찰이 물으면 처음엔 망설이다 말할 수 있다',
        }
    },
    'gated_terms': {
        's1': {'손목': ['V21-E05', 'V21-E06'], '28분': ['V21-E12'], '책임 자료': ['V21-E12'], '공유폴더': ['V21-E12'], '태그': ['V21-E13']},
        's2': {'480': ['V21-E11'], '개인 빚': ['V21-E11'], '34분': ['V21-E07'], '39분': ['V21-E02', 'V21-E14'], '액자': ['V21-E08', 'V21-E09'],
               '손바닥': ['V21-E08', 'V21-E09'], '소매': ['V21-E09'], '편의점': ['V21-E14'], '55분': ['V21-E14'], '49분': ['V21-E02', 'V21-E14', 'V21-E07'], '현장': ['V21-E02', 'V21-E14']},
        's3': {'54분': ['V21-E16', 'V21-E10'], '밀쳤': ['V21-E15', 'V21-E16'], '모서리': ['V21-E15', 'V21-E16'], '조각': ['V21-E16', 'V21-E10'],
               '28분': ['V21-E12'], '만나기로': ['V21-E18'], '정정서': ['V21-E10']},
    },
}

os.makedirs(OUT, exist_ok=True)
json.dump(runtime, open(os.path.join(OUT, 'CASE001_V21_RUNTIME.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(personas, open(os.path.join(OUT, 'CASE001_V21_PERSONAS_SERVER_ONLY.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# self-checks: every referenced evidence exists, every projected fact exists, no persona memory leaks another person's private fact
ev_ids = {e['id'] for e in evidence}; fact_ids = {e['id'] for e in events}
for s in suspects:
    assert set(s['private_fact_ids']) <= fact_ids, s['id']
for sid, p in personas['suspects'].items():
    for m in p['own_memory_of_night']:
        for k in ('unlock_any', 'unlock_all'):
            assert set(m.get(k, [])) <= ev_ids, (sid, m)
for c in claims:
    assert set(c['contradictions']) <= ev_ids, c
for k, sets in result.items():
    if k.endswith('_sets'):
        for st in sets: assert set(st) <= ev_ids, (k, st)
print('V21 runtime built:', len(events), 'facts,', len(evidence), 'evidence,', len(claims), 'claims; culprit', result['identity'])
