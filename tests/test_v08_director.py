import json, pathlib, unittest
from server.runtime import World,GuardError
from server.beat_director import BeatDirector,TrustedSignal,AssetManifest
from server.episode_controller import EpisodeController
from server.outcomes import OutcomeDirector
from server.providers import PreviewProvider,ProviderGate,REPLY_SCHEMA,OllamaProvider,ProviderError
from server.dialogue_quality import clean_line,lint_line,audit_corpus

ROOT=pathlib.Path(__file__).resolve().parents[1]

class DirectorV08Tests(unittest.TestCase):
 def setUp(self):
  self.world=World()
  self.ctrl=EpisodeController(world=self.world)
 def test_01_beat_95(self):
  # 95 authored beats; those tied to the retired v0.4 story's evidence are disabled, never auto-loaded
  d=self.ctrl.director;self.assertEqual(len(d.beats)+len(d.disabled_foreign),95)
  ev={e['id'] for e in self.world._canon['evidence']}
  self.assertTrue(all(set(b['requires_evidence_ids'])<=ev for b in d.beats))
 def test_02_unique_beat_ids(self):self.assertEqual(len(self.ctrl.director.by_id),len(self.ctrl.director.beats))
 def test_03_82_original_cues(self):self.assertEqual(len(self.world.catalog),82)
 def test_04_no_stolen_evidence(self):
  with self.assertRaises(GuardError):self.ctrl.question('시간은요?')
 def test_05_case_start_evidence(self):self.assertEqual(self.world.available_evidence,{'V21-E17'})
 def test_06_no_unacquired_access(self):
  with self.assertRaises(GuardError):self.ctrl.acquire('V21-E14',authorized=False,photo_logged=True)
 def test_07_evidence_chain(self):
  self.ctrl.transition('room302')
  with self.assertRaises(GuardError):self.ctrl.acquire('V21-E01',authorized=True,photo_logged=True,sealed=False)
  self.ctrl.acquire('V21-E01',authorized=True,photo_logged=True,sealed=True)
  self.assertIn('sealed',self.ctrl.state.acquired_chain['V21-E01'])
 def test_08_scene_transition_cannot_jump_to_interview(self):
  with self.assertRaises(GuardError):self.ctrl.transition('interview')
 def test_09_interview_preview(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview');self.ctrl.start_interview('s1')
  r=self.ctrl.question('몇 시에 나가셨어요?')
  self.assertEqual(r['provider'],'SCRIPTED_PREVIEW_NOT_AI')
  self.assertNotIn('진범',r['line'])
 def test_10_no_unverified_evidence_prompt(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview');self.ctrl.start_interview('s1')
  with self.assertRaises(GuardError):self.ctrl.question('어떻게요?',presented_evidence='e11')
 def test_11_no_end_without_report_scene(self):
  with self.assertRaises(GuardError):self.ctrl.file_report(None,[],final=True)
 def test_12_no_final_without_confirmation(self):
  self.ctrl.transition('desk')
  with self.assertRaises(GuardError):self.ctrl.file_report(None,[],final=False)
 def test_13_defer_report(self):
  self.ctrl.transition('desk');r=self.ctrl.file_report(None,[],final=True)
  self.assertEqual(r['ending_code'],'ongoing')
  self.assertTrue(r['may_continue'])
 def _all_evidence(self):
  for e in self.world._canon['evidence']:self.world.expose_evidence(e['id'])
 def test_14_correct_full_report(self):
  self._all_evidence();self.ctrl.transition('desk')
  r=self.ctrl.file_report('s3',sorted(self.world.available_evidence),final=True)
  self.assertEqual(r['ending_code'],'substantiated')
  self.assertFalse(r['may_continue'])
 def test_15_wrong_accusation_not_accepted(self):
  self._all_evidence();self.ctrl.transition('desk')
  r=self.ctrl.file_report('s1',sorted(self.world.available_evidence),final=True)
  self.assertEqual(r['ending_code'],'recheck_required')
  self.assertNotIn('correct_identity',r)
 def test_16_correct_but_missing_axis_no_spoiler(self):
  self.ctrl.transition('desk')
  r=self.ctrl.file_report('s3',['V21-E17'],final=True)
  self.assertEqual(r['ending_code'],'recheck_required')
  self.assertTrue(r['may_continue'])
  self.assertNotIn('underproved_true_person',json.dumps(r,ensure_ascii=False))
 def test_17_chain_defect(self):
  self._all_evidence();self.ctrl.transition('desk')
  r=self.ctrl.file_report('s3',sorted(self.world.available_evidence),final=True,chain_defects=['V21-E16'])
  self.assertFalse(r['report_accepted'])
 def test_18_no_reverse_route(self):
  self.ctrl.set_act('pressure')
  with self.assertRaises(GuardError):self.ctrl.set_act('arrival')
 def test_19_contact_after_clock(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview');self.ctrl.start_interview('s2')
  # V21: contact window opens 00:40 on the investigation night; pin just before it
  self.ctrl.state.case_clock_minutes=0*60+30
  with self.assertRaises(GuardError):self.ctrl.resolve_action('contact_acquaintance','s3',approved=True)
  self.ctrl.advance_case_clock(15,approved=True)
  r=self.ctrl.resolve_action('contact_acquaintance','s3',approved=True)
  self.assertTrue(r['world_changed'])
 def test_20_world_not_visible_without_reveal(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview');self.ctrl.start_interview('s2')
  self.ctrl.advance_case_clock(15,approved=True)
  self.ctrl.resolve_action('contact_acquaintance','s3',approved=True)
  self.assertEqual(self.ctrl.public_state()['visible_events'],[])
 def test_21_no_world_action_without_authority(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview');self.ctrl.start_interview('s2')
  with self.assertRaises(GuardError):self.ctrl.resolve_action('contact_acquaintance','s3',approved=False)
 def test_22_no_cinematic_without_manifest(self):
  self.ctrl.transition('room302')
  signal=TrustedSignal(scene='room302',trigger='enter',act='arrival')
  r=self.ctrl.cinematic(signal,None,now=1)
  self.assertFalse(r['approved'])
 def test_23_table_slam_rejected_by_canon(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview')
  beat=self.ctrl.director.by_id['i17_table_slam_strict']
  flags=frozenset(beat['requires_flags'])
  signal=TrustedSignal(scene='interview',trigger='reply',actor_id='s1',act=beat['act'],flags=flags)
  r=self.ctrl.director.authorize(beat['id'],signal,AssetManifest.for_reference_test(beat),now=300)
  self.assertFalse(r['approved'])
  self.assertIn('actor_not_authorized_for_slam',r['reasons'])
 def test_24_incorrect_scene_event(self):
  with self.assertRaises(GuardError):self.ctrl.cinematic(TrustedSignal(scene='interview',trigger='reply'))
 def test_25_135_authored_lines(self):
  data=json.loads((ROOT/'data/case001_scriptbook.json').read_text(encoding='utf-8'))
  self.assertEqual(len(data['dialogues']),135)
 def test_26_no_terminal_dots_authored(self):
  data=json.loads((ROOT/'data/case001_scriptbook.json').read_text(encoding='utf-8'))
  self.assertFalse(any(x['text'].endswith(('.', '。','．')) for x in data['dialogues']))
 def test_27_no_repeated_stock_dialogue(self):
  data=json.loads((ROOT/'data/case001_scriptbook.json').read_text(encoding='utf-8'))
  self.assertEqual(audit_corpus([x['text'] for x in data['dialogues']])['problems'],[])
 def test_28_clean_periods(self):self.assertEqual(clean_line('  아니라고요.  '),'아니라고요')
 def test_29_stock_filter(self):self.assertIn('stock_ai_dialogue',lint_line('진실은 언제나 밝혀지는 법이죠'))
 def test_30_schema_required(self):self.assertEqual(len(REPLY_SCHEMA['required']),6)
 def test_31_replay_public_hides_culprit(self):
  data=json.dumps(self.ctrl.public_state(),ensure_ascii=False)
  self.assertNotIn('culprit_id',data);self.assertNotIn('truth_events',data)
 def test_32_ending_scripts_clean(self):
  from server.outcomes import ENDING_SCRIPTS
  self.assertEqual(len(ENDING_SCRIPTS),5)
  self.assertFalse(any(line.endswith('.') for v in ENDING_SCRIPTS.values() for a,b,line in v))
 def test_33_public_report_never_includes_identity_correct(self):
  self.ctrl.transition('desk');r=self.ctrl.file_report('s1',['V21-E17'],final=True)
  self.assertFalse('correct_identity' in r)
 def test_34_no_evidence_name_auto_leak(self):
  from server.api import page_projection
  page=page_projection(self.ctrl,'evidence')
  self.assertEqual([x['status'] for x in page['records']],['V21-E17'])
 def test_35_question_no_terminal_dot(self):
  self.ctrl.transition('desk');self.ctrl.transition('interview');self.ctrl.start_interview('s2')
  self.assertFalse(self.ctrl.question('몇 시요?')['line'].endswith('.'))
 def test_36_forbidden_nonlocal_bridge(self):
  from server.api import serve
  with self.assertRaises(RuntimeError):serve(host='0.0.0.0')
 def test_37_policy_does_not_admit_by_gesture(self):
  for b in self.ctrl.director.beats:self.assertEqual(b['guilt_hint'],'NONE')
 def test_38_performance_no_evidence_generation(self):
  for b in self.ctrl.director.beats:self.assertEqual(b['evidence_creation'],'NONE')
 def test_39_invalid_scene_flag(self):
  from server.beat_director import BeatValidationError
  with self.assertRaises(BeatValidationError):self.ctrl.director.candidates(TrustedSignal('home','open'))
 def test_40_no_canon_mutation(self):self.world.assert_canon_unchanged()

if __name__=='__main__':unittest.main()
