import unittest
from server.strategy import pick_motion, pick_beat, MOTION_PREF

AVAILABLE = ['still', 'cup_touch', 'finger_tap', 'look_down', 'back_in_chair', 'chair_shift', 'lean_forward', 'jaw_tight', 'cross_arms', 'exhale', 'hand_stop', 'deep_breath', 'lean_back']


class PerformanceTests(unittest.TestCase):
    def test_same_tactic_does_not_always_produce_the_same_gaze_aversion(self):
        seq = [pick_motion('DENY', AVAILABLE, v) for v in range(12)]
        self.assertGreaterEqual(len(set(seq)), 4)                      # varies turn to turn
        self.assertLess(seq.count('look_down') / len(seq), 0.34)        # a denial is NOT 'look away' by default

    def test_beat_depends_on_what_the_detective_did_not_on_truth(self):
        # a denial of a fact the suspect did commit and one they did not are the same tactic => same beat
        truthful = {'tactic': 'DENY', 'accused': False, 'pressed': False, 'accusations': 0}
        lying = {'tactic': 'DENY', 'accused': False, 'pressed': False, 'accusations': 0, 'focus': 'visit'}
        self.assertEqual(pick_beat(truthful, None), pick_beat(lying, None))
        self.assertEqual(pick_beat({'tactic': 'DENY', 'accused': True, 'accusations': 2}, None)[0], 'Guarded')    # accusation => guarded
        self.assertEqual(pick_beat({'tactic': 'DENY'}, 'V21-E02')[0], 'Challenged')                                # a record on the table => looks at it
        self.assertEqual(pick_beat({'tactic': 'REBUKE'}, None)[0], 'Angry')


if __name__ == '__main__':
    unittest.main()
