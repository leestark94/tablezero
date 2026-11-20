using System;
using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// High-end authored performance executor
    /// AI can request a cue ID but only the authoritative server selects it
    /// NEVER trigger physics before the actual animator contact event
    /// Never synthesize primitive bodies, chairs, cups or a suspect
    /// </summary>
    public sealed class TZInterrogationPerformance : MonoBehaviour
    {
        [Serializable] public sealed class Performance
        {
            public string cueId;
            public string animatorState;
            public AudioClip anticipation;
            public AudioClip impactSound;
            public AudioClip clothingRustle;
            public bool requiresTableContact;
            public bool requiresChairContact;
            public float blendSeconds = .20f;
        }
        [Header("Authentic artist-made assets only")]
        public Animator suspectAnimator;
        public AudioSource spatialVoice;
        public AudioSource propAudio;
        public InterrogationTable physicalTable;
        public Rigidbody chairBody;
        public Transform contactPalm;
        public Transform actualTablePoint;
        public Camera sceneCamera;
        public bool reducedMotion;
        public float maxViewOffsetMeters = .0035f;
        public Performance[] performances;
        public event Action<string> OnPerformanceCompleted;
        private readonly HashSet<string> played = new HashSet<string>();
        private Performance active;
        private Vector3 cameraRest;
        private float shakeRemaining;
        private float shakeMagnitude;
        private bool impactFired;

        private void Awake()
        {
            if (sceneCamera) cameraRest = sceneCamera.transform.localPosition;
        }
        public bool IsBound(string cueId)
        {
            Performance p = Array.Find(performances, x => x != null && x.cueId == cueId);
            if (p == null || suspectAnimator == null || string.IsNullOrEmpty(p.animatorState)) return false;
            if (!suspectAnimator.HasState(0, Animator.StringToHash(p.animatorState))) return false;
            if (p.requiresTableContact && (!physicalTable || !physicalTable.cupBody || !contactPalm || !actualTablePoint)) return false;
            if (p.requiresChairContact && !chairBody) return false;
            if (!propAudio || (p.requiresTableContact && !p.impactSound)) return false;
            return true;
        }
        public bool PlayApprovedCue(string approvedCueId, string serverEventId)
        {
            if (string.IsNullOrWhiteSpace(serverEventId)) return false;
            string key = serverEventId + ":" + approvedCueId;
            if (played.Contains(key)) return false; // network retries cannot replay impacts
            if (!IsBound(approvedCueId))
            {
                Debug.LogError("TABLE//ZERO MISSING_AUTHORED_PERFORMANCE " + approvedCueId);
                return false;
            }
            active = Array.Find(performances, p => p != null && p.cueId == approvedCueId);
            impactFired = false;
            played.Add(key);
            suspectAnimator.CrossFadeInFixedTime(active.animatorState, Mathf.Clamp(active.blendSeconds, .12f, .55f));
            if (active.anticipation && propAudio) propAudio.PlayOneShot(active.anticipation);
            return true;
        }
        /// <summary>Place AnimationEvent on actual palm-to-table keyframe, NEVER at clip start</summary>
        public void ContactFrame_Table()
        {
            if (active == null || !active.requiresTableContact || impactFired) return;
            if (!physicalTable || !contactPalm || !actualTablePoint) return;
            impactFired = true;
            Vector3 direction = (contactPalm.position - actualTablePoint.position).normalized;
            // Very small collision-derived impulse; rigidbody handles resonance
            physicalTable.OnApprovedTableSlam((direction + Vector3.up * .08f).normalized * .08f);
            if (propAudio && active.impactSound) propAudio.PlayOneShot(active.impactSound);
            shakeRemaining = reducedMotion ? 0f : .17f;
            shakeMagnitude = Mathf.Min(maxViewOffsetMeters, .003f);
        }
        /// <summary>Place on chair-leg contact frame only</summary>
        public void ContactFrame_Chair()
        {
            if (active == null || !active.requiresChairContact || !chairBody || impactFired) return;
            impactFired = true;
            chairBody.AddForce(chairBody.transform.forward * .06f, ForceMode.Impulse);
            if (propAudio && active.impactSound) propAudio.PlayOneShot(active.impactSound);
        }
        public void PerformanceEnd()
        {
            if (active == null) return;
            string cueId = active.cueId;
            active = null;
            OnPerformanceCompleted?.Invoke(cueId);
        }
        private void LateUpdate()
        {
            if (!sceneCamera) return;
            if (shakeRemaining > 0f)
            {
                shakeRemaining = Mathf.Max(0f, shakeRemaining - Time.unscaledDeltaTime);
                float normalized = shakeRemaining / .17f;
                float t = Time.unscaledTime * 43f;
                Vector3 offset = new Vector3(Mathf.Sin(t), Mathf.Sin(t * .73f), 0) * shakeMagnitude * normalized;
                sceneCamera.transform.localPosition = cameraRest + offset;
            }
            else
            {
                sceneCamera.transform.localPosition = Vector3.Lerp(sceneCamera.transform.localPosition,
                    cameraRest, Mathf.Clamp01(Time.unscaledDeltaTime * 18f));
            }
        }
    }
}
