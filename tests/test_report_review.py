import unittest
from server.episode_controller import EpisodeController
from server.runtime import GuardError

PL = ('presence_or_timing', 'motive', 'physical_link', 'exclude_alternative')


def payload(c, accused, axes, session=None):
    return {'schema_version': 1, 'session_id': session or c.session_id, 'accused_id': accused, 'confirm': True,
            'axes': {a: {'claim': t, 'evidence_ids': e} for a, (t, e) in axes.items()}}


class ReportReviewTests(unittest.TestCase):
    def setUp(self):
        self.c = EpisodeController()
        for e in self.c.world._canon['evidence']:
            self.c.world.expose_evidence(e['id'])
        self.c.transition('desk')

    GOOD = {'presence_or_timing': ('t', ['V21-E07', 'V21-E18']), 'motive': ('m', ['V21-E10']),
            'physical_link': ('p', ['V21-E16', 'V21-E15']), 'exclude_alternative': ('x', ['V21-E13', 'V21-E07'])}

    def file(self, axes, accused='s3', session=None):
        return self.c.file_report(accused, [], final=True, report=payload(self.c, accused, axes, session))

    def test_per_axis_evidence_succeeds(self):
        self.assertEqual(self.file(self.GOOD)['ending_code'], 'SOLVED_PROVEN')

    def test_same_union_on_the_wrong_axes_does_not_succeed(self):
        # every needed record is attached, but to the wrong axis -> the old union logic would pass; per-axis must not
        bad = {'presence_or_timing': ('t', ['V21-E10']), 'motive': ('m', ['V21-E07', 'V21-E18']),
               'physical_link': ('p', ['V21-E13', 'V21-E07']), 'exclude_alternative': ('x', ['V21-E16', 'V21-E15'])}
        r = self.file(bad)
        self.assertEqual(r['ending_code'], 'CORRECT_UNPROVEN')
        self.assertTrue(r['missing_proof_axes'])

    def test_physical_link_needs_two_source_families(self):
        one = dict(self.GOOD); one['physical_link'] = ('p', ['V21-E10', 'V21-E15', 'V21-E10'][:2] and ['V21-E15', 'V21-E09'])
        # E15 (SCENE_IMPACT) + E09 (MEDICAL) are different families but not a listed set -> unproven, not an error
        r = self.file(one)
        self.assertIn('physical_link', r['missing_proof_axes'])

    def test_empty_claim_or_axis_rejected_before_judgement(self):
        for mutate in (lambda a: a.update(motive=('   ', ['V21-E10'])), lambda a: a.update(motive=('m', [])), lambda a: a.pop('motive')):
            axes = dict(self.GOOD); mutate(axes)
            c = EpisodeController()
            for e in c.world._canon['evidence']: c.world.expose_evidence(e['id'])
            c.transition('desk')
            with self.assertRaises(GuardError):
                c.file_report('s3', [], final=True, report=payload(c, 's3', axes))
            self.assertFalse(c.state.closed)   # a rejected form must not close the case

    def test_unacquired_evidence_and_stale_session_rejected(self):
        c = EpisodeController(); c.transition('desk')
        with self.assertRaises(GuardError):
            c.file_report('s3', [], final=True, report=payload(c, 's3', self.GOOD))
        with self.assertRaises(GuardError):
            self.file(self.GOOD, session='old-session')

    def test_legacy_union_payload_cannot_name_an_accused(self):
        with self.assertRaises(GuardError):
            self.c.file_report('s3', ['V21-E07'], final=True)
        self.assertEqual(self.c.file_report(None, [], final=True)['ending_code'], 'UNRESOLVED')


if __name__ == '__main__':
    unittest.main()


class CollectEvidenceTests(unittest.TestCase):
    """TZ-QA-004: collecting the delivery bag used the pre-V21 id 'e04' and failed with 'Unknown item'."""
    def setUp(self):
        from tests.test_v11int_case_flow import near
        self.near = near
        self.c = EpisodeController(); self.c.transition('room302'); self.c.props.set_gloves(True)

    def test_food_bag_collect_acquires_delivery_record_and_lists_custody(self):
        me = self.near(self.c, 'living_food_bag')
        self.c.props.procedure('living_food_bag', 'photograph', player_pos=me)
        rec = self.c.props.procedure('living_food_bag', 'collect', player_pos=me)
        self.assertTrue(rec['collected'])
        self.assertIn('V21-E01', self.c.world.available_evidence)
        cust = self.c.public_state()['custody']
        self.assertEqual(cust[0]['prop_id'], 'living_food_bag')
        self.assertTrue(cust[0]['sealed'])

    def test_phone_collect_gives_scene_record_and_unlocks_forensics_without_noise(self):
        me = self.near(self.c, 'living_phone')
        self.c.props.procedure('living_phone', 'photograph', player_pos=me)
        self.c.props.procedure('living_phone', 'collect', player_pos=me)
        self.assertIn('V21-E06', self.c.world.available_evidence)
        self.assertIn('phone_seized', self.c.state.flags)

    def test_scene_transition_is_idempotent_and_new_case_has_new_session(self):
        before = self.c.session_id
        self.assertEqual(self.c.transition('room302')['scene'], 'room302')   # re-asserting the current scene is not an error
        self.assertNotEqual(before, EpisodeController().session_id)
