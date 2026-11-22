"""V21.1 canon lock: the retired v0.4 story is not loaded, guessing the name does not win, and no suspect's starting
prompt carries facts outside their own V21 knowledge projection."""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from server.runtime import World, CANON_PATH
from server.episode_controller import EpisodeController
from server.suspect_mind import build_system_prompt, guard_utterance


class V21CanonTests(unittest.TestCase):
    def setUp(self):
        self.c = EpisodeController(); self.w = self.c.world

    def test_runtime_is_v21_not_legacy(self):
        self.assertIn('v21', str(CANON_PATH))
        self.assertEqual(self.w._canon['case_result_logic']['identity'], 's3')
        self.assertTrue(all(e['id'].startswith('V21-') for e in self.w._canon['evidence']))
        self.assertEqual(len(self.w._canon['evidence']), 19)
        self.assertEqual(len(self.w._canon['truth_events']), 27)

    def test_three_injuries_are_separate_facts(self):
        sep = self.w._canon['truth_server_only']['incident_separation']
        self.assertEqual(len({sep['s1_minor_assault'], sep['s2_palm_cut'], sep['s3_fatal_injury']}), 3)

    def test_name_only_report_fails(self):
        self.assertFalse(self.w.evaluate_report('s3', ('V21-E17',))['sufficient_for_game_report'])

    def test_correct_name_needs_independent_physical_link(self):
        for e in ('V21-E07', 'V21-E18', 'V21-E10', 'V21-E13'):
            self.w.expose_evidence(e)
        # presence + motive + alternatives, but physical link needs two different source families
        self.assertFalse(self.w.evaluate_report('s3', ('V21-E07', 'V21-E18', 'V21-E10', 'V21-E13'))['sufficient_for_game_report'])

    def _prompt(self, sid):
        return build_system_prompt(self.w, sid, presented=set(), climate={}, known_events=[])

    def test_s1_starting_prompt_has_no_later_or_other_facts(self):
        p = self._prompt('s1')
        for w in ('21시 50분', '54분', '밀쳤', '액자', '개인 빚', '손목', '28분'):
            self.assertNotIn(w, p)

    def test_s2_starting_prompt_has_no_post_exit_or_other_facts(self):
        p = self._prompt('s2')
        for w in ('21시 50분', '54분', '밀쳤', '손목', '21시 39분', '49분', '소매', '28분'):
            self.assertNotIn(w, p)

    def test_s3_starting_prompt_hides_own_crime_and_others(self):
        p = self._prompt('s3')
        for w in ('54분', '밀쳤', '모서리', '조각', '개인 빚', '손목', '액자', '28분'):
            self.assertNotIn(w, p)

    def test_innocents_cannot_confess_and_culprit_needs_evidence(self):
        self.assertIn('false_confession_innocent', guard_utterance('s1', '제가 죽였어요', presented=set()))
        self.assertIn('false_confession_innocent', guard_utterance('s2', '제가 밀었어요', presented={'V21-E16', 'V21-E15'}))
        self.assertIn('unearned_confession', guard_utterance('s3', '제가 밀었어요', presented=set()))

    def test_cctv_does_not_claim_the_blind_spot(self):
        e = next(x for x in self.w._canon['evidence'] if x['id'] == 'V21-E02')
        self.assertIn('시야 밖', e['detail'])


    def test_api_main_guard_is_last(self):
        # 'python -m server.api' (how the game starts the server) runs serve() at the guard; anything defined after it
        # is missing at runtime (this broke the evidence list in the game while unit tests passed)
        src = (ROOT / 'server' / 'api.py').read_text(encoding='utf-8').rstrip().splitlines()
        self.assertTrue(src[-1].startswith("if __name__=='__main__'"))


if __name__ == '__main__':
    unittest.main()
