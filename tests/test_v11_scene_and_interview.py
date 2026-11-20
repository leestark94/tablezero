import unittest,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from server.prop_world import PropWorld,MANIFEST
from server.episode_controller import EpisodeController
from server.interview_service import InterviewService
from server.runtime import GuardError
from server.providers import PreviewProvider
from server.speech_adapter import validate_wav,SpeechNotReady

class PropTests(unittest.TestCase):
    def setUp(self):self.p=PropWorld()
    def test_all_ids_unique(self):
        raw=json.loads(MANIFEST.read_text('utf-8'))['props']
        self.assertEqual(len(raw),140)
        self.assertEqual(len(raw),len(self.p.definitions))
    def test_every_observation_authored(self):
        for p in self.p.definitions.values():
            self.assertGreater(len(p['observation_ko']),10)
            self.assertTrue(p['asset_status'].startswith('UNASSIGNED'))
            self.assertTrue(p['inspectable'])
    def test_no_case_truth_in_props(self):
        raw=MANIFEST.read_text('utf-8')
        for k in ['culprit_id','truth_server_only','case_result_logic']:
            self.assertNotIn(k,raw)
    def test_missing_authority_blocked(self):
        with self.assertRaises(GuardError):
            self.p.interact('bath_bath_door','open',action_id='case-interact-00001',asset_ready=True)
    def test_missing_asset_blocked(self):
        with self.assertRaises(GuardError):
            self.p.interact('bath_bath_door','open',action_id='case-interact-00002',authorized=True)
    def test_open_room_and_close(self):
        a=self.p.interact('bath_bath_door','open',action_id='case-interact-00003',authorized=True,asset_ready=True)
        self.assertTrue(a['opened']);self.assertFalse(a['evidence_acquired'])
        b=self.p.interact('bath_bath_door','close',action_id='case-interact-00004',authorized=True,asset_ready=True)
        self.assertFalse(b['opened'])
    def test_parent_blocks(self):
        self.assertIsNone(self.p.public_target('kitchen_fridge_bottle',zone='kitchen'))
        with self.assertRaises(GuardError):
            self.p.interact('kitchen_fridge_bottle','inspect',action_id='case-interact-00005',authorized=True,asset_ready=True)
        self.p.interact('kitchen_fridge_door','open',action_id='case-interact-00006',authorized=True,asset_ready=True)
        self.assertIsNotNone(self.p.public_target('kitchen_fridge_bottle',zone='kitchen'))
        self.assertFalse(self.p.interact('kitchen_fridge_bottle','inspect',action_id='case-interact-00007',authorized=True,asset_ready=True)['evidence_acquired'])
    def test_inspect_no_evidence_acquired(self):
        r=self.p.interact('living_phone','inspect',action_id='case-interact-00008',authorized=True,asset_ready=True)
        self.assertEqual(r['canonical_evidence_reference'],'e02')
        self.assertFalse(r['evidence_acquired'])
        self.assertFalse(r['verified_fact_created'])
    def test_permission_gate(self):
        with self.assertRaises(GuardError):
            self.p.interact('hall_mailbox','open',action_id='case-interact-00009',authorized=True,asset_ready=True)
        r=self.p.interact('hall_mailbox','open',action_id='case-interact-00010',authorized=True,asset_ready=True,access_grants=['authorization'])
        self.assertTrue(r['opened'])
    def test_switch_toggle(self):
        self.assertTrue(self.p.interact('bath_light_switch','activate',action_id='case-interact-00011',authorized=True,asset_ready=True)['active'])
        self.assertFalse(self.p.interact('bath_light_switch','deactivate',action_id='case-interact-00012',authorized=True,asset_ready=True)['active'])
    def test_duplicate_idempotent(self):
        a=self.p.interact('entrance_mat','inspect',action_id='case-interact-00013',authorized=True,asset_ready=True)
        b=self.p.interact('entrance_mat','inspect',action_id='case-interact-00013',authorized=True,asset_ready=True)
        self.assertEqual(a,b);self.assertEqual(self.p.states['entrance_mat'].inspected,1)
    def test_duplicate_conflict(self):
        self.p.interact('entrance_mat','inspect',action_id='case-interact-00014',authorized=True,asset_ready=True)
        with self.assertRaises(GuardError):
            self.p.interact('entrance_shoes1','inspect',action_id='case-interact-00014',authorized=True,asset_ready=True)
    def test_prop_coverage_explicitly_blocked(self):
        report=self.p.audit(scene_ids=[],verified_ids=[])
        self.assertEqual(report['declared'],140)
        self.assertTrue(report['ship_blocked'])
        self.assertEqual(len(report['missing_scene_bindings']),140)
    def test_scene_zone_hidden(self):
        self.assertIsNone(self.p.public_target('bath_sink',zone='sleep'))

