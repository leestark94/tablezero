using System.IO;
using UnityEditor;
using UnityEngine;

namespace TableZero.EditorTools
{
    /// <summary>
    /// Procedural texture sets for room polish v4 (no third-party art):
    ///   gen_bloodpool    pooled blood: wet glossy centre, darker dried rim, satellite drops, meniscus in the normal map
    ///   gen_bloodsmear   CPR drag smear (u along the path, v across): drag striations, breaking up toward the end
    ///   gen_shoeprint    4-column atlas of a partial sole print, transfer strength 100 % .. 25 %
    ///   gen_bloodspatter 2-column atlas: drop cluster (horizontal) | runs/drips (vertical)
    ///   gen_printdoc     2-page A4 atlas: settlement table with pen corrections | continuation page
    ///   gen_nightwin     4-column atlas of neighbour windows at night: curtain glow | blinds | TV glow | dark
    /// Files follow the project convention {set}_{map}_2k.png (diff, nor_gl, metalsmooth).
    /// </summary>
    public static class TZProcTextures
    {
        public static bool Handles(string set) =>
            set == "gen_bloodpool" || set == "gen_bloodsmear" || set == "gen_shoeprint" || set == "gen_bloodspatter" ||
            set == "gen_printdoc" || set == "gen_nightwin";

        public static void Ensure(string dir, string set)
        {
            if (File.Exists(Path.Combine(dir, set + "_diff_2k.png"))) return;
            Directory.CreateDirectory(dir);
            switch (set)
            {
                case "gen_bloodpool": BloodPool(dir, set); break;
                case "gen_bloodsmear": BloodSmear(dir, set); break;
                case "gen_shoeprint": ShoePrint(dir, set); break;
                case "gen_bloodspatter": Spatter(dir, set); break;
                case "gen_printdoc": PrintDoc(dir, set); break;
                case "gen_nightwin": NightWin(dir, set); break;
            }
            AssetDatabase.Refresh();
        }

        // ------------------------------------------------------------------ helpers
        static float S(float a, float b, float x) { float t = Mathf.Clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); }
        static float Fbm(float x, float y, int oct = 4)
        {
            float a = 0.5f, f = 1, s = 0, n = 0;
            for (int i = 0; i < oct; i++) { s += a * Mathf.PerlinNoise(x * f + i * 17.3f, y * f + i * 9.1f); n += a; a *= 0.5f; f *= 2.03f; }
            return s / n;
        }
        static Color Blood(float wet) => Color.Lerp(new Color(0.085f, 0.018f, 0.012f), new Color(0.20f, 0.010f, 0.010f), wet);

        static void Save(string dir, string set, string map, Color[] px, int W, int H, bool linear)
        {
            var t = new Texture2D(W, H, TextureFormat.RGBA32, false, linear);
            t.SetPixels(px); t.Apply();
            string file = Path.Combine(dir, $"{set}_{map}_2k.png");
            File.WriteAllBytes(file, t.EncodeToPNG());
            Object.DestroyImmediate(t);
        }

