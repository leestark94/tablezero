using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace TableZero.EditorTools
{
    /// <summary>
    /// Room polish pass: procedural 실크벽지 surface, localized grime/scuff/stain decals (real quads, not post FX),
    /// light-probe grid and a CPU lightmap bake for indirect bounce.
    /// Coordinates are given in the Blender layout (x east, y north, z up) and converted: Unity = (-x, z, -y).
    /// </summary>
    public static class TZRoom302Dressing
    {
        const string Root = "Assets/TableZero";
        const string GenDir = Root + "/Art/Textures/Generated";
        static string Full(string p) => Path.Combine(Directory.GetParent(Application.dataPath).FullName, p);
        static Vector3 U(float bx, float by, float bz) => new Vector3(-bx, bz, -by);
        static Vector3 UN(float nx, float ny, float nz) => new Vector3(-nx, nz, -ny);

        // ------------------------------------------------------------------ 실크벽지
        /// <summary>Off-white silk wallpaper: fine woven noise, faint seam every 1.06 m (Korean roll width), soft sheen.</summary>
        public static void EnsureSilkWallpaper(string dir, string set)
        {
            if (File.Exists(Path.Combine(dir, set + "_diff_2k.png"))) return;
            Directory.CreateDirectory(dir);
            int N = 2048; float cover = 1.06f;
            var alb = new Color32[N * N]; var h = new float[N * N]; var ms = new Color32[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float u = x / (float)N, v = y / (float)N;
                    float weave = Mathf.PerlinNoise(u * 900f, v * 60f) * 0.5f + Mathf.PerlinNoise(u * 60f, v * 900f) * 0.5f;
                    float mottle = Mathf.PerlinNoise(u * 6f + 3, v * 6f + 7) * 0.5f + Mathf.PerlinNoise(u * 23f, v * 23f) * 0.5f;
                    float seamD = Mathf.Min(u, 1 - u) * cover;               // distance to the roll seam in meters
                    float seam = 1f - Mathf.Clamp01(seamD / 0.0012f);
                    float baseV = 0.905f + (weave - 0.5f) * 0.035f + (mottle - 0.5f) * 0.03f - seam * 0.05f;
                    alb[y * N + x] = new Color(baseV, baseV * 0.988f, baseV * 0.955f, 1);
                    h[y * N + x] = weave * 0.6f + mottle * 0.1f - seam * 0.6f;
                    ms[y * N + x] = new Color32(0, 0, 0, (byte)(255 * (0.26f + weave * 0.08f)));
                }
            Save(dir, set, "diff", alb, false, N);
            Save(dir, set, "nor_gl", NormalFrom(h, N, 1.6f), true, N);
            Save(dir, set, "metalsmooth", ms, true, N);
            AssetDatabase.Refresh();
        }

        static Color32[] NormalFrom(float[] h, int N, float k)
        {
            var n = new Color32[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float dx = h[y * N + (x + 1) % N] - h[y * N + (x + N - 1) % N];
                    float dy = h[((y + 1) % N) * N + x] - h[((y + N - 1) % N) * N + x];
                    var v = new Vector3(-dx * k, -dy * k, 1f).normalized;
                    n[y * N + x] = new Color(v.x * 0.5f + 0.5f, v.y * 0.5f + 0.5f, v.z * 0.5f + 0.5f, 1);
                }
            return n;
        }

        static void Save(string dir, string set, string map, Color32[] px, bool linear, int N)
        {
            var t = new Texture2D(N, N, TextureFormat.RGBA32, false, linear);
            t.SetPixels32(px); t.Apply();
            File.WriteAllBytes(Path.Combine(dir, $"{set}_{map}_2k.png"), t.EncodeToPNG());
            Object.DestroyImmediate(t);
        }

        // ------------------------------------------------------------------ grime decals
        enum Grime { HandSmudge, Scuff, WaterStain, Grease, Mildew, Dust, WaterStreak, PinkMold, SoapScum, HairOil, PosterFade, CondensationMold }

        static Texture2D GrimeTex(Grime g)
        {
            string path = $"{GenDir}/grime_{g}.png";
            if (!File.Exists(Full(path)))
            {
                Directory.CreateDirectory(Full(GenDir));
                int N = 512; var px = new Color32[N * N];
                var rnd = new System.Random((int)g * 97 + 13);
                float ox = (float)rnd.NextDouble() * 50, oy = (float)rnd.NextDouble() * 50;
                for (int y = 0; y < N; y++)
                    for (int x = 0; x < N; x++)
                    {
                        float u = x / (float)N * 2 - 1, v = y / (float)N * 2 - 1;
                        float r = Mathf.Sqrt(u * u + v * v);
                        float n1 = Mathf.PerlinNoise(ox + x * 0.012f, oy + y * 0.012f), n2 = Mathf.PerlinNoise(ox + x * 0.05f, oy + y * 0.05f);
                        float a; Color c;
                        switch (g)
                        {
                            case Grime.HandSmudge: a = Mathf.Clamp01(1 - r * 1.1f) * (0.35f + 0.65f * n2) * 0.55f; c = new Color(0.35f, 0.30f, 0.25f); break;
                            case Grime.Scuff: a = Mathf.Clamp01(1 - Mathf.Abs(v) * 1.6f) * Mathf.Clamp01(1 - Mathf.Abs(u) * 1.05f) * Mathf.Pow(n2, 2.2f) * 1.4f; c = new Color(0.18f, 0.16f, 0.14f); break;
                            case Grime.WaterStain:
                                float ring = Mathf.Exp(-Mathf.Pow((r - 0.62f - (n1 - 0.5f) * 0.25f) * 9f, 2)) * 0.55f;
                                a = Mathf.Clamp01(1 - r) * 0.22f * n1 + ring; c = new Color(0.55f, 0.45f, 0.28f); break;
                            case Grime.Grease: a = Mathf.Clamp01(1 - r * 1.05f) * (0.4f + 0.6f * n1) * 0.45f; c = new Color(0.42f, 0.33f, 0.18f); break;
                            case Grime.Mildew: a = Mathf.Clamp01(1 - (v + 1) * 1.3f) * Mathf.Pow(n2, 1.5f) * 1.1f; c = new Color(0.12f, 0.13f, 0.11f); break;
                            case Grime.WaterStreak:   // limescale runs down the tiles under the shower
                                float runs = Mathf.Pow(Mathf.PerlinNoise(ox + x * 0.09f, oy + y * 0.004f), 3f) * 2.2f;
                                a = runs * Mathf.Clamp01(1 - Mathf.Abs(u) * 1.1f) * Mathf.Clamp01((v + 1.1f) * 0.6f) * 0.55f; c = new Color(0.80f, 0.79f, 0.72f); break;
                            case Grime.PinkMold:      // Serratia film in wet corners
                                a = Mathf.Clamp01(1 - r * 1.15f) * Mathf.Pow(n2, 1.3f) * 1.2f; c = new Color(0.72f, 0.38f, 0.40f); break;
                            case Grime.SoapScum:
                                float rg = Mathf.Exp(-Mathf.Pow((r - 0.45f - (n1 - 0.5f) * 0.3f) * 5f, 2));
                                a = (rg * 0.5f + Mathf.Clamp01(1 - r) * 0.15f) * (0.5f + n2); c = new Color(0.86f, 0.85f, 0.80f); break;
                            case Grime.HairOil:       // greasy patch on the wallpaper above the headboard
                                a = Mathf.Clamp01(1 - Mathf.Abs(u) * 1.05f) * Mathf.Clamp01(1 - Mathf.Abs(v) * 1.3f) * (0.4f + 0.6f * n1) * 0.42f; c = new Color(0.50f, 0.42f, 0.26f); break;
                            case Grime.PosterFade:    // brighter unfaded rectangle + tape corners where a poster hung
                                bool inRect = Mathf.Abs(u) < 0.72f && Mathf.Abs(v) < 0.86f;
                                bool tape = (Mathf.Abs(Mathf.Abs(u) - 0.72f) < 0.07f) && (Mathf.Abs(Mathf.Abs(v) - 0.86f) < 0.06f);
                                a = tape ? 0.55f * (0.6f + 0.4f * n2) : inRect ? 0.13f : 0f; c = tape ? new Color(0.62f, 0.55f, 0.40f) : new Color(1f, 1f, 0.98f); break;
                            case Grime.CondensationMold: // black mould spreading from a cold window corner
                                a = Mathf.Clamp01(1 - r * 1.05f) * Mathf.Pow(n2, 1.1f) * Mathf.Pow(n1, 0.6f) * 1.6f; c = new Color(0.07f, 0.08f, 0.06f); break;
                            default: a = Mathf.Clamp01(1 - r) * n1 * 0.3f; c = new Color(0.45f, 0.43f, 0.40f); break;
                        }
                        a = Mathf.Clamp01(a) * (g == Grime.PosterFade || g == Grime.WaterStreak ? 1f : Mathf.Clamp01((1 - r) * 4f));
                        px[y * N + x] = new Color(c.r, c.g, c.b, a);
                    }
                var t = new Texture2D(N, N, TextureFormat.RGBA32, false);
                t.SetPixels32(px); t.Apply();
                File.WriteAllBytes(Full(path), t.EncodeToPNG());
                Object.DestroyImmediate(t);
                AssetDatabase.ImportAsset(path);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                ti.alphaIsTransparency = true; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        static Material GrimeMat(Grime g)
        {
            string mp = $"{Root}/Art/Materials/Decal_{g}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(mp);
            if (!m) { m = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(m, mp); }
            m.SetTexture("_BaseMap", GrimeTex(g));
            m.SetColor("_BaseColor", Color.white);
            m.SetFloat("_Smoothness", g == Grime.Grease ? 0.55f : 0.12f);
            m.SetFloat("_Surface", 1); m.SetFloat("_Blend", 0);
            m.SetOverrideTag("RenderType", "Transparent");
            m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); m.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
            m.SetFloat("_ZWrite", 0); m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.SetFloat("_ReceiveShadows", 1);
            m.renderQueue = (int)RenderQueue.Transparent - 50;
            EditorUtility.SetDirty(m);
            return m;
        }

        static void Decal(Transform parent, string name, Grime g, Vector3 bpos, Vector3 bnormal, Vector2 size, float rot = 0)
        {
            var q = GameObject.CreatePrimitive(PrimitiveType.Quad);   // a flat decal card, never visible as a primitive object
            Object.DestroyImmediate(q.GetComponent<Collider>());
            q.name = "arch_decal_" + name;
            q.transform.SetParent(parent, false);
            Vector3 n = UN(bnormal.x, bnormal.y, bnormal.z).normalized;
            q.transform.position = U(bpos.x, bpos.y, bpos.z) + n * 0.003f;
            q.transform.rotation = Quaternion.LookRotation(-n, Mathf.Abs(n.y) > 0.9f ? Vector3.forward : Vector3.up) * Quaternion.Euler(0, 0, rot);
            q.transform.localScale = new Vector3(size.x, size.y, 1);
            var r = q.GetComponent<MeshRenderer>();
            r.sharedMaterial = GrimeMat(g); r.shadowCastingMode = ShadowCastingMode.Off;
        }

        public static void AddGrime()
        {
            var root = new GameObject("Dressing_Grime").transform;
            // hand grime around switches (people hit the same spot for years)
            Decal(root, "switch_living", Grime.HandSmudge, new Vector3(2.1f, 1.93f, 1.2f), new Vector3(-1, 0, 0), new Vector2(0.28f, 0.32f));
            Decal(root, "switch_entrance", Grime.HandSmudge, new Vector3(1.12f, 0f, 1.2f), new Vector3(0, 1, 0), new Vector2(0.26f, 0.30f));
            Decal(root, "switch_bath", Grime.HandSmudge, new Vector3(2.1f, 0.87f, 1.2f), new Vector3(-1, 0, 0), new Vector2(0.3f, 0.3f));
            // scuffs low on walls: entrance corridor, next to the low table, behind the drying rack
            Decal(root, "scuff_corridor", Grime.Scuff, new Vector3(2.1f, 0.6f, 0.18f), new Vector3(-1, 0, 0), new Vector2(0.9f, 0.25f));
            Decal(root, "scuff_entrance", Grime.Scuff, new Vector3(1.6f, 0f, 0.05f), new Vector3(0, 1, 0), new Vector2(0.7f, 0.2f));
            Decal(root, "scuff_north", Grime.Scuff, new Vector3(1.9f, 6.0f, 0.2f), new Vector3(0, -1, 0), new Vector2(1.0f, 0.25f));
            Decal(root, "scuff_bed", Grime.Scuff, new Vector3(4.2f, 5.0f, 0.45f), new Vector3(-1, 0, 0), new Vector2(1.2f, 0.22f));
            // ceiling water stain near the window corner (old 빌라 roof leak)
            Decal(root, "water_ceiling", Grime.WaterStain, new Vector3(3.6f, 5.55f, 2.299f), new Vector3(0, 0, -1), new Vector2(0.8f, 0.7f), 20);
            // kitchen grease behind the range, dust on top of the fridge
            Decal(root, "grease_range", Grime.Grease, new Vector3(0.008f, 3.0f, 1.12f), new Vector3(1, 0, 0), new Vector2(0.75f, 0.5f));
            Decal(root, "dust_fridge", Grime.Dust, new Vector3(0.3f, 4.12f, 1.731f), new Vector3(0, 0, 1), new Vector2(0.5f, 0.5f));
            // bathroom: mildew along the tile base by the shower, around the drain
            Decal(root, "mildew_south", Grime.Mildew, new Vector3(2.9f, 0.002f, 0.12f), new Vector3(0, 1, 0), new Vector2(1.3f, 0.35f));
            Decal(root, "mildew_corner", Grime.Mildew, new Vector3(2.201f, 0.4f, 0.12f), new Vector3(1, 0, 0), new Vector2(0.8f, 0.35f));
            Decal(root, "mildew_drain", Grime.Dust, new Vector3(2.6f, 0.55f, -0.0435f), new Vector3(0, 0, 1), new Vector2(0.4f, 0.4f));
            // v5: the bathroom is used every day — limescale runs, pink film in wet corners, soap scum at the drain and the sink
            Decal(root, "streak_shower", Grime.WaterStreak, new Vector3(2.62f, 0.002f, 0.85f), new Vector3(0, 1, 0), new Vector2(0.75f, 1.5f));
            Decal(root, "streak_sink", Grime.WaterStreak, new Vector3(3.22f, 1.998f, 1.0f), new Vector3(0, -1, 0), new Vector2(0.5f, 0.45f));
            Decal(root, "pinkmold_corner", Grime.PinkMold, new Vector3(2.32f, 0.12f, -0.0438f), new Vector3(0, 0, 1), new Vector2(0.35f, 0.3f), 30);
            Decal(root, "pinkmold_wall", Grime.PinkMold, new Vector3(2.202f, 0.25f, 0.05f), new Vector3(1, 0, 0), new Vector2(0.4f, 0.18f));
            Decal(root, "pinkmold_toilet", Grime.PinkMold, new Vector3(3.74f, 0.5f, -0.0437f), new Vector3(0, 0, 1), new Vector2(0.42f, 0.36f));
            Decal(root, "scum_drain", Grime.SoapScum, new Vector3(2.6f, 0.55f, -0.0434f), new Vector3(0, 0, 1), new Vector2(0.34f, 0.34f), 40);
            // v5: walls — condensation mould at the cold window corners (결로), greasy patch above the bed head, a poster that was taken down
            Decal(root, "condmold_win_l", Grime.CondensationMold, new Vector3(1.18f, 5.997f, 0.95f), new Vector3(0, -1, 0), new Vector2(0.36f, 0.42f));
            Decal(root, "condmold_win_r", Grime.CondensationMold, new Vector3(2.72f, 5.997f, 2.05f), new Vector3(0, -1, 0), new Vector2(0.42f, 0.36f), 180);
            Decal(root, "condmold_ceil", Grime.CondensationMold, new Vector3(4.05f, 5.85f, 2.299f), new Vector3(0, 0, -1), new Vector2(0.5f, 0.45f));
            Decal(root, "condmold_base", Grime.CondensationMold, new Vector3(4.198f, 5.7f, 0.12f), new Vector3(-1, 0, 0), new Vector2(0.55f, 0.25f));
            Decal(root, "hairoil_bed", Grime.HairOil, new Vector3(3.6f, 5.997f, 0.98f), new Vector3(0, -1, 0), new Vector2(0.8f, 0.32f));
            Decal(root, "poster_west", Grime.PosterFade, new Vector3(0.003f, 3.95f, 1.55f), new Vector3(1, 0, 0), new Vector2(0.5f, 0.7f));
        }

        // ------------------------------------------------------------------ probes + bake
        public static void AddLightProbes()
        {
            var go = new GameObject("LightProbes_Room302");
            var g = go.AddComponent<LightProbeGroup>();
            var pts = new List<Vector3>();
            for (float x = 0.3f; x <= 4.0f; x += 0.7f)
                for (float y = 0.3f; y <= 5.8f; y += 0.7f)
                    foreach (float z in new[] { 0.25f, 1.1f, 2.0f })
                        pts.Add(U(x, y, z));
            for (float x = -1.2f; x <= 6.2f; x += 1.0f)
                foreach (float z in new[] { 0.2f, 1.2f, 2.0f })
                    pts.Add(U(x, -1.0f, z));
            g.probePositions = pts.ToArray();
        }

        [MenuItem("TableZero/Build/Bake Room 302 Lighting (CPU)")]
        public static string BakeLighting()
        {
            var ls = new LightingSettings
            {
                name = "Room302_Lighting",
                bakedGI = true,
                realtimeGI = false,
                lightmapper = LightingSettings.Lightmapper.ProgressiveCPU,   // GPU lightmapper avoided: BUG-0001
                mixedBakeMode = MixedLightingMode.IndirectOnly,
                lightmapResolution = 14,
                lightmapPadding = 4,
                lightmapMaxSize = 1024,
                directSampleCount = 32,
                indirectSampleCount = 192,
                environmentSampleCount = 64,
                maxBounces = 3,
                filteringMode = LightingSettings.FilterMode.Auto,
                ao = true, aoMaxDistance = 0.6f,
                lightmapCompression = LightmapCompression.NormalQuality,
            };
            string lp = Root + "/Art/Rendering/Room302_Lighting.lighting";
            if (AssetDatabase.LoadAssetAtPath<LightingSettings>(lp)) AssetDatabase.DeleteAsset(lp);
            AssetDatabase.CreateAsset(ls, lp);
            Lightmapping.lightingSettings = ls;
            // lights that are on when the detective arrives bake their bounce; switchable room lights stay realtime
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include))
            {
                bool bake = l.name == "L_StandLamp" || l.name == "L_HoodLamp" || l.name == "L_StreetThroughWindow" || l.name == "L_HallSensor";
                l.lightmapBakeType = bake ? LightmapBakeType.Mixed : LightmapBakeType.Realtime;
                l.bounceIntensity = bake ? 1.4f : 1f;
            }
            var sw = System.Diagnostics.Stopwatch.StartNew();
            bool ok = Lightmapping.Bake();
            sw.Stop();
            UnityEditor.SceneManagement.EditorSceneManager.SaveOpenScenes();
            return $"bake ok={ok} seconds={sw.Elapsed.TotalSeconds:F0} lightmaps={LightmapSettings.lightmaps.Length}";
        }
    }
}