class InterviewTests(unittest.TestCase):
    def setUp(self):
        self.c=EpisodeController(provider=PreviewProvider())
        self.c.transition('desk');self.c.transition('interview')
        self.s=InterviewService(self.c)
        self.s.begin('s2')
    def test_free_text_costs_only_after_reply(self):
        r=self.s.ask('어제 몇 시에 통화하셨어요?',input_mode='typed',action_id='interview-txt-00001')
        self.assertEqual(r.seconds_spent,24)
        self.assertEqual(r.seconds_left,876)
        self.assertEqual(len(self.c.world.claims),1)
    def test_recommended_cheaper(self):
        r=self.s.ask('그 시간은 어떻게 기억하세요?',input_mode='suggested',action_id='interview-rec-00001')
        self.assertEqual(r.seconds_spent,14)
    def test_voice_cost_equal_to_free(self):
        r=self.s.ask('몇 시에 전화했는지 기억하세요?',input_mode='voice',action_id='interview-voc-00001',transcript_confirmed=True)
        self.assertEqual(r.seconds_spent,24)
    def test_voice_not_confirmed_free(self):
        with self.assertRaises(GuardError):
            self.s.ask('방금 뭐라고 하셨어요?',input_mode='voice',action_id='interview-voc-00002',transcript_confirmed=False)
        self.assertEqual(self.s.tactics.public_state('s2')['seconds_left'],900)
    def test_rejected_evidence_free(self):
        with self.assertRaises(GuardError):
            self.s.ask('이 증거 보이세요?',input_mode='typed',action_id='interview-ev-00001',presented_evidence='e11')
        self.assertEqual(self.s.tactics.public_state('s2')['seconds_left'],900)
    def test_inference_time_unbilled(self):
        class Broken:
            label='BROKEN'
            def reply(self,ctx):raise RuntimeError('Network not working')
        self.c.provider.provider=Broken()
        with self.assertRaises(RuntimeError):
            self.s.ask('통화 기록은요?',input_mode='typed',action_id='interview-bad-00001')
        self.assertEqual(self.s.tactics.public_state('s2')['seconds_left'],900)
    def test_no_double_charge_on_retry(self):
        a=self.s.ask('어제 몇 시에 통화하셨어요?',input_mode='typed',action_id='interview-dup-00001')
        b=self.s.ask('어제 몇 시에 통화하셨어요?',input_mode='typed',action_id='interview-dup-00001')
        self.assertEqual(a,b)
        self.assertEqual(self.s.tactics.public_state('s2')['seconds_left'],876)
    def test_retry_change_rejected(self):
        self.s.ask('통화하셨죠?',input_mode='typed',action_id='interview-dup-00002')
        with self.assertRaises(GuardError):
            self.s.ask('방문하셨죠?',input_mode='typed',action_id='interview-dup-00002')
    def test_no_answer_leak_in_response(self):
        r=self.s.ask('사건 당일 통화는 했나요?',input_mode='typed',action_id='interview-safe-0001')
        self.assertNotIn('culprit_id',str(r))
        self.assertFalse(r.claims_verified)
    def test_not_in_live_interview_rejected(self):
        self.s.close()
        with self.assertRaises(GuardError):
            self.s.ask('다시 묻겠습니다',input_mode='typed',action_id='interview-closed-01')

class SpeechTests(unittest.TestCase):
    def test_empty_not_transcript(self):
        with self.assertRaises(SpeechNotReady):validate_wav(b'')
    def test_wav_header_not_enough(self):
        with self.assertRaises(SpeechNotReady):validate_wav(b'RIFFbadheader')
if __name__=='__main__':unittest.main()
