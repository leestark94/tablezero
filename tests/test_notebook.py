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
