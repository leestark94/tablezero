// Integration candidate, not installed in the game. Unity uGUI, no third-party packages.
// Requires separately painted/rigged portrait layers. It cannot animate a flattened photo well.
using System;
using UnityEngine;
using UnityEngine.UI;

namespace TableZero.Handoff
{
    public enum InterviewBeat { Idle, Listening, Considering, Answering, Guarded, Challenged, Angry, Withdrawn }

    [Serializable]
    public sealed class PortraitPose
    {
        public InterviewBeat beat;
        public Sprite face;
        [Range(-1, 1)] public float gazeX;
        [Range(-1, 1)] public float gazeY;
        [Range(-5, 5)] public float headTilt;
        [Range(-1, 1)] public float lean;
    }

    [DisallowMultipleComponent]
    public sealed class LivingSuspectPortrait : MonoBehaviour
    {
        [Header("Optional layer pivots; each must be a different transform")]
        [SerializeField] RectTransform torsoPivot;
        [SerializeField] RectTransform headPivot;
        [SerializeField] RectTransform gazePivot;
        [SerializeField] RectTransform handPivot;
        [Header("Actual artwork, not a black censor bar")]
        [SerializeField] Image face;
        [SerializeField] Image eyelidsClosed;
        [SerializeField] Image mouth;
        [SerializeField] Sprite mouthRest;
        [SerializeField] Sprite mouthSmall;
        [SerializeField] Sprite mouthOpen;
        [SerializeField] PortraitPose[] poses = Array.Empty<PortraitPose>();
        [Header("Small restrained motion at 1080p reference resolution")]
        [SerializeField, Range(0, 4)] float breathPixels = 1.2f;
        [SerializeField, Range(0, 4)] float headPixels = 0.7f;
        [SerializeField, Range(0, 8)] float gazePixels = 2.5f;
        [SerializeField, Range(0, 12)] float leanPixels = 4;
        [SerializeField, Range(0, 4)] float handPixels = 0.6f;
        [SerializeField] bool reducedMotion;
        [SerializeField] bool freezeWhenPaused = true;
        [SerializeField, Range(1, 20)] float blendSpeed = 5;

        Vector2 torsoBase, headBase, gazeBase, handBase;
        Quaternion headRotation;
        InterviewBeat current;
        PortraitPose pose;
        float elapsed, phase, nextBlink, blinkUntil, gazeAt, lookX, lookY;
        float targetX, targetY, targetTilt, targetLean, tilt, lean;
        float speechEnvelope, speechExpiry, nextMouth;
        int sequence;
        bool captured;

        void Awake()
        {
            if (torsoPivot) torsoBase = torsoPivot.anchoredPosition;
            if (headPivot) { headBase = headPivot.anchoredPosition; headRotation = headPivot.localRotation; }
            if (gazePivot) gazeBase = gazePivot.anchoredPosition;
            if (handPivot) handBase = handPivot.anchoredPosition;
            captured = true;
            phase = UnityEngine.Random.Range(0f, 20f);
            SetBeat(InterviewBeat.Idle);
        }

        void OnEnable()
        {
            nextBlink = elapsed + UnityEngine.Random.Range(2.4f, 5.5f);
            gazeAt = elapsed + UnityEngine.Random.Range(1.2f, 3.8f);
            blinkUntil = -1;
            speechEnvelope = 0;
            if (eyelidsClosed) eyelidsClosed.enabled = false;
            if (mouth) mouth.sprite = mouthRest;
        }

        // Call ONLY from a validated interview event. It conveys acting, not guilt/truth probability.
        // Return false on stale/out-of-order events after an async answer or a cancelled request.
        public bool ApplyBeat(InterviewBeat beat, int eventSequence)
        {
            if (eventSequence <= sequence) return false;
            sequence = eventSequence;
            SetBeat(beat);
            return true;
        }

        public void ResetForSession()
        {
            sequence = 0;
            speechEnvelope = 0;
            speechExpiry = 0;
            blinkUntil = -1;
            if (eyelidsClosed) eyelidsClosed.enabled = false;
            if (mouth) mouth.sprite = mouthRest;
            SetBeat(InterviewBeat.Idle);
        }

