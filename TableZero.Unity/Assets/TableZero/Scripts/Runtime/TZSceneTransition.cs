using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UIElements;

namespace TableZero
{
    // Seamless camera exposure bridge. No shock cuts, no camera teleportation, no forced 1P surrender.
    public sealed class TZSceneTransition : MonoBehaviour
    {
        [Serializable] public class TransitionCue
        {
            public string id;
            public AudioClip environmentalTail;
            public AudioClip environmentalNext;
            [Range(.15f,1.4f)]public float blendSeconds=.4f;
            public UnityEvent afterFade;
        }
        public AudioSource oldAmbience;
        public AudioSource newAmbience;
        public TransitionCue[] cues;
        public bool cinematicTransitionsEnabled=true;
        public event Action<string> OnTransitionCompleted;
        private bool playing;
        public bool TryTransition(string id)
        {
            if(playing)return false;
            var cue=Array.Find(cues,x=>x!=null&&x.id==id);
            if(cue==null || !oldAmbience || !newAmbience || !cue.environmentalNext)
            {
                Debug.LogError("TABLE ZERO MISSING SOUND TRANSITION " + id);return false;
            }
            StartCoroutine(Blend(cue));return true;
        }
        IEnumerator Blend(TransitionCue cue)
        {
            playing=true;
            newAmbience.clip=cue.environmentalNext;newAmbience.volume=0;newAmbience.loop=true;newAmbience.Play();
            float from=oldAmbience.volume;
            float duration=cinematicTransitionsEnabled?cue.blendSeconds:.02f;
            for(float t=0;t<duration;t+=Time.unscaledDeltaTime)
            {
                float x=Mathf.Clamp01(t/duration);
                float eased=x*x*(3f-2f*x);
                oldAmbience.volume=Mathf.Lerp(from,0,eased);
                newAmbience.volume=Mathf.Lerp(0,from,eased);
                yield return null;
            }
            oldAmbience.Stop();oldAmbience.volume=from;newAmbience.volume=from;
            cue.afterFade?.Invoke();
            playing=false;OnTransitionCompleted?.Invoke(cue.id);
        }
    }
}
