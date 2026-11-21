"""V11 integration tests: playable case flow, knowledge isolation and AI guards (no live model)."""
import os, unittest, uuid
from server.episode_controller import EpisodeController
from server.interview_service import InterviewService
from server.runtime import GuardError
from server.suspect_mind import guard_utterance, build_system_prompt


class Fake:
    label = 'FAKE_TEST_PROVIDER'

    def __init__(self, lines):
        self.lines = list(lines); self.calls = 0; self.last_stats = {}

    def reply(self, ctx):
        self.calls += 1
        line = self.lines.pop(0) if self.lines else '그건 잘 모르겠어요'
        return {'utterance': line, 'reply_mode': 'answer', 'motion_id': ctx['approved_motions'][0],
                'asserted_claim_ids': [], 'new_unsupported_assertion': None, 'request_external_action': None}


def near(c, prop, dx=0.6):
    p = c.props.positions[prop]['center']
    return [p[0] + dx, 1.6, p[2]]


class CaseFlowTests(unittest.TestCase):
    def setUp(self):
        os.environ['TABLEZERO_ALLOW_UNAPPROVED_ART'] = '1'
        self.c = EpisodeController()

    def test_prop_requires_scene_and_distance(self):
        with self.assertRaises(GuardError):  # starts in hall; kitchen prop is not in this scene
            self.c.props.interact('kitchen_fridge_door', 'open', action_id=uuid.uuid4().hex, player_pos=near(self.c, 'kitchen_fridge_door'))
        self.c.transition('room302')
        with self.assertRaises(GuardError):
            self.c.props.interact('kitchen_fridge_door', 'open', action_id=uuid.uuid4().hex, player_pos=near(self.c, 'kitchen_fridge_door', 4.0))

    def test_prop_response_hides_evidence_mapping(self):
        self.c.transition('room302')
        r = self.c.props.interact('kitchen_mug', 'inspect', action_id=uuid.uuid4().hex, player_pos=near(self.c, 'kitchen_mug'))
        self.assertNotIn('canonical_evidence_reference', r)
        self.assertNotIn('e06', str(r))
        r2 = self.c.props.interact('kitchen_spoon', 'inspect', action_id=uuid.uuid4().hex, player_pos=near(self.c, 'kitchen_spoon'))
        self.assertEqual(r['procedure_actions'], r2['procedure_actions'])

    def test_unapproved_art_blocked_without_dev_flag(self):
        os.environ['TABLEZERO_ALLOW_UNAPPROVED_ART'] = '0'
        self.c.transition('room302')
        with self.assertRaises(GuardError):
            self.c.props.interact('kitchen_mug', 'inspect', action_id=uuid.uuid4().hex, player_pos=near(self.c, 'kitchen_mug'))

    def test_fridge_contents_need_open_door(self):
        self.c.transition('room302')
        me = near(self.c, 'kitchen_fridge_door', 0.8)
        with self.assertRaises(GuardError):
            self.c.props.interact('kitchen_fridge_bottle', 'inspect', action_id=uuid.uuid4().hex, player_pos=me)
        self.c.props.interact('kitchen_fridge_door', 'open', action_id=uuid.uuid4().hex, player_pos=me)
        self.c.props.interact('kitchen_fridge_bottle', 'inspect', action_id=uuid.uuid4().hex, player_pos=me)

    def test_collect_without_gloves_marks_defect_and_blocks_acceptance(self):
        self.c.transition('room302')
        self.c.props.procedure('kitchen_mug', 'collect', player_pos=near(self.c, 'kitchen_mug'))
        self.assertTrue(any('no_gloves' in d for d in self.c.state.chain_defects))
        self.c.transition('desk')
        self.c.state.interviewed.update({'s2'})
        for e in ('e07', 'e08', 'e10', 'e06', 'e11'):
            self.c.desk.request(e)
        r = self.c.file_report('s2', ['e01', 'e07', 'e08', 'e10', 'e06', 'e11'], final=True)
        self.assertFalse(r['report_accepted'])

    def test_photo_marker_numbers_follow_first_photo_order(self):
        self.c.transition('room302')
        me = near(self.c, 'kitchen_mug')
        r1 = self.c.props.procedure('kitchen_mug', 'photograph', player_pos=me)
        me2 = near(self.c, 'living_floor_blood')
        r2 = self.c.props.procedure('living_floor_blood', 'photograph', player_pos=me2)
        r3 = self.c.props.procedure('living_floor_blood', 'photograph', player_pos=me2)
        self.assertEqual((r1['marker_no'], r2['marker_no'], r3['marker_no']), (1, 2, 2))
        self.assertFalse(r2['duplicate'])
        self.assertTrue(r3['duplicate'])

    def test_proper_procedure_substantiated(self):
        self.c.transition('room302')
        me = near(self.c, 'kitchen_mug')
        self.c.props.procedure('kitchen_mug', 'photograph', player_pos=me)
        self.c.props.set_gloves(True)
        self.assertEqual(self.c.props.procedure('kitchen_mug', 'collect', player_pos=me)['defects'], [])
        self.c.transition('desk')
        self.c.state.interviewed.update({'s2'})
        for e in ('e07', 'e08', 'e10', 'e06', 'e11'):
            self.c.desk.request(e)
        r = self.c.file_report('s2', ['e01', 'e07', 'e08', 'e10', 'e06', 'e11'], final=True)
        self.assertTrue(r['report_accepted'])

    def test_desk_prerequisites_and_budget(self):
        self.c.transition('desk')
        with self.assertRaises(GuardError): self.c.desk.request('e09')   # needs e02
        with self.assertRaises(GuardError): self.c.desk.request('e11')   # needs presence + motive
        with self.assertRaises(GuardError): self.c.desk.request('e02')   # phone not seized
        self.c.state.flags.add('phone_seized')
        self.c.desk.request('e02'); self.c.desk.request('e09')
        self.assertEqual(self.c.desk.budget - self.c.desk.spent, 8)

    def test_desk_options_never_reveal_identity(self):
        txt = str(self.c.desk.options())
        self.assertNotIn('culprit', txt); self.assertNotIn('이서연', txt)