        // Supply normalized envelope from REAL playback only, or use a separate viseme adapter.
        // Do not wiggle the mouth while waiting for the model or pretend this is phoneme lip sync.
        public void SetSpeechEnvelope(float envelope)
        {
            speechEnvelope = float.IsNaN(envelope) || float.IsInfinity(envelope) ? 0 : Mathf.Clamp01(envelope);
            speechExpiry = elapsed + 0.15f;
        }

        public void SetReducedMotion(bool enabled) { reducedMotion = enabled; }

        void SetBeat(InterviewBeat beat)
        {
            current = beat;
            pose = Array.Find(poses, p => p != null && p.beat == beat);
            targetX = pose != null ? pose.gazeX : 0;
            targetY = pose != null ? pose.gazeY : 0;
            targetTilt = pose != null ? pose.headTilt : 0;
            targetLean = pose != null ? pose.lean : 0;
            if (face && pose != null && pose.face) face.sprite = pose.face;
            if (beat != InterviewBeat.Answering) { speechEnvelope = 0; if (mouth) mouth.sprite = mouthRest; }
        }

        void Update()
        {
            if (!captured || (freezeWhenPaused && Time.timeScale == 0)) return;
            float dt = Mathf.Min(Time.unscaledDeltaTime, 0.1f);
            elapsed += dt;
            float blend = 1 - Mathf.Exp(-blendSpeed * dt);
            if (elapsed >= gazeAt)
            {
                // No fixed "look away means lying" mapping. Micro-gaze is cosmetic.
                targetX = (pose != null ? pose.gazeX : 0) + UnityEngine.Random.Range(-0.22f, 0.22f);
                targetY = (pose != null ? pose.gazeY : 0) + UnityEngine.Random.Range(-0.1f, 0.1f);
                gazeAt = elapsed + UnityEngine.Random.Range(1.5f, 4.5f);
            }
            lookX = Mathf.Lerp(lookX, targetX, blend);
            lookY = Mathf.Lerp(lookY, targetY, blend);
            tilt = Mathf.Lerp(tilt, targetTilt, blend);
            lean = Mathf.Lerp(lean, targetLean, blend);
            float motion = reducedMotion ? 0 : 1;
            float breath = Mathf.Sin(elapsed * 1.35f + phase);
            if (torsoPivot) torsoPivot.anchoredPosition = torsoBase + new Vector2(0, breath * breathPixels * motion);
            if (headPivot)
            {
                headPivot.anchoredPosition = headBase + new Vector2(lean * leanPixels, breath * headPixels) * motion;
                headPivot.localRotation = headRotation * Quaternion.Euler(0, 0, tilt * motion);
            }
            if (gazePivot) gazePivot.anchoredPosition = gazeBase + new Vector2(lookX, lookY) * gazePixels * motion;
            if (handPivot) handPivot.anchoredPosition = handBase + new Vector2(Mathf.Sin(elapsed * 0.47f + phase), 0) * handPixels * motion;
            if (elapsed >= nextBlink)
            {
                blinkUntil = elapsed + UnityEngine.Random.Range(0.10f, 0.16f);
                nextBlink = elapsed + UnityEngine.Random.Range(2.4f, 6.2f);
            }
            if (eyelidsClosed) eyelidsClosed.enabled = !reducedMotion && elapsed < blinkUntil;
            if (mouth && elapsed >= nextMouth)
            {
                float level = current == InterviewBeat.Answering && elapsed < speechExpiry ? speechEnvelope : 0;
                mouth.sprite = level > 0.6f && mouthOpen ? mouthOpen : level > 0.12f && mouthSmall ? mouthSmall : mouthRest;
                nextMouth = elapsed + 0.06f;
            }
        }

        void OnDisable()
        {
            if (!captured) return;
            if (torsoPivot) torsoPivot.anchoredPosition = torsoBase;
            if (headPivot) { headPivot.anchoredPosition = headBase; headPivot.localRotation = headRotation; }
            if (gazePivot) gazePivot.anchoredPosition = gazeBase;
            if (handPivot) handPivot.anchoredPosition = handBase;
            if (eyelidsClosed) eyelidsClosed.enabled = false;
            if (mouth) mouth.sprite = mouthRest;
        }
    }
}
