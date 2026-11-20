import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from server.v11_cinematic_gate import CinematicGate
from server.runtime import GuardError

class CinematicGateTests(unittest.TestCase):
    def setUp(self):
        self.g=CinematicGate()
        self.id='V11_PLAYER_TABLE_STRIKE'
        self.kw={'scene':'interview','flags':['pressure_tactic_approved'],
                 'verified_asset_ids':['fp_slam_clip','table_rigidbody','glass_rigidbody','mic_overload'],
                 'now':1000,'safe_window':True}
    def test_catalog_has_55_unique_beats(self):
        self.assertEqual(len(self.g.beats),55)
    def test_missing_mesh_blocks(self):
        kw=dict(self.kw,verified_asset_ids=['fp_slam_clip'])
        self.assertEqual(self.g.request(self.id,**kw)['reason'],'authored_assets_missing')
    def test_unsafe_window_blocks(self):
        kw=dict(self.kw,safe_window=False)
        self.assertEqual(self.g.request(self.id,**kw)['reason'],'unsafe_play_window')
    def test_authorized_not_played(self):
        v=self.g.request(self.id,**self.kw)
        self.assertTrue(v['approved']);self.assertEqual(v['status'],'AUTHORIZED_NOT_YET_PLAYED')
        self.assertEqual(self.g.counts[self.id],0)
        self.assertFalse(self.g.confirm_playback(v['authorization_token'],started=False,played_by_authorized_runtime=False)['played'])
        self.assertEqual(self.g.counts[self.id],0)
    def test_successful_playback_logged(self):
        v=self.g.request(self.id,**self.kw)
        p=self.g.confirm_playback(v['authorization_token'],started=True,played_by_authorized_runtime=True)
        self.assertTrue(p['played']);self.assertFalse(p['world_mutation'])
        self.assertEqual(self.g.counts[self.id],1)
    def test_cooldown(self):
        v=self.g.request(self.id,**self.kw)
        self.g.confirm_playback(v['authorization_token'],started=True,played_by_authorized_runtime=True)
        w=self.g.request(self.id,**dict(self.kw,now=1005))
        self.assertEqual(w['reason'],'session_repeat_limit')
    def test_wrong_scene(self):
        self.assertEqual(self.g.request(self.id,**dict(self.kw,scene='room302'))['reason'],'scene_mismatch')
    def test_missing_conditions(self):
        self.assertEqual(self.g.request(self.id,**dict(self.kw,flags=[]))['reason'],'conditions_not_met')
    def test_no_double_confirm(self):
        v=self.g.request(self.id,**self.kw)
        self.g.confirm_playback(v['authorization_token'],started=True,played_by_authorized_runtime=True)
        with self.assertRaises(GuardError):
            self.g.confirm_playback(v['authorization_token'],started=True,played_by_authorized_runtime=True)
if __name__=='__main__':unittest.main()