class MindTests(unittest.TestCase):
    def setUp(self):
        self.c = EpisodeController()

    def test_locked_memories_not_in_context(self):
        sysp = build_system_prompt(self.c.world, 's2', presented=set(), climate={}, known_events=[])
        for w in ('편의점', '21시 39분', '몸싸움', '21시 34분'):
            self.assertNotIn(w, sysp)
        sysp2 = build_system_prompt(self.c.world, 's2', presented={'e08'}, climate={}, known_events=[])
        self.assertIn('편의점', sysp2)

    def test_other_suspect_secrets_never_in_prompt(self):
        allev = {'e01', 'e02', 'e03', 'e05', 'e07', 'e08', 'e09', 'e10'}
        for sid in ('s1', 's2', 's3'):
            sysp = build_system_prompt(self.c.world, sid, presented=allev, climate={'trust_turns': 99}, known_events=[])
            self.assertNotIn('culprit', sysp); self.assertNotIn('truth_server_only', sysp)
            if sid != 's1': self.assertNotIn('한지윤', sysp)
            if sid != 's3': self.assertNotIn('단기 임대', sysp)

    def test_gate_blocks_volunteered_detail(self):
        bad = guard_utterance('s2', '그날 편의점에 잠깐 갔었어요', presented=set(), detective_text='어디 계셨어요?', memories=[])
        self.assertIn('volunteered_concealed_detail', bad)
        ok = guard_utterance('s2', '편의점이요? 그건 기억이 잘', presented=set(), detective_text='편의점 가셨죠?', memories=[])
        self.assertEqual(ok, [])

    def test_unearned_confession_blocked(self):
        self.assertIn('unearned_confession', guard_utterance('s2', '제가 밀었어요', presented={'e08'}))
        self.assertIn('false_confession_innocent', guard_utterance('s1', '제가 죽였어요', presented=set()))

    def test_rejected_generation_not_charged_and_retried(self):
        fake = Fake(['그날 편의점에서 물 샀어요', '저는 집에 있었어요'])
        c = EpisodeController(provider=fake); s = InterviewService(c)
        c.transition('desk'); c.transition('interview'); s.begin('s2')
        r = s.ask('어디 계셨어요?', input_mode='typed', action_id=uuid.uuid4().hex)
        self.assertEqual(r.suspect_text, '저는 집에 있었어요'); self.assertEqual(r.generation_attempts, 2)
        self.assertEqual(r.seconds_left, 900 - 24)

    def test_all_attempts_fail_no_charge(self):
        fake = Fake(['편의점', '편의점 갔어요', '생수 샀어요'])
        c = EpisodeController(provider=fake); s = InterviewService(c)
        c.transition('desk'); c.transition('interview'); s.begin('s2')
        with self.assertRaises(GuardError):
            s.ask('어디 계셨어요?', input_mode='typed', action_id=uuid.uuid4().hex)
        self.assertEqual(s.tactics.state('s2').seconds_left, 900)

    def test_autonomy_reaches_s3_memory_only(self):
        fake = Fake(['그건 회사 일이었어요'])
        c = EpisodeController(provider=fake); s = InterviewService(c)
        c.world.expose_evidence('e09')
        c.transition('desk'); c.transition('interview'); s.begin('s2')
        s.ask('21시 34분 통화 상대가 이서연 씨예요', input_mode='typed', action_id=uuid.uuid4().hex, presented_evidence='e09')
        ev = s.close()
        self.assertIsNotNone(ev)
        e = next(x for x in c.world.events if x.event_id == ev)
        self.assertEqual(e.visible_to, {'s2', 's3'})
        self.assertEqual(c.public_state()['visible_events'], [])


if __name__ == '__main__':
    unittest.main()
