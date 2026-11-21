using System;
using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Acting layer for a seated, rigged suspect (Unity Humanoid avatar). Never decides anything about the case:
    /// it only turns the server-validated reply_mode / motion_id into body behaviour.
    ///
    /// Layers, evaluated every frame in LateUpdate:
    ///  1. Pose presets (muscle space) cross-faded by weight — seated rest, lean back/forward, look down, hand to mouth, arms crossed.
    ///  2. Procedural life: breathing (chest/shoulders), blinks (shape keys, irregular, occasional double/half blink), eye saccades,
    ///     head micro drift, finger micro motion, weight shifts on a cooldown — tuned per person (Profile), so nothing loops visibly.
    ///  3. Speaking: jaw + mouth shape keys on a syllable rhythm derived from the line (placeholder until TTS visemes exist).
    ///  4. Contact IK: two-bone arm IK keeps resting palms on the tabletop; table_slam fires OnTableContact on the real contact frame.
    /// Motions the rig cannot perform are refused and logged (never reported as played).
    /// </summary>
    public sealed class TZSuspectActor : MonoBehaviour
    {
        [Serializable] public class Profile
        {
            public float breathPeriod = 4.4f;      // seconds per breath at rest
            public float fidget = 0.5f;            // 0 still … 1 restless (finger/weight-shift rate)
            public float gazeAversion = 0.5f;      // how often gaze leaves the detective while listening
            public float headDown = 0.35f;         // resting head-down bias (keeps the upper face in the pendant's shadow)
        }

        public enum State { Listen, Think, Speak, Silence, ReviewEvidence, Reposition, Resist, RequestCounsel, EndInterview }

        public Animator animator;
        public SkinnedMeshRenderer face;
        public Transform lookTarget;               // detective camera
        public Transform tableTop;                 // a transform on the table surface (y = top)
        public Transform restLeft, restRight;      // palm rest targets on the table
        public Profile profile = new Profile();
        public float seatHeight = 0.455f;

        public event Action<string, Vector3> OnTableContact;   // ("left"/"right", world position)
        public State state { get; private set; } = State.Listen;
        public readonly List<string> missingMotions = new List<string>();

        HumanPoseHandler handler; HumanPose pose; int muscleCount;
        readonly Dictionary<string, int> mIndex = new Dictionary<string, int>();
        readonly Dictionary<string, Dictionary<string, float>> presets = new Dictionary<string, Dictionary<string, float>>();
        readonly Dictionary<string, float> weight = new Dictionary<string, float>(), weightTarget = new Dictionary<string, float>();
        float[] baseMuscles;
        Vector3 bodyPos; Quaternion bodyRot;

        // procedural state
        float nextBlink, blinkT = -1, blinkLen = 0.14f, blinkDepth = 1f; bool doubleBlink;
        Vector2 eye, eyeTarget; float nextSaccade;
        float nextShift; Vector2 shift, shiftTarget;
        float speakUntil, speakStart; string speakText = ""; float jaw;
        float gazeAwayUntil; Vector2 gazeAway;
        readonly Dictionary<string, int> shapeIdx = new Dictionary<string, int>();
        Coroutine gesture; float slamLift;
        static readonly System.Random rng = new System.Random();
        static float R(float a, float b) => a + (float)rng.NextDouble() * (b - a);

        // -------------------------------------------------------------------------------------------------- setup
        void Awake()
        {
            if (!animator) animator = GetComponentInChildren<Animator>();
            handler = new HumanPoseHandler(animator.avatar, animator.transform);
            handler.GetHumanPose(ref pose);
            muscleCount = HumanTrait.MuscleCount;
            for (int i = 0; i < muscleCount; i++) mIndex[HumanTrait.MuscleName[i]] = i;
            baseMuscles = new float[muscleCount];
            bodyPos = pose.bodyPosition; bodyRot = pose.bodyRotation;
            if (face && face.sharedMesh)
                for (int i = 0; i < face.sharedMesh.blendShapeCount; i++) shapeIdx[face.sharedMesh.GetBlendShapeName(i)] = i;
            BuildPresets();
            foreach (var k in presets.Keys) { weight[k] = 0; weightTarget[k] = 0; }
            weight["rest"] = weightTarget["rest"] = 1;
            nextBlink = Time.time + R(1f, 3f); nextSaccade = Time.time + R(0.5f, 1.5f); nextShift = Time.time + R(6f, 12f);
        }

        void BuildPresets()
        {
            // Values are Unity muscle units (-1..1). "rest" = seated, forearms on the table, shoulders slightly rounded.
            var sit = new Dictionary<string, float>
            {
                {"Left Upper Leg Front-Back", -0.68f}, {"Right Upper Leg Front-Back", -0.68f},
                {"Left Lower Leg Stretch", -0.70f}, {"Right Lower Leg Stretch", -0.70f},
                {"Left Upper Leg In-Out", -0.08f}, {"Right Upper Leg In-Out", -0.08f},
                {"Left Foot Up-Down", 0.15f}, {"Right Foot Up-Down", 0.15f},
                {"Spine Front-Back", -0.30f}, {"Chest Front-Back", -0.22f}, {"UpperChest Front-Back", -0.10f},
                {"Neck Nod Down-Up", -0.05f}, {"Head Nod Down-Up", 0.0f},
                {"Left Shoulder Front-Back", 0.15f}, {"Right Shoulder Front-Back", 0.15f},
                {"Left Shoulder Down-Up", -0.05f}, {"Right Shoulder Down-Up", -0.05f},
                {"Left Arm Down-Up", -0.45f}, {"Right Arm Down-Up", -0.45f},
                {"Left Arm Front-Back", -0.45f}, {"Right Arm Front-Back", -0.45f},
                {"Left Arm Twist In-Out", 0.0f}, {"Right Arm Twist In-Out", 0.0f},
                {"Left Forearm Stretch", -0.40f}, {"Right Forearm Stretch", -0.40f},
                {"Left Forearm Twist In-Out", -0.55f}, {"Right Forearm Twist In-Out", -0.55f},
                {"Left Hand Down-Up", -0.05f}, {"Right Hand Down-Up", -0.05f},
            };
            foreach (var side in new[] { "Left", "Right" })
                foreach (var f in new[] { "Thumb", "Index", "Middle", "Ring", "Little" })
                {
                    float curl = f == "Thumb" ? 0.35f : f == "Index" ? 0.25f : f == "Little" ? 0.05f : 0.15f;   // relaxed half-curl, graded
                    sit[$"{side} {f} 1 Stretched"] = curl; sit[$"{side} {f} 2 Stretched"] = curl - 0.1f; sit[$"{side} {f} 3 Stretched"] = curl - 0.1f;
                }
            presets["rest"] = sit;
            presets["lean_back"] = new Dictionary<string, float> { {"Spine Front-Back", 0.45f}, {"Chest Front-Back", 0.25f}, {"Head Nod Down-Up", 0.10f},
                {"Left Arm Front-Back", 0.25f}, {"Right Arm Front-Back", 0.25f}, {"Left Forearm Stretch", 0.15f}, {"Right Forearm Stretch", 0.15f} };
            presets["lean_forward"] = new Dictionary<string, float> { {"Spine Front-Back", -0.25f}, {"Chest Front-Back", -0.15f}, {"Head Nod Down-Up", -0.05f} };
            presets["look_down"] = new Dictionary<string, float> { {"Neck Nod Down-Up", -0.25f}, {"Head Nod Down-Up", -0.45f}, {"Left Eye Down-Up", -0.5f}, {"Right Eye Down-Up", -0.5f} };
            presets["hand_to_mouth"] = new Dictionary<string, float> { {"Right Arm Front-Back", -0.15f}, {"Right Arm Down-Up", 0.25f}, {"Right Forearm Stretch", -0.55f},
                {"Right Hand Down-Up", 0.35f}, {"Right Index 1 Stretched", 0.35f}, {"Right Middle 1 Stretched", 0.45f}, {"Head Nod Down-Up", -0.15f} };
            presets["arms_crossed"] = new Dictionary<string, float> { {"Left Arm Front-Back", 0.25f}, {"Right Arm Front-Back", 0.25f}, {"Left Forearm Stretch", -0.6f},
                {"Right Forearm Stretch", -0.6f}, {"Left Arm Twist In-Out", 0.5f}, {"Right Arm Twist In-Out", 0.5f}, {"Spine Front-Back", 0.2f} };
            presets["jaw_tight"] = new Dictionary<string, float> { {"Neck Nod Down-Up", 0.05f} };
            presets["slam"] = new Dictionary<string, float> { {"Left Arm Down-Up", 0.25f}, {"Right Arm Down-Up", 0.25f}, {"Left Forearm Stretch", 0.25f},
                {"Right Forearm Stretch", 0.25f}, {"Spine Front-Back", -0.2f}, {"Head Nod Down-Up", -0.1f} };
        }

        // -------------------------------------------------------------------------------------------------- public API
        public void SetState(State s)
        {
            state = s;
            switch (s)
            {
                case State.Listen: Blend("look_down", profile.headDown * 0.6f, 0.9f); break;
                case State.Think: Blend("look_down", 0.55f + profile.gazeAversion * 0.3f, 0.7f); gazeAwayUntil = Time.time + R(1.2f, 2.4f); gazeAway = new Vector2(R(-0.4f, 0.4f), R(-0.5f, -0.2f)); break;
                case State.Speak: Blend("look_down", profile.headDown * 0.4f, 0.5f); break;
                case State.Silence: Blend("look_down", 0.7f, 1.4f); break;
                case State.ReviewEvidence: Blend("look_down", 1f, 0.6f); Blend("lean_forward", 0.6f, 0.8f); break;
                case State.Resist: Blend("lean_back", 0.7f, 0.6f); Blend("look_down", 0.1f, 0.6f); break;
                case State.RequestCounsel: Blend("lean_back", 0.9f, 0.9f); Blend("arms_crossed", 0.8f, 1.0f); break;
                case State.EndInterview: Blend("lean_back", 0.5f, 1.2f); break;
            }
        }

        /// <summary>Speak a validated line: short pre-speech breath, then jaw/mouth rhythm for the line's length.</summary>
        public void Speak(string line, string replyMode, string motion)
        {
            speakText = line ?? ""; speakStart = Time.time + 0.45f;   // breath in before the first syllable
            int syll = 0; foreach (var c in speakText) if (c >= 0xAC00 && c <= 0xD7A3 || char.IsLetterOrDigit(c)) syll++;
            speakUntil = speakStart + Mathf.Clamp(syll * 0.16f, 0.6f, 14f);
            SetState(replyMode == "silence" ? State.Silence : replyMode == "angry" || replyMode == "counter" ? State.Resist :
                     replyMode == "request_counsel" ? State.RequestCounsel : State.Speak);
            if (!string.IsNullOrEmpty(motion)) PlayMotion(motion);
        }

        public bool PlayMotion(string id)
        {
            switch (id)
            {
                case "still": return true;
                case "look_down": Pulse("look_down", 0.9f, 0.5f, R(1.6f, 2.6f)); return true;
                case "avoid_gaze": gazeAwayUntil = Time.time + R(1.5f, 3f); gazeAway = new Vector2(R(-0.6f, 0.6f) > 0 ? 0.55f : -0.55f, R(-0.3f, 0.1f)); return true;
                case "lean_back": case "back_in_chair": Blend("lean_back", 0.8f, 1.1f); return true;
                case "lean_forward": Blend("lean_forward", 0.8f, 0.9f); return true;
                case "cross_arms": Blend("arms_crossed", 0.9f, 1.0f); return true;
                case "deep_breath": breathBoost = 1.8f; return true;
                case "exhale": exhaleT = Time.time; return true;
                case "shift_chair": case "chair_shift": shiftTarget = new Vector2(R(-1f, 1f), R(-1f, 1f)); nextShift = Time.time + R(6f, 10f); return true;
                case "hand_stop": fingerFreezeUntil = Time.time + R(1.5f, 3f); return true;
                case "finger_tap": tapUntil = Time.time + R(1.8f, 3.2f); return true;
                case "jaw_tight": jawTightUntil = Time.time + R(1.5f, 2.5f); return true;
                case "table_slam": if (gesture != null) StopCoroutine(gesture); gesture = StartCoroutine(Slam()); return true;
                case "cup_touch": Pulse("hand_to_mouth", 0.35f, 0.6f, 1.2f); return true;   // TODO: IK reach to the cup handle
                default:
                    if (!missingMotions.Contains(id)) missingMotions.Add(id);
                    Debug.LogWarning("[TZSuspectActor] motion not available on this rig: " + id);
                    return false;
            }
        }

        float breathBoost = 1f, exhaleT = -10f, fingerFreezeUntil, tapUntil, jawTightUntil;

        void Blend(string preset, float w, float seconds) { weightTarget[preset] = w; blendRate[preset] = 1f / Mathf.Max(0.05f, seconds); }
        readonly Dictionary<string, float> blendRate = new Dictionary<string, float>();
        void Pulse(string preset, float w, float inSec, float hold) { StartCoroutine(PulseCo(preset, w, inSec, hold)); }
        System.Collections.IEnumerator PulseCo(string p, float w, float inSec, float hold)
        {
            float prev = weightTarget[p]; Blend(p, w, inSec);
            yield return new WaitForSeconds(inSec + hold);
            Blend(p, prev, inSec * 1.4f);
        }

        System.Collections.IEnumerator Slam()
        {
            Blend("slam", 1f, 0.35f); slamLift = 0f;
            float t = 0;
            while (t < 0.35f) { t += Time.deltaTime; slamLift = Mathf.SmoothStep(0, 0.16f, t / 0.35f); yield return null; }
            t = 0;
            while (t < 0.09f) { t += Time.deltaTime; slamLift = Mathf.Lerp(0.16f, 0f, t / 0.09f); yield return null; }
            slamLift = 0f;
            var lh = animator.GetBoneTransform(HumanBodyBones.LeftHand); var rh = animator.GetBoneTransform(HumanBodyBones.RightHand);
            OnTableContact?.Invoke("left", lh ? lh.position : transform.position);
            OnTableContact?.Invoke("right", rh ? rh.position : transform.position);
            yield return new WaitForSeconds(0.6f);
            Blend("slam", 0f, 0.8f); gesture = null;
        }

        // -------------------------------------------------------------------------------------------------- per-frame
        void LateUpdate()
        {
            float dt = Time.deltaTime, t = Time.time;
            foreach (var k in presets.Keys)
            {
                float rate = blendRate.TryGetValue(k, out var r) ? r : 1.5f;
                weight[k] = Mathf.MoveTowards(weight[k], weightTarget[k], rate * dt);
            }
            for (int i = 0; i < muscleCount; i++) baseMuscles[i] = 0f;
            foreach (var kv in presets)
            {
                float w = kv.Key == "rest" ? 1f : SmoothW(weight[kv.Key]);
                if (w <= 0f) continue;
                foreach (var m in kv.Value) if (mIndex.TryGetValue(m.Key, out var idx)) baseMuscles[idx] += m.Value * w;
            }

            // breathing — irregular period, occasional deeper breath, exhale slump
            float period = profile.breathPeriod * (1f + 0.12f * (Mathf.PerlinNoise(t * 0.05f, 2f) - 0.5f));
            float br = Mathf.Sin(t * 2f * Mathf.PI / period) * 0.5f + 0.5f;
            float amp = 0.035f * breathBoost; breathBoost = Mathf.MoveTowards(breathBoost, 1f, dt * 0.25f);
            float ex = Mathf.Clamp01(1f - (t - exhaleT) / 2.2f) * Mathf.Sin(Mathf.Clamp01((t - exhaleT) / 2.2f) * Mathf.PI);
            Add("Chest Front-Back", br * amp - ex * 0.08f); Add("UpperChest Front-Back", br * amp * 0.8f);
            Add("Left Shoulder Down-Up", br * amp * 0.9f - ex * 0.08f); Add("Right Shoulder Down-Up", br * amp * 0.9f - ex * 0.08f);
            Add("Neck Nod Down-Up", -ex * 0.06f);

            // weight shifts on a cooldown (never periodic)
            if (t > nextShift) { shiftTarget = new Vector2(R(-1f, 1f), R(-0.6f, 0.6f)) * profile.fidget; nextShift = t + R(7f, 16f) / Mathf.Max(0.3f, profile.fidget + 0.3f); }
            shift = Vector2.Lerp(shift, shiftTarget, 1f - Mathf.Exp(-dt * 1.2f));
            Add("Spine Left-Right", shift.x * 0.06f); Add("Spine Twist Left-Right", shift.y * 0.05f); Add("Head Tilt Left-Right", -shift.x * 0.05f);

            // head: micro drift + look at the detective (or away), speaking nods
            float hx = (Mathf.PerlinNoise(t * 0.11f, 7f) - 0.5f) * 0.10f, hy = (Mathf.PerlinNoise(t * 0.09f, 3f) - 0.5f) * 0.08f;
            Vector2 look = LookAngles();
            bool away = t < gazeAwayUntil;
            if (away) look = gazeAway;
            Add("Head Turn Left-Right", hx + look.x * 0.45f); Add("Head Nod Down-Up", hy + look.y * 0.12f - profile.headDown * 0.42f); Add("Neck Nod Down-Up", -profile.headDown * 0.15f);
            bool speaking = t > speakStart && t < speakUntil;
            if (speaking) Add("Head Nod Down-Up", Mathf.Sin(t * 5.3f) * 0.02f + Mathf.Sin(t * 1.7f) * 0.03f);

            // eyes: saccades toward the gaze target, small fixational jitter
            if (t > nextSaccade)
            {
                eyeTarget = (away ? gazeAway : look) * 0.6f + new Vector2(R(-0.12f, 0.12f), R(-0.08f, 0.08f));
                nextSaccade = t + R(0.4f, 2.2f) * (state == State.Think ? 0.6f : 1f);
            }
            eye = Vector2.Lerp(eye, eyeTarget, 1f - Mathf.Exp(-dt * 28f));
            Add("Left Eye In-Out", eye.x); Add("Right Eye In-Out", -eye.x); Add("Left Eye Down-Up", eye.y); Add("Right Eye Down-Up", eye.y);

            // fingers: slow independent micro motion, freezes on "hand_stop", tapping on "finger_tap"
            if (t > fingerFreezeUntil)
            {
                int f = 0;
                foreach (var side in new[] { "Left", "Right" })
                    foreach (var fn in new[] { "Index", "Middle", "Ring", "Little", "Thumb" })
                    {
                        float n = (Mathf.PerlinNoise(t * (0.15f + 0.1f * profile.fidget), f * 3.7f) - 0.5f) * 0.18f * (0.4f + profile.fidget); f++;
                        Add($"{side} {fn} 1 Stretched", n); Add($"{side} {fn} 2 Stretched", n * 0.7f);
                    }
            }
            if (t < tapUntil) Add("Right Index 1 Stretched", Mathf.Abs(Mathf.Sin(t * 11f)) * 0.35f);

            // jaw / mouth while speaking (syllable rhythm, not lip-sync), tight jaw on request
            float jawTarget = 0f;
            if (speaking) jawTarget = Mathf.Clamp01(Mathf.Abs(Mathf.Sin(t * 14.5f)) * 0.8f + Mathf.PerlinNoise(t * 9f, 1f) * 0.3f) * 0.55f;
            jaw = Mathf.Lerp(jaw, jawTarget, 1f - Mathf.Exp(-dt * 22f));
            Add("Jaw Close", -jaw * 0.25f);
            SetShape("fx_mouth_open", jaw * 55f);
            SetShape("fx_mouth_compression", t < jawTightUntil ? 60f : 0f);

            // blinks: irregular, sometimes double or half; slower and more frequent when thinking/stressed
            if (blinkT < 0 && t > nextBlink) { blinkT = 0; blinkLen = R(0.11f, 0.18f); blinkDepth = rng.NextDouble() < 0.12 ? 0.55f : 1f; doubleBlink = rng.NextDouble() < 0.14; }
            float blink = 0f;
            if (blinkT >= 0)
            {
                blinkT += dt; float k = blinkT / blinkLen;
                blink = k < 0.4f ? k / 0.4f : 1f - (k - 0.4f) / 0.6f;
                if (k >= 1f)
                {
                    blinkT = doubleBlink ? -0.001f : -1f;
                    if (doubleBlink) { doubleBlink = false; blinkT = -1f; nextBlink = t + 0.12f; }
                    else nextBlink = t + R(2.2f, 6.5f) * (state == State.Think || state == State.Resist ? 0.6f : 1f);
                }
            }
            blink = Mathf.Clamp01(blink) * blinkDepth;
            SetShape("fx_eye_left_closure", blink * 100f); SetShape("fx_eye_right_closure", blink * 100f);
            // upper lids follow gaze down (natural lid-gaze coupling)
            SetShape("fx_eye_left_slit", Mathf.Clamp01(-eye.y) * 35f); SetShape("fx_eye_right_slit", Mathf.Clamp01(-eye.y) * 35f);

            for (int i = 0; i < muscleCount; i++) pose.muscles[i] = Mathf.Clamp(baseMuscles[i], -1f, 1f);
            pose.bodyPosition = bodyPos; pose.bodyRotation = bodyRot;
            handler.SetHumanPose(ref pose);
            if (seatAnchor) SnapToSeat();
            HandContactIK();
        }

        static float SmoothW(float w) => w * w * (3f - 2f * w);
        void Add(string muscle, float v) { if (mIndex.TryGetValue(muscle, out var i)) baseMuscles[i] += v; }
        void SetShape(string n, float v) { if (face && shapeIdx.TryGetValue(n, out var i)) face.SetBlendShapeWeight(i, Mathf.Clamp(v, 0f, 100f)); }

        Vector2 LookAngles()
        {
            var head = animator.GetBoneTransform(HumanBodyBones.Head);
            if (!head || !lookTarget) return Vector2.zero;
            var local = transform.InverseTransformDirection((lookTarget.position - head.position).normalized);
            return new Vector2(Mathf.Clamp(Mathf.Atan2(local.x, local.z) / 1.2f, -1f, 1f), Mathf.Clamp(local.y * 1.4f, -1f, 1f));
        }

        // ------------------------------------------------------------------------------- seat + hand contact
        public Transform seatAnchor;   // seat-surface point; hips are kept on it after the muscle pose
        void SnapToSeat()
        {
            var lu = animator.GetBoneTransform(HumanBodyBones.LeftUpperLeg); var ru = animator.GetBoneTransform(HumanBodyBones.RightUpperLeg);
            if (!lu || !ru) return;
            Vector3 hipMid = (lu.position + ru.position) * 0.5f;
            Vector3 want = seatAnchor.position + Vector3.up * 0.085f + seatAnchor.forward * 0.02f;   // thigh-joint height above the cushion
            animator.transform.position += want - hipMid;
        }

        void HandContactIK()
        {
            if (!tableTop) return;
            float topY = tableTop.position.y;
            Solve(HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand, restLeft, topY, weight["rest"] * (1f - SmoothW(weight["arms_crossed"])) * (1f - SmoothW(weight["lean_back"])));
            Solve(HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand, restRight, topY,
                  (1f - SmoothW(weight["hand_to_mouth"])) * (1f - SmoothW(weight["arms_crossed"])) * (1f - SmoothW(weight["lean_back"])));
        }

        void Solve(HumanBodyBones ub, HumanBodyBones lb, HumanBodyBones hb, Transform rest, float topY, float w)
        {
            var u = animator.GetBoneTransform(ub); var l = animator.GetBoneTransform(lb); var h = animator.GetBoneTransform(hb);
            if (!u || !l || !h || w <= 0.001f) return;
            Vector3 target = rest ? rest.position : h.position;
            target.y = Mathf.Max(target.y, topY + 0.022f) + slamLift;                    // palm thickness above the laminate; slam lift
            target = Vector3.Lerp(h.position, target, w);
            if (h.position.y < topY + 0.018f) target.y = Mathf.Max(target.y, topY + 0.022f);   // never through the table
            TwoBone(u, l, h, target, u.position + transform.right * (ub == HumanBodyBones.LeftUpperArm ? -0.22f : 0.22f) + transform.forward * 0.05f + Vector3.down * 0.6f);
            // elbow rests on (never sinks into) the laminate
            if (l.position.y < topY + 0.035f) { var lp = l.position; lp.y = topY + 0.035f; TwoBone(u, l, h, target, lp + Vector3.down * 0.05f); }
        }

        static void TwoBone(Transform a, Transform b, Transform c, Vector3 target, Vector3 hint)
        {
            float la = (b.position - a.position).magnitude, lb = (c.position - b.position).magnitude;
            Vector3 at = target - a.position; float d = Mathf.Clamp(at.magnitude, Mathf.Abs(la - lb) + 1e-3f, la + lb - 1e-3f);
            Vector3 dir = at.normalized;
            Vector3 bend = Vector3.ProjectOnPlane(hint - a.position, dir).normalized;
            if (bend.sqrMagnitude < 1e-6f) bend = Vector3.ProjectOnPlane(b.position - a.position, dir).normalized;
            float cosA = Mathf.Clamp((la * la + d * d - lb * lb) / (2 * la * d), -1f, 1f);
            Vector3 elbow = a.position + dir * (la * cosA) + bend * (la * Mathf.Sqrt(1 - cosA * cosA));
            Quaternion ra = Quaternion.FromToRotation(b.position - a.position, elbow - a.position); a.rotation = ra * a.rotation;
            Quaternion rb = Quaternion.FromToRotation(c.position - b.position, a.position + dir * d - b.position); b.rotation = rb * b.rotation;
        }
    }
}
