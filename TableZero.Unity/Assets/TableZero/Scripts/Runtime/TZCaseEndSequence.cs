using System;
using System.Collections;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Plays a branching final staging sequence using real Timeline/PlayableDirector references.
    /// Subtitles are loaded from approved server outcome; never infer culprit from local assets.
    /// </summary>
    public sealed class TZCaseEndSequence : MonoBehaviour
    {
        [Serializable]public sealed class Moment
        {
            public string id;
            public UnityEngine.Playables.PlayableDirector authoredTimeline;
            public AudioSource sound;
            public AudioClip authoredClip;
            public float afterSeconds=.25f;
        }
        public Moment[] moments;
        public event Action<string> OnMomentCompleted;
        private bool running;
        public bool StartApprovedSequence(string[] approvedMomentIds)
        {
            if(running || approvedMomentIds==null || approvedMomentIds.Length==0)return false;
            foreach(string id in approvedMomentIds)
            {
                Moment item=Array.Find(moments,x=>x!=null && x.id==id);
                if(item==null || !item.authoredTimeline || !item.sound || !item.authoredClip)
                {
                    Debug.LogError("Case ending Timeline or recorded sound missing: " + id);
                    return false;
                }
            }
            StartCoroutine(Play(approvedMomentIds));return true;
        }
        private IEnumerator Play(string[] ids)
        {
            running=true;
            foreach(string id in ids)
            {
                Moment moment=Array.Find(moments,x=>x.id==id);
                moment.authoredTimeline.Play();
                moment.sound.PlayOneShot(moment.authoredClip);
                // Use director timeline duration; do not invent clip time
                double seconds=moment.authoredTimeline.duration;
                yield return new WaitForSecondsRealtime((float)Math.Max(.05,seconds)+Mathf.Max(0,moment.afterSeconds));
                moment.authoredTimeline.Stop();
                OnMomentCompleted?.Invoke(id);
            }
            running=false;
        }
    }
}
