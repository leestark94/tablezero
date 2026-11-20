using System;
using UnityEngine;
using UnityEngine.Audio;

namespace TableZero
{
    // Korean lived-in ambience, authored recordings only. No fake sound generators.
    // Snapshot audio mixing lets the refrigerator emerge when the hallway door closes.
    public sealed class TZSoundStage : MonoBehaviour
    {
        [Serializable] public class Stage
        {
            public string sceneId;
            public AudioMixerSnapshot snapshot;
            public AudioSource roomTone;
            public AudioSource exteriorLeak;
            public AudioSource soundDetail;
            public float transitionSeconds=.45f;
        }
        public Stage[] stages;
        public bool subtitlesOn=true;
        public string currentStage;
        public bool Enter(string sceneId)
        {
            Stage next=Array.Find(stages,x=>x!=null&&x.sceneId==sceneId);
            if(next==null || next.snapshot==null || next.roomTone==null || next.roomTone.clip==null)
            {
                Debug.LogError("TABLE ZERO AUDIO STAGE MISSING: " + sceneId);return false;
            }
            next.snapshot.TransitionTo(Mathf.Clamp(next.transitionSeconds,.15f,1.5f));
            if(!next.roomTone.isPlaying)next.roomTone.Play();
            currentStage=sceneId;
            return true;
        }
        public void PlayWorldSound(string stageId,AudioClip authoredClip,Vector3 worldPoint,float volume=.65f)
        {
            Stage stage=Array.Find(stages,x=>x!=null&&x.sceneId==stageId);
            if(stage==null || !stage.soundDetail || !authoredClip)
            {
                Debug.LogError("Spatial sound missing; refusing fake playback");return;
            }
            stage.soundDetail.transform.position=worldPoint;
            stage.soundDetail.spatialBlend=1f;
            stage.soundDetail.PlayOneShot(authoredClip,Mathf.Clamp01(volume));
        }
    }
}
