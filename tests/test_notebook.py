import os, unittest, uuid
from server.episode_controller import EpisodeController
from server.interview_service import InterviewService
from server.runtime import GuardError
from server import notebook


class NotebookTests(unittest.TestCase):
    def setUp(self):
        os.environ['TABLEZERO_PERFORMER'] = 'authored'
        self.c = EpisodeController(); self.s = InterviewService(self.c)
        for e in ('V21-E07', 'V21-E18', 'V21-E02', 'V21-E10'): self.c.world.expose_evidence(e)

    def tearDown(self): os.environ.pop('TABLEZERO_PERFORMER', None)

    def test_same_source_family_is_flagged_not_counted_as_independent(self):
        r = notebook.compare(self.c, self.s, 'V21-E07', 'V21-E18')
        self.assertTrue(r['same_source_family']); self.assertIsNone(r['verdict'])
        self.assertTrue(any('독립 근거 두 개로 세지 않습니다' in n for n in r['notes']))

    def test_document_time_is_not_event_time_and_certainty_is_separate(self):
        o = {x['id']: x for x in notebook.observations(self.c)}
        self.assertTrue(o['V21-E10']['time']['note'])                 # DOCUMENT: recorded time != event time
        self.assertIn(o['V21-E07']['time']['certainty'], ('estimated', 'recorded'))

    def test_statements_are_server_built_unverified_and_hypotheses_never_become_facts(self):
        self.c.transition('desk'); self.c.transition('interview'); self.s.begin('s2')
        self.s.ask('그날 302호에 갔습니까?', input_mode='typed', action_id=uuid.uuid4().hex)
        st = notebook.statements(self.c, self.s)
        self.assertEqual(st[0]['actor'], 's2'); self.assertTrue(st[0]['unverified'])
        notebook.add_hypothesis(self.c, '이서연이 21:39에 방문했을 수 있다', ['V21-E02', 'NOT-OWNED'])
        h = self.c.hypotheses[0]; self.assertEqual(h['links'], ['V21-E02']); self.assertEqual(h['status'], 'open')
        self.assertNotIn('V21-E02', [x['id'] for x in notebook.projection(self.c, self.s)['hypotheses']])
        r = notebook.compare(self.c, self.s, 's2#1', 'V21-E02'); self.assertEqual(r['a']['kind'], 'statement')

    def test_unacquired_records_cannot_be_compared_and_requests_hide_results(self):
        with self.assertRaises(GuardError): notebook.compare(self.c, self.s, 'V21-E07', 'V21-E16')
        for item in notebook.to_check(self.c)['requests']:
            self.assertNotIn('detail', item)


if __name__ == '__main__':
    unittest.main()


class SceneObservationTests(unittest.TestCase):
    def setUp(self):
        from tests.test_v11int_case_flow import near
        self.c = EpisodeController(); self.c.transition('room302')
        self.me = near(self.c, 'living_phone'); self.p = self.c.props

    def test_phone_points_are_staged_hinted_and_never_name_a_culprit(self):
        info = self.p.observation_info('living_phone', player_pos=self.me)
        self.assertEqual(info['total'], 3); self.assertEqual(info['done'], 0)
        self.assertTrue(all(pt['label'] == '' for pt in info['points']))          # nothing is pre-highlighted
        h1 = self.p.hint('living_phone', player_pos=self.me)['hint']; h2 = self.p.hint('living_phone', player_pos=self.me)['hint']
        self.assertNotEqual(h1, h2)                                              # hints escalate step by step
        r = self.p.observe('living_phone', 'screen', player_pos=self.me)
        self.assertTrue(r['first']); self.assertIn('알 수 없다', r['text'])
        self.assertFalse(self.p.observe('living_phone', 'screen', player_pos=self.me)['first'])
        for pid in ('lock', 'back'): r = self.p.observe('living_phone', pid, player_pos=self.me)
        self.assertTrue(r['complete'])
        for rec in self.p.scene_observations():
            for bad in ('범인', '박현수가', '이서연이', '강도현이'): self.assertNotIn(bad, rec['text'])

    def test_observation_is_comparable_and_separate_from_records(self):
        self.p.observe('living_phone', 'screen', player_pos=self.me)
        self.c.world.expose_evidence('V21-E07')
        r = notebook.compare(self.c, None, 'obs:living_phone:screen', 'V21-E07')
        self.assertEqual(r['a']['kind'], 'observation'); self.assertFalse(r['same_source_family'])   # external look vs digital data
        self.assertIsNone(r['verdict'])
        self.assertEqual({o['id'] for o in notebook.observations(self.c)}, {'V21-E17', 'V21-E07'})   # records only; the observation lives in scene_observations

    def test_every_other_prop_gets_one_neutral_point(self):
        from tests.test_v11int_case_flow import near
        me = near(self.c, 'kitchen_mug'); info = self.p.observation_info('kitchen_mug', player_pos=me)
        self.assertEqual(info['total'], 1)
