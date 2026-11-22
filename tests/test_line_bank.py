import unittest
from server import line_bank
from server.strategy import SuspectState


class LineBankTests(unittest.TestCase):
    def plan(self, tactic, focus=None, **kw):
        d = {'tactic': tactic, 'focus': focus, 'accusations': 1, 'mode': 'deny'}; d.update(kw); return d

    def test_every_authored_line_is_korean_and_has_no_trailing_period(self):
        for sid, b in line_bank.BANK.items():
            for key, lines in b.items():
                for l in lines:
                    self.assertTrue(any('가' <= c <= '힣' for c in l), (sid, key, l))
                    self.assertFalse(l.rstrip().endswith('.'), (sid, key, l))

    def test_variants_do_not_repeat_then_fall_back_to_repeat_lines(self):
        used = {}; seen = []
        for _ in range(8):
            seen.append(line_bank.pick('s2', self.plan('DENY', 'head'), '다치게 했죠', used))
        self.assertEqual(len(set(seen[:3])), 3)
        self.assertTrue(all(seen))                       # never None -> never a slow model turn
        self.assertIn(seen[3], line_bank.REPEAT['s2'])

    def test_demand_proof_escalates_with_accusations(self):
        used = {}
        a = line_bank.pick('s1', self.plan('DEMAND_PROOF', accusations=1), 'x', used)
        b = line_bank.pick('s1', self.plan('DEMAND_PROOF', accusations=3), 'x', used)
        self.assertNotEqual(a, b)

    def test_unknown_question_gets_a_clarifying_line(self):
        self.assertTrue(line_bank.pick('s3', self.plan('ANSWER'), '오늘 날씨 어때요', {}))


if __name__ == '__main__':
    unittest.main()
