using System.Collections;
using UnityEngine;

namespace TableZero
{
    public enum TZMotionKind { None, Hinge, Slide, Lift }

    /// <summary>
    /// Physical open/close motion for a server-approved prop (door/drawer/lid/sash).
    /// Pivot comes from Blender (hinge edge / drawer front). Easing has a short settle so it does
    /// not read as a tween; audio fires on the frame the latch releases and the frame it stops.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class TZPropMotion : MonoBehaviour
    {
        public TZMotionKind kind = TZMotionKind.None;
        public Vector3 localAxis = Vector3.up;   // hinge axis or slide direction (in parent space)
        public float amount = 95f;               // degrees for Hinge/Lift, meters for Slide
        public float duration = 0.55f;
        public AudioClip latchClip, stopClip;
        public Light[] lightsWhenOpen;           // e.g. fridge interior lamp
        public bool IsOpen { get; private set; }
        public bool Moving { get; private set; }

        Quaternion restRot; Vector3 restPos; AudioSource src; float cur;

        void Awake()
        {
            restRot = transform.localRotation;
            restPos = transform.localPosition;
            src = GetComponent<AudioSource>();
            if (!src && (latchClip || stopClip))
            {
                src = gameObject.AddComponent<AudioSource>();
                src.spatialBlend = 1f; src.minDistance = 0.4f; src.maxDistance = 8f; src.playOnAwake = false;
            }
            SetLights(false);
        }

        public void Play(bool open)
        {
            if (kind == TZMotionKind.None || open == IsOpen) return;
            StopAllCoroutines();
            StartCoroutine(Run(open));
        }

        static float EaseOpen(float t)
        {
            // fast start, decelerate, tiny settle (<2%) like a real hinge / runner stop
            float e = 1f - Mathf.Pow(1f - t, 3f);
            return e + Mathf.Sin(t * Mathf.PI) * 0.015f * (1f - t);
        }

        IEnumerator Run(bool open)
        {
            Moving = true;
            if (src && latchClip) src.PlayOneShot(latchClip, 0.8f);
            if (open) SetLights(true);
            float from = cur, to = open ? 1f : 0f, t = 0f;
            float d = Mathf.Max(0.05f, duration * (open ? 1f : 0.85f));
            while (t < 1f)
            {
                t += Time.deltaTime / d;
                float k = Mathf.Lerp(from, to, open ? EaseOpen(Mathf.Clamp01(t)) : Mathf.SmoothStep(0, 1, Mathf.Clamp01(t)));
                Apply(k);
                yield return null;
            }
            Apply(to);
            IsOpen = open;
            if (!open) SetLights(false);
            if (src && stopClip) src.PlayOneShot(stopClip, open ? 0.5f : 0.9f);
            Moving = false;
        }

        void Apply(float k)
        {
            cur = k;
            ApplyRaw(k);
        }

        void ApplyRaw(float k)
        {
            switch (kind)
            {
                case TZMotionKind.Hinge:
                case TZMotionKind.Lift:
                    transform.localRotation = restRot * Quaternion.AngleAxis(amount * k, localAxis);
                    break;
                case TZMotionKind.Slide:
                    transform.localPosition = restPos + localAxis.normalized * (amount * k);
                    break;
            }
        }

        void SetLights(bool on)
        {
            if (lightsWhenOpen == null) return;
            foreach (var l in lightsWhenOpen) if (l) l.enabled = on;
        }

        /// <summary>Start partly open (e.g. a door left ajar). Counts as open.</summary>
        public void SnapPartial(float k) { StopAllCoroutines(); Apply(k); IsOpen = true; Moving = false; }

        /// <summary>Restore saved state without animating (load game).</summary>
        public void Snap(bool open) { StopAllCoroutines(); Apply(open ? 1 : 0); IsOpen = open; SetLights(open); Moving = false; }
    }
}
