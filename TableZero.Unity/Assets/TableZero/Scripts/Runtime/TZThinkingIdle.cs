using System;
using UnityEngine;

namespace TableZero
{
    // Playback while waiting for a real network model. Does not imply the NPC knows anything.
    // Idle clips require real mocap/keyframe motions; no procedural skeleton puppeteering.
    public sealed class TZThinkingIdle : MonoBehaviour
    {
        [Serializable]public class Idle
        {
            public string stateName;
            [Range(.4f,12f)]public float minimumGap=2.5f;
            public float blend=.3f;
        }
        public Animator actor;
        public Idle[] available;
        public bool active;
        public float minPauseSeconds=2.2f;
        public float maxReactDelaySeconds=12f;
        private float startTime;
        private float nextMotion;
        private int lastIndex=-1;
        public void BeginWait()
        {
            active=true;startTime=Time.unscaledTime;
            nextMotion=startTime+Mathf.Max(.4f,minPauseSeconds);
        }
        public void EndWait(){active=false;lastIndex=-1;}
        private void Update()
        {
            if(!active || !actor || available==null || available.Length==0)return;
            float now=Time.unscaledTime;
            if(now<nextMotion)return;
            if(now-startTime>maxReactDelaySeconds)
            {
                // Silence is preferable to repeated canned acting while server times out
                active=false;return;
            }
            int index=(lastIndex+1)%available.Length;
            Idle idle=available[index];
            if(idle==null || !actor.HasState(0,Animator.StringToHash(idle.stateName)))
            {
                Debug.LogWarning("Missing authored thinking idle animation");active=false;return;
            }
            actor.CrossFadeInFixedTime(idle.stateName,Mathf.Max(.12f,idle.blend));
            nextMotion=now+Mathf.Max(1.2f,idle.minimumGap);
            lastIndex=index;
        }
    }
}
