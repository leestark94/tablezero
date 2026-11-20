using System;
using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    // Drop onto scene controller. Never use runtime-generated primitive meshes as production art.
    // Explicit animator/audio/physics bindings are REQUIRED: absent assets cause clear warnings, not fake execution.
    public class CinematicDirector : MonoBehaviour
    {
        [Serializable] public class Cue
        {
            public string id, group, description, animation, sfx, physics_event, subtitle, status;
            public string[] requires;
            public float cooldown_s, camera_impulse;
            public int repeat_limit;
        }
        [Serializable] public class CueList { public Cue[] items; }
        [Serializable] public class AnimationBinding { public string cueAnimation; public string animatorState; }
        [Serializable] public class AudioBinding { public string cueSound; public AudioClip clip; }
        [Serializable] public class PhysicsBinding { public string physicsEvent; public Rigidbody body; public Vector3 localImpulse; }

        public TextAsset catalogWrapper; // JSON object {"items":[...]} ; never expose private canon.
        public Animator subjectAnimator;
        public AudioSource effectsSource;
        public Camera viewCamera;
        public AnimationBinding[] animations;
        public AudioBinding[] sounds;
        public PhysicsBinding[] props;
        public float maxCameraDisplacement = 0.004f;
        public bool allowCuesWithoutClips = false; // Preview ONLY
        public bool legacyPreviewMode = false; // PRODUCTION FALSE; use TZInterrogationPerformance + server approvals
        public event Action<string> OnSubtitle;

        readonly Dictionary<string,Cue> cues = new Dictionary<string,Cue>();
        readonly Dictionary<string,float> lastAt = new Dictionary<string,float>();
        readonly Dictionary<string,int> counts = new Dictionary<string,int>();
        readonly HashSet<string> flags = new HashSet<string>();
        Vector3 cameraBase;
        float shakeUntil, shakeAmplitude;

        void Awake()
        {
            if (viewCamera) cameraBase = viewCamera.transform.localPosition;
            if (!catalogWrapper) { Debug.LogError("TABLE//ZERO: cinematic catalog absent"); return; }
            var list = JsonUtility.FromJson<CueList>(catalogWrapper.text);
            if (list == null || list.items == null) { Debug.LogError("Invalid catalog wrapper"); return; }
            foreach (var c in list.items) if (!string.IsNullOrEmpty(c.id)) cues[c.id] = c;
        }
        public void SetFlag(string flag, bool enabled)
        {
            if (enabled) flags.Add(flag); else flags.Remove(flag);
        }
        public bool Trigger(string id, string actorId)
        {
            if (!legacyPreviewMode)
            {
                Debug.LogWarning("Legacy cinematic Trigger blocked: use authenticated server approval and animation-contact performance");
                return false;
            }
            if (!cues.TryGetValue(id, out var cue)) { Debug.LogWarning("Missing cue " + id); return false; }
            foreach (var f in cue.requires ?? Array.Empty<string>()) if (!flags.Contains(f)) return false;
            string key = actorId + ":" + id;
            if (counts.TryGetValue(key, out int count) && count >= cue.repeat_limit) return false;
            if (lastAt.TryGetValue(key, out float timestamp) && Time.time - timestamp < cue.cooldown_s) return false;
            AnimationBinding motion = Array.Find(animations, x => x != null && x.cueAnimation == cue.animation);
            AudioBinding audio = Array.Find(sounds, x => x != null && x.cueSound == cue.sfx);
            if (!allowCuesWithoutClips && (motion == null || subjectAnimator == null || audio == null || audio.clip == null || effectsSource == null))
            {
                Debug.LogWarning("TABLE//ZERO ASSET_MISSING: " + id + " (animation/audio)"); return false;
            }
            if (motion != null && subjectAnimator) subjectAnimator.CrossFadeInFixedTime(motion.animatorState, .16f);
            if (audio != null && audio.clip && effectsSource) effectsSource.PlayOneShot(audio.clip);
            if (cue.physics_event != "none")
                Debug.LogWarning("Legacy preview physics cue: production must use animator contact event");
            if (false && cue.physics_event != "none")
            {
                PhysicsBinding physics = Array.Find(props, x => x != null && x.physicsEvent == cue.physics_event);
                if (physics != null && physics.body != null) physics.body.AddForce(physics.body.transform.TransformVector(physics.localImpulse), ForceMode.Impulse);
                else Debug.LogWarning("TABLE//ZERO physics prop unbound: " + cue.physics_event);
            }
            if (!string.IsNullOrWhiteSpace(cue.subtitle)) OnSubtitle?.Invoke(cue.subtitle);
            shakeAmplitude = Mathf.Min(maxCameraDisplacement, cue.camera_impulse * .025f);
            shakeUntil = Time.time + .22f;
            lastAt[key] = Time.time;
            counts[key] = count + 1;
            return true;
        }
        void LateUpdate()
        {
            if (!viewCamera) return;
            if (Time.time < shakeUntil)
            {
                float p = Mathf.Clamp01((shakeUntil - Time.time) / .22f);
                float t = Time.time * 29f;
                viewCamera.transform.localPosition = cameraBase + new Vector3(Mathf.Sin(t),Mathf.Sin(t*1.37f),0f) * shakeAmplitude * p;
            }
            else viewCamera.transform.localPosition = Vector3.Lerp(viewCamera.transform.localPosition,cameraBase,Time.deltaTime * 18f);
        }
    }
}
