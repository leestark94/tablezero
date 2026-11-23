using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>
    /// Moving 2D suspect (UI Toolkit). The approved portrait is one painting, so the rig is a TWO-PART layer split at the shoulders:
    /// the whole picture (torso, room) stays as the stage background and a HEAD layer (same picture, clipped above the seam) is
    /// rotated/shifted about the neck seam. At the seam the displacement is zero, so it does not tear; amplitude is kept small
    /// (acting, not animation). Eyelids/mouth need separately painted layers — not available — so there is no blink or lip-sync here:
    /// speech is shown by restrained head/jaw-height pulses on word boundaries only while text is actually being spoken.
    /// Which beat plays is decided by the server from the DETECTIVE's action (accused / showed a record / insulted / pressed), never
    /// from whether the suspect is lying. Micro-movements are random with cooldowns, so no 3-second loop.
    /// </summary>
    public sealed class TZLivingPortrait2D
    {
        public enum Beat { Idle, Listening, Considering, Answering, Guarded, Challenged, Angry, Withdrawn }
        public static bool ReducedMotion;

        VisualElement clip, cam, sway, stageRef;
        float stageW = 0, stageH = 0, seam, widthFrac;
        Beat beat = Beat.Idle; float intensity = 0.3f; int lastSeq = -1;
        float t, nextMicro, mdx, mdy, mtilt, tdx, tdy, ttilt, dx, dy, tilt, impX, impY, pulse; bool speaking; System.Random rnd;
        public bool Active => clip != null && clip.style.display != DisplayStyle.None;

        public void Build(VisualElement stage, int seed, float seamFrac = 0.52f, float widthFraction = 0.46f)
        {
            seam = seamFrac; widthFrac = widthFraction; rnd = new System.Random(seed);
            clip = new VisualElement { pickingMode = PickingMode.Ignore }; clip.style.position = Position.Absolute; clip.style.top = 0; clip.style.overflow = Overflow.Hidden; clip.style.display = DisplayStyle.None;
            cam = new VisualElement { pickingMode = PickingMode.Ignore }; cam.style.position = Position.Absolute; cam.style.top = 0;
            sway = new VisualElement { pickingMode = PickingMode.Ignore }; sway.style.position = Position.Absolute; sway.style.left = 0; sway.style.top = 0; sway.style.right = 0; sway.style.bottom = 0;
            sway.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Cover);
            cam.Add(sway); clip.Add(cam);
            stage.Add(clip);
            stageRef = stage;
        }

        /// <summary>The head layer sits right above the stage image (below the grain/vignette added later by the caller).</summary>
        public void MoveBelow(VisualElement sibling) { if (clip != null && sibling != null) clip.PlaceBehind(sibling); }

        void Layout(float w, float h)
        {
            if (float.IsNaN(w) || float.IsNaN(h) || w < 10 || h < 10 || clip == null) return;
            stageW = w; stageH = h;
            float cw = w * widthFrac, left = (w - cw) * 0.5f;
            clip.style.left = left; clip.style.width = cw; clip.style.height = h * seam;
            cam.style.left = -left; cam.style.width = w; cam.style.height = h;
            sway.style.transformOrigin = new TransformOrigin(w * 0.5f, h * seam);   // pivot = the neck seam
        }

        public void SetImage(Texture2D tex)
        {
            if (clip == null) return;
            sway.style.backgroundImage = tex; clip.style.display = tex != null ? DisplayStyle.Flex : DisplayStyle.None;
            Reset();
        }

        public void Hide() { if (clip != null) clip.style.display = DisplayStyle.None; }
        void Reset() { beat = Beat.Idle; lastSeq = -1; speaking = false; dx = dy = tilt = impX = impY = pulse = 0; }

        public void SetBeat(string name, float inten, int seq = -1)
        {
            if (seq >= 0) { if (seq <= lastSeq) return; lastSeq = seq; }   // stale performance events (an older answer) are dropped
            if (!Enum.TryParse(name, out Beat b)) b = Beat.Idle;
            if (b != beat && (b == Beat.Challenged || b == Beat.Angry)) { impX = (float)(rnd.NextDouble() - 0.5) * 3f; impY = -2.2f; }   // a small sharp shift, once
            beat = b; intensity = Mathf.Clamp01(inten);
        }
        public void SetBeat(Beat b, float inten = 0.3f) { SetBeat(b.ToString(), inten, -1); }
        public void SetSpeaking(bool on) { speaking = on; if (!on && beat == Beat.Answering) beat = Beat.Idle; }
        /// <summary>One call per spoken word: a tiny nod.</summary>
        public void Pulse() { if (speaking) pulse = 1f; }

        static void Params(Beat b, float k, out float baseDx, out float baseDy, out float baseTilt, out float amp)
        {
            switch (b)
            {
                case Beat.Listening:   baseDx = 0f; baseDy = -1.6f; baseTilt = 0.30f; amp = 0.8f; break;
                case Beat.Considering: baseDx = 2.6f; baseDy = 0.6f; baseTilt = -0.55f; amp = 0.7f; break;
                case Beat.Answering:   baseDx = 0f; baseDy = 0f; baseTilt = 0.05f; amp = 1.0f; break;
                case Beat.Guarded:     baseDx = 0f; baseDy = 2.6f * k + 1f; baseTilt = 0f; amp = 0.35f; break;
                case Beat.Challenged:  baseDx = 0f; baseDy = -1.8f; baseTilt = 0.15f; amp = 0.4f; break;
                case Beat.Angry:       baseDx = 0f; baseDy = -1.2f; baseTilt = 0f; amp = 1.1f; break;
                case Beat.Withdrawn:   baseDx = -2f; baseDy = 4.2f * k + 1f; baseTilt = -0.2f; amp = 0.3f; break;
                default:               baseDx = 0f; baseDy = 0f; baseTilt = 0f; amp = 0.8f; break;
            }
        }

        /// <summary>camScale/camTranslate: the exact transform the stage background uses (camera drift + breathing), so the head layer stays glued to it.</summary>
        public void Tick(float dt, Vector3 camScale, Vector2 camTranslate)
        {
            if (!Active) return;
            var rs = stageRef.resolvedStyle; if (Mathf.Abs(rs.width - stageW) > 0.5f || Mathf.Abs(rs.height - stageH) > 0.5f) Layout(rs.width, rs.height);   // follows window resizes
            t += dt; float m = ReducedMotion ? 0.3f : 1f, px = stageH / 1080f;
            cam.style.scale = new Scale(camScale); cam.style.translate = new Translate(camTranslate.x, camTranslate.y);
            Params(beat, intensity, out float bdx, out float bdy, out float btilt, out float amp);
            // random micro head-turns with cooldown (2.5 - 7 s): never a fixed loop
            if (t >= nextMicro)
            {
                nextMicro = t + 2.5f + (float)rnd.NextDouble() * 4.5f;
                float a = amp * m; mdx = ((float)rnd.NextDouble() * 2f - 1f) * 1.6f * a; mdy = ((float)rnd.NextDouble() * 2f - 1f) * 1.0f * a; mtilt = ((float)rnd.NextDouble() * 2f - 1f) * 0.14f * a;
            }
            float breath = Mathf.Sin(t * (beat == Beat.Angry ? 1.5f : beat == Beat.Withdrawn ? 0.55f : 0.9f)) * (beat == Beat.Angry ? 1.1f : 0.8f) * amp * m;
            float jitter = beat == Beat.Angry ? Mathf.Sin(t * 43f) * 0.05f * m : 0f;
            tdx = bdx * m + mdx; tdy = bdy * m + mdy + breath; ttilt = btilt * m + mtilt + jitter;
            float k = 1f - Mathf.Exp(-3.2f * dt);
            dx = Mathf.Lerp(dx, tdx, k); dy = Mathf.Lerp(dy, tdy, k); tilt = Mathf.Lerp(tilt, ttilt, k);
            impX *= Mathf.Exp(-6f * dt); impY *= Mathf.Exp(-6f * dt); pulse *= Mathf.Exp(-9f * dt);
            float nod = pulse * 1.8f * m;
            sway.style.translate = new Translate((dx + impX * m) * px, (dy + impY * m + nod) * px);
            sway.style.rotate = new Rotate(tilt);
        }
    }
}
