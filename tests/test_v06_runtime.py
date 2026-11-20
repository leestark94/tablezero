import sys,unittest,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.runtime import World,GuardError
class RuntimeTests(unittest.TestCase):
 def setUp(self):self.w=World()
 def reply(self,**kw):
  r={'utterance':'그건 기억이 잘 안 납니다.','reply_mode':'uncertain','motion_id':'still','asserted_claim_ids':[],'new_unsupported_assertion':None,'request_external_action':None};r.update(kw);return r
 def test_01_canon_hash(self):self.w.assert_canon_unchanged()
 def test_02_projection_hidden(self):self.assertNotIn('culprit_id',str(self.w.projection()))
 def test_03_other_suspect_hidden(self):self.assertNotIn('truth_server_only',str(self.w.prompt_context('s1','어디 있었죠?')))
 def test_04_evidence_not_acquired(self):
  with self.assertRaises(GuardError):self.w.prompt_context('s2','보여드릴게요','e01')
 def test_05_reject_unknown_suspect(self):
  with self.assertRaises(GuardError):self.w.prompt_context('s99','hi')
 def test_06_accept_clean_reply(self):self.assertEqual(self.w.accept_reply('s1',self.reply())['claims_verified'],False)
 def test_07_reject_unknown_motion(self):
  with self.assertRaises(GuardError):self.w.accept_reply('s1',self.reply(motion_id='shoot'))
 def test_08_reject_extra_keys(self):
  x=self.reply();x['culprit_id']='s2'
  with self.assertRaises(GuardError):self.w.accept_reply('s2',x)
 def test_09_reject_foreign_claim(self):
  with self.assertRaises(GuardError):self.w.accept_reply('s1',self.reply(asserted_claim_ids=['c_s2_home']))
 def test_10_unverified_claim_stays_unverified(self):
  self.w.accept_reply('s2',self.reply(new_unsupported_assertion='아무도 못 봤어요'))
  self.assertIn('verified',str(self.w.projection()))
 def test_11_action_needs_server_approval(self):
  with self.assertRaises(GuardError):self.w.action('s2','contact_acquaintance','s3')
 def test_12_authorized_contact(self):
  eid=self.w.action('s2','contact_acquaintance','s3',True)
  self.assertIn(eid,self.w.knowledge['s3'])
 def test_13_detective_does_not_know_contact(self):
  self.w.action('s2','contact_acquaintance','s3',True)
  self.assertEqual(self.w.projection()['events'],[])
 def test_14_reveal_is_explicit(self):
  eid=self.w.action('s2','contact_acquaintance','s3',True);self.w.reveal(eid,'detective')
  self.assertEqual(len(self.w.projection()['events']),1)
 def test_15_unauthorized_contact(self):
  with self.assertRaises(GuardError):self.w.action('s1','contact_acquaintance','s3',True)
 def test_16_cues_82(self):self.assertEqual(len(self.w.catalog),82)
 def test_17_cue_conditions(self):self.assertFalse(self.w.director('s2','interview.table_slam',0,set())['play'])
 def test_18_cue_allow(self):self.assertTrue(self.w.director('s2','interview.table_slam',0,{'interview_active'})['play'])
 def test_19_cue_cooldown(self):
  self.w.director('s2','interview.table_slam',0,{'interview_active'})
  self.assertEqual(self.w.director('s2','interview.table_slam',1,{'interview_active'})['reason'],'cooldown')
 def test_20_cue_clip_missing(self):
  self.assertEqual(self.w.director('s2','interview.table_slam',0,{'interview_active'},available_clips={'still'})['reason'],'missing_animation')
 def test_21_canon_immutable_detection(self):
  self.w._canon['truth_server_only']['culprit_id']='s1'
  with self.assertRaises(GuardError):self.w.assert_canon_unchanged()
 def test_22_noncanonical_evidence(self):
  with self.assertRaises(GuardError):self.w.expose_evidence('nonexistent')
 def test_23_invalid_action(self):
  with self.assertRaises(GuardError):self.w.action('s2','escape_to_moon',approved=True)
 def test_24_proposal_does_not_execute(self):
  self.w.accept_reply('s2',self.reply(request_external_action='contact_acquaintance'))
  self.assertEqual(self.w.events,[])
 def test_25_four_axis_report(self):
  for e in ('e07','e08','e10','e06','e11','e01'):self.w.expose_evidence(e)
  r=self.w.evaluate_report('s2',('e07','e08','e10','e06','e11','e01'))
  self.assertTrue(r['sufficient_for_game_report'])
 def test_26_wrong_person_cannot_satisfy_report(self):
  for e in ('e07','e08','e10','e06','e11','e01'):self.w.expose_evidence(e)
  self.assertFalse(self.w.evaluate_report('s1',('e07','e08','e10','e06','e11','e01'))['sufficient_for_game_report'])
 def test_27_evidence_count_is_not_proof(self):
  for e in ('e01','e03','e04','e05'):self.w.expose_evidence(e)
  self.assertFalse(self.w.evaluate_report('s2',('e01','e03','e04','e05'))['sufficient_for_game_report'])
 def test_28_unacquired_submission_blocked(self):
  with self.assertRaises(GuardError):self.w.evaluate_report('s2',('e06',))
 def test_29_only_suspect_private_events(self):
  ctx=self.w.prompt_context('s1','뭐 했어요?')
  own={e['id'] for e in self.w._canon['truth_events'] if e['id'] in self.w.suspects['s1']['private_fact_ids']}
  self.assertEqual({e['id'] for e in ctx['private_memories']},own)
 def test_30_motion_ownership(self):
  with self.assertRaises(GuardError):self.w.accept_reply('s1',self.reply(motion_id='table_slam'))
if __name__=='__main__':unittest.main()
