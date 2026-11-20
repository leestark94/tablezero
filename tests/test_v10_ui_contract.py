"""Regression guards for the newly applied V0.7 UI directive.
Runs with Python only; Unity must still compile and be visually reviewed separately.
"""
from __future__ import annotations
import pathlib, unittest, json, xml.etree.ElementTree as ET
from server.api import page_projection
from server.episode_controller import EpisodeController
from server.runtime import World
ROOT=pathlib.Path(__file__).resolve().parents[1]

class UIContractTests(unittest.TestCase):
    def setUp(self): self.ctrl=EpisodeController(world=World())
    def test_01_uxml_is_wellformed(self):
        ET.parse(ROOT/'unity/UI/CaseDesk.uxml')
    def test_02_uxml_elements_match_controller(self):
        doc=(ROOT/'unity/UI/CaseDesk.uxml').read_text()
        for n in ('case-desk','content-list','record-inspector','inspector-provenance',
                  'inspector-limitation','compare-a','compare-b','compare-clear',
                  'question-input','report-confirm','report-evidence-list'):
            self.assertIn('name="'+n+'"',doc)
    def test_03_server_only_reveals_acquired_evidence(self):
        d=page_projection(self.ctrl,'evidence')
        self.assertEqual([x['id'] for x in d['records']],['e01'])
        self.assertEqual([x['status'] for x in d['records']],['e01'])
        self.assertIn('limitation',d['records'][0])
        self.assertNotIn('culprit_id',json.dumps(d,ensure_ascii=False))
        self.assertNotIn('truth_events',json.dumps(d,ensure_ascii=False))
    def test_04_evidence_records_have_limits_and_source(self):
        e=page_projection(self.ctrl,'evidence')['records'][0]
        self.assertTrue(e['limitation'])
        self.assertTrue(e['provenance'])
        self.assertEqual(e['display_status'],'확보됨')
    def test_05_no_unacquired_evidence_on_timeline(self):
        d=page_projection(self.ctrl,'timeline')
        shown={x['id'] for x in d['records'] if x['kind']=='timeline_source'}
        self.assertEqual(shown,{'e01'})
    def test_06_testimony_unverified(self):
        self.ctrl.world.claims.append({'suspect_id':'s1','utterance':'저는 그 시간에 집에 있었어요','mode':'deny'})
        d=page_projection(self.ctrl,'interview')
        self.assertEqual(d['records'][0]['status'],'미검증 진술')
        self.assertTrue(d['records'][0]['id'].startswith('statement:'))
        self.assertIn('확정되지 않음',d['records'][0]['limitation'])
    def test_07_navigation_is_server_authoritative(self):
        with self.assertRaises(ValueError):page_projection(self.ctrl,'truth')
    def test_08_developer_preview_flag_exists(self):
        for tab in ('case','evidence','interview','timeline','report','settings'):
            self.assertIn('LOCAL PREVIEW',page_projection(self.ctrl,tab)['connection'])
    def test_09_record_comparison_never_sets_guilt(self):
        code=(ROOT/'unity/Runtime/TZCaseDeskUI.cs').read_text()
        self.assertIn('거짓 진술이 확정되지 않습니다',code)
        self.assertNotIn('guilt_score',code)
        self.assertNotIn('lie_probability',code)
    def test_10_raw_v07_directive_preserved(self):
        text=(ROOT/'reference/MASTER_DEVELOPMENT_DIRECTIVE_V07_ORIGINAL.txt').read_text()
        for s in ('AI 용의자','영화형 연출','한국적인 현실감','최종 합격 기준'):
            self.assertIn(s,text)
    def test_11_comparison_only_evidence_with_id(self):
        code=(ROOT/'unity/Runtime/TZCaseDeskUI.cs').read_text()
        self.assertIn('string.IsNullOrEmpty(selectedRecord.id)',code)
        self.assertIn('firstRecord.id != selectedRecord.id',code)
    def test_12_original_canon_unmodified(self):
        from server.episode_controller import EpisodeController
        self.ctrl.world.assert_canon_unchanged()

if __name__=='__main__':unittest.main()
