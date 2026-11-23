"""One whole CASE001 investigation through the REAL HTTP API (same endpoints and JSON shape the Unity client uses), with no evidence
grants, no budget edits and no teleport: new case -> scene -> photo/gloves/collect -> close observation -> desk requests (paid from the
real 12-point budget) -> interviews with attached records -> notebook compare -> report v1 -> ending -> new case (clean). Server side only:
the client UI itself is verified separately in Play Mode."""
import json, os, threading, unittest, urllib.request, uuid
from http.server import ThreadingHTTPServer
from server import api
from server.episode_controller import EpisodeController
from tests.test_v11int_case_flow import near

TOKEN = 'x' * 32


class Client:
    def __init__(self, port): self.base = f'http://127.0.0.1:{port}'

    def call(self, path, body=None, method='POST'):
        req = urllib.request.Request(self.base + path, data=None if method == 'GET' else json.dumps(body or {}).encode(), method=method,
                                     headers={'X-TableZero-Dev-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())
        except urllib.error.HTTPError as e: return json.loads(e.read().decode())


class FullPlaythroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['TABLEZERO_PERFORMER'] = 'authored'
        api.LocalBridgeHandler.local_token = TOKEN
        api.LocalBridgeHandler.controller = EpisodeController()
        api.LocalBridgeHandler.interview_service = api.InterviewService(api.LocalBridgeHandler.controller)
        cls.srv = ThreadingHTTPServer(('127.0.0.1', 0), api.LocalBridgeHandler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.c = Client(cls.srv.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); os.environ.pop('TABLEZERO_PERFORMER', None)

    def pos(self, prop):
        return near(api.LocalBridgeHandler.controller, prop)

    def test_complete_investigation_then_clean_new_case(self):
        c = self.c
        nc = c.call('/v1/case/new'); self.assertTrue(nc['ok']); sid = nc['data']['session_id']
        self.assertTrue(c.call('/v1/scene', {'scene': 'room302'})['ok'])
        self.assertTrue(c.call('/v1/player/gloves', {'on': True})['ok'])
        # scene work: photograph -> close observation (staged) -> collect & seal
        for prop in ('living_phone', 'living_food_bag', 'kitchen_mug'):
            self.assertTrue(c.call('/v1/prop/procedure', {'prop_id': prop, 'action': 'photograph', 'player_pos': self.pos(prop)})['ok'], prop)
        pp = self.pos('living_phone')
        self.assertEqual(c.call('/v1/prop/observe_info', {'prop_id': 'living_phone', 'player_pos': pp})['data']['done'], 0)
        for pt in ('screen', 'lock', 'back'): self.assertTrue(c.call('/v1/prop/observe', {'prop_id': 'living_phone', 'point_id': pt, 'player_pos': pp})['data']['first'])
        for prop in ('living_phone', 'living_food_bag', 'kitchen_mug'):
            r = c.call('/v1/prop/procedure', {'prop_id': prop, 'action': 'collect', 'player_pos': self.pos(prop)}); self.assertTrue(r['ok'], r)
            self.assertEqual(r['data']['defects'], [])                          # proper procedure, nothing to penalise
        nb = c.call('/v1/notebook')['data']
        self.assertEqual({o['id'] for o in nb['observations']}, {'V21-E17', 'V21-E06', 'V21-E01'})
        self.assertEqual(len(nb['scene_observations']), 3); self.assertEqual(len(nb['custody']), 3)
        # desk: pay from the real budget; blocked requests say why and cost nothing
        self.assertTrue(c.call('/v1/scene', {'scene': 'desk'})['ok'])
        opts = c.call('/v1/desk/options')['data']; self.assertEqual(opts['budget_left'], 12)
        r = c.call('/v1/desk/request', {'request_id': 'V21-E13'}); self.assertFalse(r['ok'])          # needs an interview of s1 first
        self.assertEqual(c.call('/v1/desk/options')['data']['budget_left'], 12)
        # interview s1 (first interview is free), attach a record only after requesting it
        self.assertTrue(c.call('/v1/desk/request', {'request_id': 'V21-E02'})['ok'])
        self.assertTrue(c.call('/v1/scene', {'scene': 'interview'})['ok'])
        self.assertTrue(c.call('/v1/interview/start', {'suspect_id': 's1'})['ok'])
        a1 = c.call('/v1/interview/ask', {'question': '직장에는 몇 시에 도착했습니까?', 'input_mode': 'typed', 'action_id': uuid.uuid4().hex})
        self.assertIn('9시', a1['data']['suspect_text']); self.assertEqual(a1['data']['performer'], 'AUTHORED_MODE')
        a2 = c.call('/v1/interview/ask', {'question': '방금 직장에 10시 반에 도착했다고 했죠? 집에서는 몇 시에 나왔습니까?', 'input_mode': 'typed', 'action_id': uuid.uuid4().hex})
        self.assertIn('아니', a2['data']['suspect_text']); self.assertIn('9시 반', a2['data']['suspect_text'])
        a3 = c.call('/v1/interview/ask', {'question': '이 영상 보세요. 21시 12분에 들어가셨네요', 'input_mode': 'typed', 'action_id': uuid.uuid4().hex, 'evidence_id': 'V21-E02'})
        self.assertTrue(a3['ok']); self.assertIn(a3['data']['beat'], ('Challenged', 'Guarded', 'Answering'))
        st = c.call('/v1/notebook')['data']['statements']; self.assertEqual(len(st), 3); self.assertTrue(all(s['unverified'] for s in st))
        self.assertTrue(c.call('/v1/interview/end')['ok'])
        self.assertTrue(c.call('/v1/scene', {'scene': 'desk'})['ok'])
        for rid in ('V21-E13', 'V21-E07', 'V21-E18', 'V21-E10', 'V21-E15', 'V21-E16'):
            r = c.call('/v1/desk/request', {'request_id': rid}); self.assertTrue(r['ok'], (rid, r))
        self.assertEqual(c.call('/v1/desk/options')['data']['budget_left'], 1)      # 12 - (1+1+2+2+1+1+3 +0 first interview) ; all earned, none granted
        cmp = c.call('/v1/notebook/compare', {'a': 'V21-E07', 'b': 'V21-E18'})['data']
        self.assertTrue(cmp['same_source_family']); self.assertIsNone(cmp['verdict'])
        # wrong-axis report is NOT a success; the right one is
        ev = {'presence_or_timing': ['V21-E07', 'V21-E18'], 'motive': ['V21-E10'], 'physical_link': ['V21-E16', 'V21-E15'], 'exclude_alternative': ['V21-E13', 'V21-E07']}
        rep = {'schema_version': 1, 'session_id': sid, 'accused_id': 's3', 'confirm': True,
               'axes': {a: {'claim': f'{a} 주장', 'limit_note': '한계', 'evidence_ids': ids} for a, ids in ev.items()}}
        r = c.call('/v1/report', rep); self.assertTrue(r['ok'], r); self.assertEqual(r['data']['ending_code'], 'SOLVED_PROVEN')
        # clean new case: new session, no evidence, no carry-over, report slot open again
        nc2 = c.call('/v1/case/new')['data']
        self.assertNotEqual(nc2['session_id'], sid)
        st2 = c.call('/v1/state', method='GET')['state']
        self.assertEqual(st2['evidence_ids'], ['V21-E17']); self.assertEqual(st2['scene'], 'hall'); self.assertFalse(st2['case_closed'])
        self.assertEqual(c.call('/v1/notebook')['data']['statements'], [])
        old = c.call('/v1/report', rep)                                           # the OLD session's report cannot be filed into the new case
        self.assertFalse(old['ok'])


if __name__ == '__main__':
    unittest.main()
