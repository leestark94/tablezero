using System;
using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// A cue cannot play from an unverified AI action; requires server approval envelope
    /// and an authored asset manifest. Transport must be authenticated in production.
    /// </summary>
    public sealed class TZAuthorizedCuePlayer : MonoBehaviour
    {
        [Serializable] public class ApprovedPlayback
        {
            public string beat_id;
            public string legacy_cue;
            public string gesture_binding;
            public string sound_binding;
            public string prop_binding;
            public string camera_style;
            public float duration_s;
            public string contact_animation_event;
        }
        [Serializable] public class ApprovedEnvelope
        {
            public bool approved;
            public string status;
            public string event_id;
            public ApprovedPlayback playback;
        }
        public TZPerformanceManifest manifest;
        public TZInterrogationPerformance suspect;
        public AudioSource sceneFoley;
        public bool allowReferenceOnlyPlayback = false;
        private readonly HashSet<string> eventDedupe=new HashSet<string>();
        public bool PlayApproved(ApprovedEnvelope envelope)
        {
            if(envelope==null || !envelope.approved || envelope.playback==null || string.IsNullOrEmpty(envelope.event_id))return false;
            if(eventDedupe.Contains(envelope.event_id))return false;
            // The manifest is a release gate, not an art generator
            if(manifest==null || !manifest.IsReady(envelope.playback.legacy_cue))
            {
                Debug.LogError("CINEMATIC BLOCKED: physical art/animation/audio/license not ready: " + envelope.playback.legacy_cue);
                return false;
            }
            if(envelope.status!="PLAYMODE_VERIFIED" && !allowReferenceOnlyPlayback)
            {
                Debug.LogWarning("Reference-only cinematic not allowed without Play Mode asset verification");
                return false;
            }
            if(envelope.playback.legacy_cue.StartsWith("interview."))
            {
                if(!suspect || !suspect.PlayApprovedCue(envelope.playback.legacy_cue,envelope.event_id))return false;
            }
            else
            {
                // Environmental cues need their own authored Timeline and actual SFX binding.
                // Never call this a completed cinematic until each cue's clip+AudioSource is installed.
                if(!sceneFoley) {Debug.LogError("Scene foley source missing");return false;}
                Debug.LogWarning("Scene cue requires separately authored Timeline playback: " + envelope.playback.legacy_cue);
                return false;
            }
            eventDedupe.Add(envelope.event_id);
            return true;
        }
    }
}
