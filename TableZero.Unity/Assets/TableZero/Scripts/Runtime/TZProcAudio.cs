using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Code-synthesised interim sounds for the call → interrogation transition (no third-party audio, no licence).
    /// They are deliberately quiet and dry. Status: PROCEDURAL_PLACEHOLDER — to be replaced by recorded/licensed foley.
    /// </summary>
    public static class TZProcAudio
    {
        const int SR = 44100;
        static AudioClip roomTone, paper, step, door, recorder;

        static AudioClip Make(string name, float seconds, System.Func<float, System.Random, float> f, int seed = 1)
        {
            int n = Mathf.CeilToInt(seconds * SR); var d = new float[n]; var rnd = new System.Random(seed);
            for (int i = 0; i < n; i++) d[i] = Mathf.Clamp(f(i / (float)SR, rnd), -1f, 1f);
            var c = AudioClip.Create(name, n, 1, SR, false); c.SetData(d, 0); return c;
        }

        /// <summary>Interrogation-wing room tone: soft brown-noise air + faint 60 Hz ballast hum, loopable (crossfaded ends).</summary>
        public static AudioClip RoomTone()
        {
            if (roomTone) return roomTone;
            float brown = 0; const float L = 8f;
            var raw = new float[(int)(L * SR)]; var rnd = new System.Random(3);
            for (int i = 0; i < raw.Length; i++)
            {
                brown = Mathf.Clamp(brown + ((float)rnd.NextDouble() * 2 - 1) * 0.02f, -1, 1) * 0.998f;
                float t = i / (float)SR;
                raw[i] = brown * 0.22f + 0.012f * Mathf.Sin(2 * Mathf.PI * 60 * t) + 0.006f * Mathf.Sin(2 * Mathf.PI * 120 * t);
            }
            int fade = SR / 2;
            for (int i = 0; i < fade; i++) { float k = i / (float)fade; raw[i] = raw[i] * k + raw[raw.Length - fade + i] * (1 - k); }
            var c = AudioClip.Create("tz_roomtone", raw.Length - fade, 1, SR, false); var d = new float[raw.Length - fade];
            System.Array.Copy(raw, d, d.Length); c.SetData(d, 0); return roomTone = c;
        }

        /// <summary>Folder closed on a desk: paper slide (band noise) then a soft slap.</summary>
        public static AudioClip PaperClose()
        {
            if (paper) return paper;
            float lp = 0;
            return paper = Make("tz_paper", 0.55f, (t, r) =>
            {
                float n = (float)r.NextDouble() * 2 - 1; lp += (n - lp) * 0.35f;
                float slide = (n - lp) * Mathf.Exp(-Mathf.Pow((t - 0.12f) / 0.07f, 2)) * 0.35f;
                float slap = (t > 0.30f ? Mathf.Exp(-(t - 0.30f) * 38f) : 0f) * lp * 1.6f;
                return slide + slap;
            }, 11);
        }

        /// <summary>One footstep on a linoleum corridor: low thump + short scuff.</summary>
        public static AudioClip Step()
        {
            if (step) return step;
            float lp = 0;
            return step = Make("tz_step", 0.32f, (t, r) =>
            {
                float n = (float)r.NextDouble() * 2 - 1; lp += (n - lp) * 0.08f;
                float thump = Mathf.Sin(2 * Mathf.PI * 70 * t) * Mathf.Exp(-t * 30f) * 0.55f;
                float scuff = lp * Mathf.Exp(-t * 18f) * 0.9f;
                return thump + scuff;
            }, 23);
        }

        /// <summary>Interrogation-room door: latch click, short hinge groan, soft close.</summary>
        public static AudioClip Door()
        {
            if (door) return door;
            float lp = 0;
            return door = Make("tz_door", 1.2f, (t, r) =>
            {
                float n = (float)r.NextDouble() * 2 - 1; lp += (n - lp) * 0.2f;
                float click = (t < 0.025f ? n * (1 - t / 0.025f) : 0f) * 0.7f;
                float f = 180 + 90 * Mathf.Sin(t * 7f);
                float groan = (t > 0.08f && t < 0.75f ? Mathf.Sin(2 * Mathf.PI * f * t) * 0.05f * Mathf.Sin((t - 0.08f) / 0.67f * Mathf.PI) : 0f);
                float shut = (t > 0.9f ? Mathf.Exp(-(t - 0.9f) * 25f) * lp * 1.3f : 0f);
                return click + groan + shut;
            }, 31);
        }

        /// <summary>Desk voice recorder: switch click + short start beep.</summary>
        public static AudioClip Recorder()
        {
            if (recorder) return recorder;
            return recorder = Make("tz_recorder", 0.5f, (t, r) =>
            {
                float n = (float)r.NextDouble() * 2 - 1;
                float click = t < 0.012f ? n * 0.6f : 0f;
                float beep = (t > 0.18f && t < 0.30f ? Mathf.Sin(2 * Mathf.PI * 1850 * t) * 0.10f : 0f);
                return click + beep;
            }, 41);
        }
    }
}