        static Color[] Normal(float[] h, int W, int H, float k)
        {
            var n = new Color[W * H];
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float dx = h[y * W + Mathf.Min(x + 1, W - 1)] - h[y * W + Mathf.Max(x - 1, 0)];
                    float dy = h[Mathf.Min(y + 1, H - 1) * W + x] - h[Mathf.Max(y - 1, 0) * W + x];
                    var v = new Vector3(-dx * k, -dy * k, 1f).normalized;
                    n[y * W + x] = new Color(v.x * 0.5f + 0.5f, v.y * 0.5f + 0.5f, v.z * 0.5f + 0.5f, 1);
                }
            return n;
        }

        static void Decal(string dir, string set, Color[] alb, float[] h, float[] smooth, int W, int H, float nk)
        {
            Save(dir, set, "diff", alb, W, H, false);
            Save(dir, set, "nor_gl", Normal(h, W, H, nk), W, H, true);
            var ms = new Color[W * H];
            for (int i = 0; i < ms.Length; i++) ms[i] = new Color(0, 0, 0, smooth[i]);
            Save(dir, set, "metalsmooth", ms, W, H, true);
        }

        // ------------------------------------------------------------------ blood pool
        static void BloodPool(string dir, string set)
        {
            int N = 1024; var alb = new Color[N * N]; var h = new float[N * N]; var sm = new float[N * N];
            var rnd = new System.Random(302);
            float a1 = 1.1f, a2 = 2.3f, a3 = 4.0f, lobe = 0.6f;
            var drops = new Vector3[34];
            for (int i = 0; i < drops.Length; i++)
            {
                float ang = (float)rnd.NextDouble() * 6.283f, d = 0.70f + (float)rnd.NextDouble() * 0.27f;
                drops[i] = new Vector3(Mathf.Cos(ang) * d, Mathf.Sin(ang) * d, 0.006f + (float)rnd.NextDouble() * (i < 8 ? 0.03f : 0.012f));
            }
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float u = x / (float)N * 2 - 1, v = y / (float)N * 2 - 1;
                    float r = Mathf.Sqrt(u * u + v * v), th = Mathf.Atan2(v, u);
                    float dl = Mathf.DeltaAngle(th * Mathf.Rad2Deg, lobe * Mathf.Rad2Deg) * Mathf.Deg2Rad;
                    float R = 0.50f * (1 + 0.10f * Mathf.Sin(2 * th + a1) + 0.07f * Mathf.Sin(3 * th + a2) + 0.04f * Mathf.Sin(7 * th + a3))
                              + 0.22f * Mathf.Exp(-dl * dl / 0.12f) + (Fbm(u * 3 + 5, v * 3 + 5) - 0.5f) * 0.10f;
                    float d = R - r;                                  // distance inside the pool edge
                    float a = S(-0.004f, 0.006f, d);
                    float wet = S(0.03f, 0.22f, d);                   // thick centre still wet, edges dried first
                    float rim = Mathf.Exp(-Mathf.Pow((d - 0.018f) / 0.014f, 2)) * 0.8f;
                    foreach (var dp in drops)
                    {
                        float dd = dp.z - Mathf.Sqrt((u - dp.x) * (u - dp.x) + (v - dp.y) * (v - dp.y));
                        if (dd > -0.004f) { float da = S(-0.004f, 0.002f, dd); if (da > a) { a = da; wet = 0.15f; rim = 0.3f; d = dd; } }
                    }
                    var c = Blood(wet * (1 - rim * 0.6f));
                    c *= 0.9f + 0.2f * Fbm(u * 18, v * 18, 3);
                    c.a = a * 0.97f;
                    alb[y * N + x] = c;
                    h[y * N + x] = a * (0.35f + 0.65f * S(0f, 0.05f, d)) + rim * 0.15f;
                    sm[y * N + x] = Mathf.Lerp(0.38f, 0.93f, wet) * a;
                }
            Decal(dir, set, alb, h, sm, N, N, 9f);
        }

        // ------------------------------------------------------------------ CPR drag smear
        static void BloodSmear(string dir, string set)
        {
            int W = 2048, H = 512; var alb = new Color[W * H]; var h = new float[W * H]; var sm = new float[W * H];
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float u = x / (float)W, v = y / (float)H;
                    float edge = S(0f, 0.12f + 0.08f * Fbm(u * 12, 1), v) * S(0f, 0.12f + 0.08f * Fbm(u * 12, 7), 1 - v);
                    float streak = Mathf.PerlinNoise(v * 55f, u * 3f) * 0.7f + Mathf.PerlinNoise(v * 140f, u * 9f) * 0.3f;
                    float body = S(0.25f + u * 0.35f, 0.55f + u * 0.3f, streak + 0.25f * (1 - u));
                    float breakup = S(u * 0.85f, u * 0.85f + 0.12f, Fbm(u * 26, v * 6));      // gets patchy toward the end
                    float start = S(0f, 0.04f, u);
                    float a = Mathf.Clamp01(edge * body * breakup * start * 1.15f);
                    var c = Blood(0.15f * (1 - u)) * (0.85f + 0.3f * streak);
                    c.a = a * 0.92f;
                    alb[y * W + x] = c;
                    h[y * W + x] = a * (0.4f + 0.6f * streak);
                    sm[y * W + x] = (0.32f + 0.25f * (1 - u)) * a;
                }
            Decal(dir, set, alb, h, sm, W, H, 4f);
        }

        // ------------------------------------------------------------------ partial sole print
        static float SoleHalfWidth(float y)
        {   // y: 0 heel .. 1 toe; half width in [-1, 1] column space (heel, arch, ball, toe)
            float[] ys = { 0.0f, 0.14f, 0.38f, 0.66f, 0.90f, 1.0f };
            float[] ws = { 0.30f, 0.62f, 0.44f, 0.86f, 0.58f, 0.20f };
            for (int i = 0; i < ys.Length - 1; i++)
                if (y <= ys[i + 1]) { float t = (y - ys[i]) / (ys[i + 1] - ys[i]); t = t * t * (3 - 2 * t); return Mathf.Lerp(ws[i], ws[i + 1], t); }
            return 0.2f;
        }

        static void ShoePrint(string dir, string set)
        {
            int W = 1536, H = 1024, cw = W / 4; var alb = new Color[W * H]; var h = new float[W * H]; var sm = new float[W * H];
            float[] strength = { 0.95f, 0.70f, 0.45f, 0.28f };
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int col = x / cw;
                    float sx = ((x % cw) / (float)cw) * 2 - 1, sy = y / (float)H;
                    float yy = (sy - 0.03f) / 0.94f;
                    if (yy < 0 || yy > 1) { alb[y * W + x] = new Color(0, 0, 0, 0); continue; }
                    float hw = SoleHalfWidth(yy) * 0.92f;
                    float edgeD = hw - Mathf.Abs(sx + 0.05f * Mathf.Sin(yy * 3f));       // slight outward curve of a right sole
                    float inside = S(0f, 0.04f, edgeD);
                    // fine zig-zag tread on the forefoot, transverse blocks on the heel, a smooth arch
                    float zig = Mathf.Sin(yy * 210f + Mathf.Abs(sx) * 14f);
                    float blocks = Mathf.Sin(yy * 120f) * Mathf.Sin(sx * 16f);
                    float tread = yy > 0.45f ? S(-0.2f, 0.4f, zig) : yy < 0.28f ? S(-0.3f, 0.3f, blocks + 0.2f) : 0.25f;
                    float rim = S(0.10f, 0.0f, edgeD) * inside;
                    // blood transfers mostly at ball and heel, patchy, weaker with every step
                    float load = Mathf.Max(Mathf.Exp(-Mathf.Pow((yy - 0.68f) / 0.22f, 2)), 0.8f * Mathf.Exp(-Mathf.Pow((yy - 0.14f) / 0.12f, 2)));
                    float patch = Fbm(sx * 2.5f + col * 11, yy * 7 + col * 3);
                    float transfer = S(1.05f - strength[col] - 0.12f, 1.05f - strength[col] + 0.12f, patch * 0.7f + load * 0.55f);
                    float a = inside * Mathf.Max(tread * 0.85f, rim) * transfer * (0.45f + 0.35f * strength[col]);
                    var c = Blood(0.08f) * (1.1f + 0.2f * patch); c.a = Mathf.Clamp01(a);
                    alb[y * W + x] = c; h[y * W + x] = a * 0.25f; sm[y * W + x] = 0.25f * a;
                }
            Decal(dir, set, alb, h, sm, W, H, 3f);
        }

        // ------------------------------------------------------------------ spatter | drips
        static void Spatter(string dir, string set)
        {
            int W = 2048, H = 1024, half = 1024; var alb = new Color[W * H]; var h = new float[W * H]; var sm = new float[W * H];
            var rnd = new System.Random(7);
            // drops: (cx, cy, r, elong angle, elong)
            var drops = new Vector4[60]; var el = new float[60];
            for (int i = 0; i < drops.Length; i++)
            {
                float d = Mathf.Pow((float)rnd.NextDouble(), 0.6f) * 0.8f, ang = (float)rnd.NextDouble() * 6.283f;
                drops[i] = new Vector4(Mathf.Cos(ang) * d, Mathf.Sin(ang) * d, 0.012f + (float)rnd.NextDouble() * (i < 6 ? 0.07f : 0.025f), ang);
                el[i] = d > 0.35f ? 1.4f + (float)rnd.NextDouble() * 1.8f : 1f;
            }
            var runs = new Vector3[9];
            for (int i = 0; i < runs.Length; i++) runs[i] = new Vector3(-0.8f + i * 0.2f + (float)rnd.NextDouble() * 0.08f, 0.25f + (float)rnd.NextDouble() * 1.4f, 0.018f + (float)rnd.NextDouble() * 0.03f);
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float a = 0, wet = 0.1f;
                    if (x < half)
                    {
                        float u = x / (float)half * 2 - 1, v = y / (float)H * 2 - 1;
                        for (int i = 0; i < drops.Length; i++)
                        {
                            var dp = drops[i];
                            float ca = Mathf.Cos(dp.w), sa = Mathf.Sin(dp.w);
                            float lx = (u - dp.x) * ca + (v - dp.y) * sa, ly = -(u - dp.x) * sa + (v - dp.y) * ca;
                            if (lx > 0) lx /= el[i];                            // tail points away from the source
                            float dd = dp.z - Mathf.Sqrt(lx * lx + ly * ly);
                            a = Mathf.Max(a, S(-0.003f, 0.002f, dd));
                            if (el[i] > 1.2f)
                            {
                                float tx = dp.x + ca * dp.z * (el[i] + 1.2f), ty = dp.y + sa * dp.z * (el[i] + 1.2f);
                                float td = dp.z * 0.3f - Mathf.Sqrt((u - tx) * (u - tx) + (v - ty) * (v - ty));
                                a = Mathf.Max(a, S(-0.002f, 0.001f, td));
                            }
                        }
                        a *= S(1.0f, 0.85f, Mathf.Sqrt(u * u + v * v));
                    }
                    else
                    {
                        float u = (x - half) / (float)half * 2 - 1, v = 1 - y / (float)H;     // v = 0 at the top edge
                        a = S(0f, 0.04f, 0.10f - v) * S(0.2f, 0.5f, Fbm(u * 8, 3));          // soaked edge along the top
                        foreach (var rn in runs)
                        {
                            float len = rn.y, w = rn.z * (1 - 0.5f * Mathf.Clamp01(v / len));
                            if (v < len) a = Mathf.Max(a, S(-0.003f, 0.003f, w - Mathf.Abs(u - rn.x - Mathf.Sin(v * 9) * 0.01f)));
                            float bulb = rn.z * 1.5f - Mathf.Sqrt((u - rn.x) * (u - rn.x) + (v - len) * (v - len) * 1.4f);
                            a = Mathf.Max(a, S(-0.003f, 0.003f, bulb));
                        }
                        wet = 0.25f;
                    }
                    var c = Blood(wet) * (0.9f + 0.2f * Mathf.PerlinNoise(x * 0.05f, y * 0.05f)); c.a = a * 0.96f;
                    alb[y * W + x] = c; h[y * W + x] = a * 0.5f; sm[y * W + x] = 0.55f * a;
                }
            Decal(dir, set, alb, h, sm, W, H, 5f);
        }

        // ------------------------------------------------------------------ printed settlement pages
        static void PrintDoc(string dir, string set)
        {
            int W = 2048, H = 1448, pw = W / 2; var alb = new Color[W * H];
            var rnd = new System.Random(3);
            var paper = new Color(0.93f, 0.925f, 0.90f);
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float f = Mathf.PerlinNoise(x * 0.3f, y * 0.3f) * 0.025f + Mathf.PerlinNoise(x * 0.01f, y * 0.01f) * 0.03f;
                    alb[y * W + x] = paper * (0.975f + f);
                }
            var ink = new Color(0.16f, 0.16f, 0.18f); var grey = new Color(0.45f, 0.45f, 0.47f); var pen = new Color(0.12f, 0.20f, 0.55f);
            void Rect(int x0, int y0, int x1, int y1, Color c, float a = 1)
            {
                for (int y = Mathf.Max(0, y0); y < Mathf.Min(H, y1); y++)
                    for (int x = Mathf.Max(0, x0); x < Mathf.Min(W, x1); x++)
                        alb[y * W + x] = Color.Lerp(alb[y * W + x], c, a);
            }
            void TextLine(int px, int x0, int x1, int yc, int hgt, Color c, bool numbers = false)
            {   // words as ink dashes with gaps (reads as text at arm's length)
                int x = x0;
                while (x < x1)
                {
                    int wl = numbers ? rnd.Next(30, 60) : rnd.Next(18, 70);
                    Rect(px + x, yc - hgt / 2, px + Mathf.Min(x + wl, x1), yc + hgt / 2, c, 0.85f);
                    x += wl + rnd.Next(8, 14);
                    if (numbers) break;
                }
            }
            for (int page = 0; page < 2; page++)
            {
                int px = page * pw, m = 80;
                // header band left blank on page 0 (3D title label sits at v ~0.91); org line below it
                if (page == 0) { TextLine(px, m, 520, (int)(H * 0.845f), 9, grey); TextLine(px, pw - 360, pw - m, (int)(H * 0.845f), 9, grey); }
                else { TextLine(px, m, 600, (int)(H * 0.92f), 16, ink); TextLine(px, m, 400, (int)(H * 0.885f), 9, grey); }
                int top = (int)(H * (page == 0 ? 0.80f : 0.84f)), rows = page == 0 ? 15 : 10, rh = 34;
                int[] cols = { m, m + 260, m + 470, m + 640, m + 800, pw - m };
                Rect(px + m, top - rh, px + pw - m, top, new Color(0.82f, 0.82f, 0.80f));     // shaded header row
                for (int r = 0; r <= rows; r++) Rect(px + m, top - rh * (r + 1) - 1, px + pw - m, top - rh * (r + 1) + 1, ink, 0.8f);
                foreach (int cx in cols) Rect(px + cx - 1, top - rh * (rows + 1), px + cx + 1, top, ink, 0.8f);
                for (int r = 0; r <= rows; r++)
                    for (int c = 0; c < cols.Length - 1; c++)
                    {
                        int yc = top - rh * r - rh / 2;
                        if (c == 0) TextLine(px, cols[c] + 12, cols[c + 1] - 30, yc, 10, r == 0 ? ink : grey);
                        else TextLine(px, cols[c + 1] - 80, cols[c + 1] - 12, yc, 10, ink, true);
                    }
                if (page == 0)
                {   // pen corrections: strike-through + a handwritten figure above (canon: 볼펜으로 고친 흔적)
                    foreach (int r in new[] { 4, 7, 11 })
                    {
                        int yc = top - rh * r - rh / 2, cx = cols[4];
                        Rect(px + cx - 90, yc - 2, px + cx - 8, yc + 2, pen);
                        for (int k = 0; k < 70; k++)
                        {
                            float t = k / 70f; int sx = px + cx - 95 + (int)(t * 80), sy = yc + 14 + (int)(Mathf.Sin(t * 19f + r) * 6);
                            Rect(sx, sy - 2, sx + 3, sy + 2, pen);
                        }
                    }
                }
                int by = top - rh * (rows + 2) - 30;
                for (int l = 0; l < (page == 0 ? 6 : 12); l++) TextLine(px, m, pw - m - rnd.Next(0, 200), by - l * 30, 9, grey);
                Rect(px + pw / 2 - 20, 40, px + pw / 2 + 20, 48, grey, 0.8f);                  // page number
            }
            Save(dir, set, "diff", alb, W, H, false);
        }

        // ------------------------------------------------------------------ neighbour windows at night
        static void NightWin(string dir, string set)
        {
            int W = 2048, H = 512, cw = 512; var alb = new Color[W * H];
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int col = x / cw; float u = (x % cw) / (float)cw, v = y / (float)H;
                    Color c;
                    switch (col)
                    {
                        case 0: // warm room light through a sheer curtain
                            float folds = 0.75f + 0.25f * Mathf.Sin(u * 40f + Mathf.Sin(u * 7f) * 2f);
                            float glow = Mathf.Lerp(0.35f, 1f, Mathf.Exp(-Mathf.Pow((u - 0.6f) / 0.5f, 2) - Mathf.Pow((v - 0.75f) / 0.6f, 2)));
                            c = new Color(1f, 0.70f, 0.42f) * glow * folds * 0.55f; break;
                        case 1: // horizontal blinds, cool white
                            float slat = S(0.35f, 0.55f, Mathf.Sin(v * 110f));
                            c = new Color(0.80f, 0.85f, 0.90f) * (0.12f + 0.45f * slat) * Mathf.Lerp(0.6f, 1f, u); break;
                        case 2: // dark room, TV glow low on one side
                            float tv = Mathf.Exp(-Mathf.Pow((u - 0.3f) / 0.25f, 2) - Mathf.Pow((v - 0.3f) / 0.25f, 2));
                            c = new Color(0.25f, 0.40f, 0.85f) * (0.03f + 0.5f * tv); break;
                        default: // unlit: faint sky reflection gradient
                            c = new Color(0.035f, 0.04f, 0.055f) * (0.6f + 0.6f * v + 0.2f * Mathf.PerlinNoise(u * 4, v * 4)); break;
                    }
                    c.a = 1; alb[y * W + x] = c;
                }
            Save(dir, set, "diff", alb, W, H, false);
        }
    }
}
