using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace TableZero.EditorTools
{
    /// <summary>
    /// Rebuilds Case001_Room302.unity from blender/out/Room302.fbx (re-runnable; never hand-edit the scene).
    /// Menu: TableZero/Build/Room 302 Scene
    /// </summary>
    public static class TZRoom302Builder
    {
        const string Root = "Assets/TableZero";
        const string FbxDst = Root + "/Art/Models/Room302.fbx";
        const string MatDir = Root + "/Art/Materials";
        const string TexDir = Root + "/Art/Textures/PolyHaven";
        const string ScenePath = Root + "/Scenes/Case001_Room302.unity";

        static string RepoRoot => Directory.GetParent(Application.dataPath).Parent.FullName;

        // material name -> (texture set, uv scale, tint, smoothness, metallic)
        struct MatSpec { public string tex; public float uv; public Color tint; public float smooth; public float metal; public bool transparent; public float emission; public float normal; }
        static MatSpec S(string tex, float uv, Color c, float smooth, float metal = 0, bool tr = false, float em = 0, float nrm = 1) =>
            new MatSpec { tex = tex, uv = uv, tint = c, smooth = smooth, metal = metal, transparent = tr, emission = em, normal = nrm };
        static Color C(float r, float g, float b, float a = 1) => new Color(r, g, b, a);

        static readonly Dictionary<string, MatSpec> Specs = new Dictionary<string, MatSpec>
        {
            {"M_WallPaper", S("gen_silkwallpaper", 1f / 1.06f, C(1f,1f,1f), 1f, 0, false, 0, 0.6f)},
            {"M_Floor", S("laminate_floor_02", 0.55f, C(1.0f,0.88f,0.72f), 0.58f)},
            {"M_EntranceTile", S("gen_entrancetile_300", 1f / 1.2f, C(1f,1f,1f), 1f)},
            {"M_BathTile", S("gen_walltile_300x600", 1f / 1.2f, C(1f,1f,1f), 1f)},
            {"M_BathFloor", S("gen_floortile_200", 1f, C(1f,1f,1f), 1f)},
            {"M_ExteriorBrick", S("brown_brick_02", 0.45f, C(0.75f,0.70f,0.68f), 0.08f)},
            {"M_WindowLitWarm", S(null, 1, C(1f,0.80f,0.55f), 0.3f, 0, false, 2.2f)},
            {"M_WindowDark", S(null, 1, C(0.02f,0.025f,0.035f), 0.9f)},
            {"M_HallConcrete", S("concrete_wall_001", 0.45f, C(0.85f,0.84f,0.80f), 0.10f)},
            {"M_HallPlaster", S("plastered_wall", 0.45f, C(0.90f,0.88f,0.82f), 0.12f)},
            {"M_StairTerrazzo", S("worn_tile_floor", 1.0f, C(0.70f,0.68f,0.65f), 0.35f)},
            {"M_CabinetWood", S("kitchen_wood", 1.0f, C(0.9f,0.9f,0.9f), 0.40f)},
            {"M_FabricLinen", S("rough_linen", 2.5f, C(0.80f,0.82f,0.85f), 0.05f)},
            {"M_FabricCotton", S("cotton_jersey", 3f, C(0.95f,0.93f,0.90f), 0.05f)},
            {"M_FabricSheet", S("cotton_jersey", 3f, C(0.88f,0.90f,0.93f), 0.05f)},
            {"M_Carpet", S("dirty_carpet", 2f, C(0.8f,0.75f,0.70f), 0.02f)},
            {"M_WoodOak", S("oak_veneer_01", 1f, C(1f,1f,1f), 0.45f)},
            {"M_WoodTrim", S("oak_veneer_01", 1f, C(0.6f,0.5f,0.42f), 0.40f)},
            {"M_Ceiling", S("white_plaster_02", 0.5f, C(0.92f,0.92f,0.90f), 0.05f, 0, false, 0, 0.2f)},
            {"M_CabinetWhite", S(null, 1, C(0.88f,0.87f,0.84f), 0.62f)},
            {"M_Counter", S(null, 1, C(0.16f,0.16f,0.17f), 0.55f)},
            {"M_Steel", S(null, 1, C(0.72f,0.72f,0.73f), 0.62f, 1)},
            {"M_Chrome", S(null, 1, C(0.88f,0.88f,0.9f), 0.92f, 1)},
            {"M_DoorSteel", S(null, 1, C(0.20f,0.17f,0.15f), 0.48f, 0.35f)},
            {"M_DoorWhite", S(null, 1, C(0.86f,0.85f,0.82f), 0.55f)},
            {"M_PlasticWhite", S(null, 1, C(0.88f,0.88f,0.86f), 0.55f)},
            {"M_PlasticBlack", S(null, 1, C(0.025f,0.025f,0.03f), 0.6f)},
            {"M_PlasticGray", S(null, 1, C(0.42f,0.43f,0.44f), 0.45f)},
            {"M_Porcelain", S(null, 1, C(0.93f,0.93f,0.92f), 0.9f)},
            {"M_Glass", S(null, 1, C(0.75f,0.82f,0.85f,0.22f), 0.95f, 0, true)},
            {"M_FrostedGlass", S(null, 1, C(0.85f,0.88f,0.9f,0.65f), 0.45f, 0, true)},
            {"M_Mirror", S(null, 1, C(0.9f,0.9f,0.9f), 0.98f, 1)},
            {"M_Rubber", S(null, 1, C(0.04f,0.04f,0.04f), 0.15f)},
            {"M_Mattress", S("cotton_jersey", 2f, C(0.93f,0.92f,0.88f), 0.08f)},
            {"M_Paper", S(null, 1, C(0.92f,0.91f,0.87f), 0.12f)},
            {"M_Cardboard", S(null, 1, C(0.58f,0.44f,0.29f), 0.12f)},
            {"M_BloodDried", S(null, 1, C(0.11f,0.012f,0.012f), 0.55f)},
            {"M_LEDPanel", S(null, 1, C(0.95f,0.95f,0.93f), 0.4f, 0, false, 0f)},
            {"M_PlasticBagWhite", S(null, 1, C(0.74f,0.74f,0.72f,0.94f), 0.5f)},
            {"M_TrashBagVolume", S(null, 1, C(0.55f,0.62f,0.70f,0.95f), 0.55f)},
            {"M_ScreenOff", S(null, 1, C(0.015f,0.015f,0.02f), 0.92f)},
            {"M_Aluminum", S(null, 1, C(0.68f,0.69f,0.70f), 0.5f, 1)},
            {"M_BrassDark", S(null, 1, C(0.50f,0.40f,0.24f), 0.5f, 1)},
            {"M_PlasticRed", S(null, 1, C(0.50f,0.05f,0.04f), 0.55f)},
            {"M_PlasticGreen", S(null, 1, C(0.17f,0.35f,0.19f), 0.6f)},
            {"M_PlasticBlue", S(null, 1, C(0.13f,0.30f,0.58f), 0.6f)},
            {"M_FloorChairFabric", S("rough_linen", 3f, C(0.32f,0.34f,0.38f), 0.05f)},
            {"M_CushionFabric", S("rough_linen", 3f, C(0.70f,0.60f,0.50f), 0.05f)},
            {"M_CurtainFabric", S("rough_linen", 2f, C(0.50f,0.52f,0.55f), 0.05f)},
            {"M_LaundryA", S("cotton_jersey", 4f, C(0.30f,0.36f,0.50f), 0.05f)},
            {"M_LaundryB", S("cotton_jersey", 4f, C(0.95f,0.94f,0.90f), 0.05f)},
            {"M_LaundryC", S("cotton_jersey", 4f, C(0.62f,0.24f,0.26f), 0.05f)},
            {"M_CoatWool", S("rough_linen", 3f, C(0.20f,0.20f,0.22f), 0.03f)},
            {"M_BloodSmear", S(null, 1, C(0.20f,0.025f,0.02f,0.78f), 0.5f)},
            {"M_FootprintBlood", S(null, 1, C(0.20f,0.04f,0.03f,0.55f), 0.3f)},
            {"M_ReleaseFilm", S(null, 1, C(0.92f,0.93f,0.95f,0.8f), 0.85f)},
            {"M_LivingBox", S(null, 1, C(0.88f,0.89f,0.92f,0.62f), 0.7f)},
            {"M_ClearBag", S(null, 1, C(0.85f,0.88f,0.9f,0.45f), 0.75f)},
            {"M_PoliceTape", S(null, 1, C(0.95f,0.76f,0.04f), 0.55f)},
            {"M_NitrileBlue", S(null, 1, C(0.20f,0.40f,0.85f), 0.45f)},
        };

        [MenuItem("TableZero/Build/Room 302 Scene")]
        public static void Build()
        {
            ImportFbx();
            var mats = BuildMaterials();
            RemapFbxMaterials();
            ConfigurePipeline();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(FbxDst));
            PrefabUtility.UnpackPrefabInstance(root, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            root.name = "Room302_Hall3F";
            var manifest = LoadManifest();
            var objs = root.GetComponentsInChildren<Transform>(true).Where(t => t != root.transform).ToDictionary(t => t.name, t => t.gameObject);
            SetupColliders(objs);
            var props = SetupProps(objs, manifest);
            var lights = SetupLighting(objs, props);
            SetupPlayerAndUI(objs);
            AssignSwitches(props, lights);
            TZRoom302Dressing.AddGrime();
            TZRoom302Dressing.AddLightProbes();
            Directory.CreateDirectory(Path.Combine(Directory.GetParent(Application.dataPath).FullName, Root, "Scenes"));
            AssetDatabase.Refresh();
            EditorSceneManager.SaveScene(scene, ScenePath);
            AddToBuild(ScenePath);
            DumpPositions(objs);
            WriteCoverage(objs, manifest);
            Debug.Log("[TZBuilder] Room302 built: " + objs.Count + " objects, props " + props.Count);
        }

        // ------------------------------------------------------------------ import
        static void ImportFbx()
        {
            string src = Path.Combine(RepoRoot, "blender", "out", "Room302.fbx");
            string dst = Path.Combine(Directory.GetParent(Application.dataPath).FullName, FbxDst);
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            File.Copy(src, dst, true);
            AssetDatabase.ImportAsset(FbxDst, ImportAssetOptions.ForceUpdate);
            var mi = (ModelImporter)AssetImporter.GetAtPath(FbxDst);
            mi.globalScale = 1; mi.useFileScale = true; mi.bakeAxisConversion = false;
            mi.importAnimation = false; mi.importCameras = false; mi.importLights = false;
            mi.importNormals = ModelImporterNormals.Import; mi.importTangents = ModelImporterTangents.CalculateMikk;
            mi.generateSecondaryUV = true; mi.meshCompression = ModelImporterMeshCompression.Off;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            mi.SaveAndReimport();
        }

        static void RemapFbxMaterials()
        {
            var mi = (ModelImporter)AssetImporter.GetAtPath(FbxDst);
            mi.SearchAndRemapMaterials(ModelImporterMaterialName.BasedOnMaterialName, ModelImporterMaterialSearch.Local);
            foreach (var m in AssetDatabase.LoadAllAssetsAtPath(FbxDst).OfType<Material>())
            {
                var path = $"{MatDir}/{m.name}.mat";
                var proj = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (proj) mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), m.name), proj);
            }
            mi.SaveAndReimport();
        }

        // ------------------------------------------------------------------ materials
        static Dictionary<string, Material> BuildMaterials()
        {
            Directory.CreateDirectory(MatDir);
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var all = new Dictionary<string, Material>();
            // every material referenced by the FBX gets a project material (spec or neutral fallback)
            var names = AssetDatabase.LoadAllAssetsAtPath(FbxDst).OfType<Material>().Select(m => m.name).Distinct().ToList();
            foreach (var n in Specs.Keys) if (!names.Contains(n)) names.Add(n);
            foreach (var name in names)
            {
                var path = $"{MatDir}/{name}.mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (!mat) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
                mat.shader = shader;
                MatSpec s;
                if (!Specs.TryGetValue(name, out s))
                {
                    var src = AssetDatabase.LoadAllAssetsAtPath(FbxDst).OfType<Material>().FirstOrDefault(x => x.name == name);
                    Color c = src && src.HasProperty("_Color") ? src.GetColor("_Color") : Color.gray;
                    s = S(null, 1, c, 0.35f);
                }
                mat.SetColor("_BaseColor", s.tint);
                mat.SetFloat("_Smoothness", s.smooth);
                mat.SetFloat("_Metallic", s.metal);
                mat.SetFloat("_EnvironmentReflections", name.Contains("Glass") ? 0 : 1);
                if (name.Contains("Glass")) mat.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF"); else mat.DisableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
                mat.SetFloat("_SpecularHighlights", 1);
                if (s.tex != null)
                {
                    var diff = LoadTex(s.tex, "diff", false);
                    var nor = LoadTex(s.tex, "nor_gl", true);
                    var ao = LoadTex(s.tex, "ao", false);
                    var mg = PackSmoothness(s.tex, s.metal);
                    if (diff) mat.SetTexture("_BaseMap", diff);
                    if (nor) { mat.SetTexture("_BumpMap", nor); mat.SetFloat("_BumpScale", s.normal); mat.EnableKeyword("_NORMALMAP"); }
                    if (ao) { mat.SetTexture("_OcclusionMap", ao); mat.SetFloat("_OcclusionStrength", 0.8f); mat.EnableKeyword("_OCCLUSIONMAP"); }
                    if (mg) { mat.SetTexture("_MetallicGlossMap", mg); mat.SetFloat("_Smoothness", 1f); mat.SetFloat("_SmoothnessTextureChannel", 0); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); }
                    mat.SetTextureScale("_BaseMap", Vector2.one * s.uv);
                }
                else
                {
                    mat.SetTexture("_BaseMap", null); mat.SetTexture("_BumpMap", null); mat.SetTexture("_MetallicGlossMap", null);
                    mat.DisableKeyword("_NORMALMAP"); mat.DisableKeyword("_METALLICSPECGLOSSMAP");
                }
                if (s.transparent || s.tint.a < 0.999f)
                {
                    mat.SetFloat("_Surface", 1); mat.SetFloat("_Blend", 0);
                    mat.SetOverrideTag("RenderType", "Transparent");
                    mat.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); mat.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                    mat.SetFloat("_SrcBlendAlpha", (float)BlendMode.One); mat.SetFloat("_DstBlendAlpha", (float)BlendMode.OneMinusSrcAlpha);
                    mat.SetFloat("_ZWrite", 0); mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                    mat.renderQueue = (int)RenderQueue.Transparent;
                }
                else
                {
                    mat.SetFloat("_Surface", 0); mat.SetOverrideTag("RenderType", "Opaque");
                    mat.SetFloat("_SrcBlend", (float)BlendMode.One); mat.SetFloat("_DstBlend", (float)BlendMode.Zero);
                    mat.SetFloat("_ZWrite", 1); mat.DisableKeyword("_SURFACE_TYPE_TRANSPARENT");
                    mat.renderQueue = -1;
                }
                if (s.emission > 0)
                {
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", s.tint * s.emission);
                    mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                }
                if (name == "M_LEDPanel")
                {
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", new Color(1f, 0.96f, 0.9f) * 0.0f);
                    mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                }
                EditorUtility.SetDirty(mat);
                all[name] = mat;
            }
            AssetDatabase.SaveAssets();
            return all;
        }

        static Texture2D LoadTex(string set, string map, bool normal)
        {
            if (set == "gen_silkwallpaper") TZRoom302Dressing.EnsureSilkWallpaper(Path.Combine(Directory.GetParent(Application.dataPath).FullName, TexDir, set), set);
            else if (set.StartsWith("gen_")) EnsureGeneratedTiles(set);
            string path = $"{TexDir}/{set}/{set}_{map}_2k.jpg";
            if (!File.Exists(Path.Combine(Directory.GetParent(Application.dataPath).FullName, path))) path = path.Replace(".jpg", ".png");
            if (!File.Exists(Path.Combine(Directory.GetParent(Application.dataPath).FullName, path))) return null;
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            if (ti)
            {
                bool dirty = false;
                if (normal && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; dirty = true; }
                if (!normal && map != "diff" && ti.sRGBTexture) { ti.sRGBTexture = false; dirty = true; }
                if (ti.maxTextureSize != 2048) { ti.maxTextureSize = 2048; dirty = true; }
                if (ti.anisoLevel != 8) { ti.anisoLevel = 8; dirty = true; }
                if (dirty) ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        /// <summary>Procedural ceramic tiles (real grout recess in the normal map, per-tile tone variation, glossy tile / matte grout).
        /// Used where the CC0 library had no Korean-bathroom-like tile. 2048 px covers 1.2 m (or 1.0 m for the 200 floor).</summary>
        static void EnsureGeneratedTiles(string set)
        {
            string dir = Path.Combine(Directory.GetParent(Application.dataPath).FullName, TexDir, set);
            if (File.Exists(Path.Combine(dir, set + "_diff_2k.png"))) return;
            Directory.CreateDirectory(dir);
            float coverM; float tw, th, grout; Color baseC, groutC; float var; float tileSmooth;
            if (set.Contains("walltile")) { coverM = 1.2f; tw = 0.3f; th = 0.6f; grout = 0.003f; baseC = new Color(0.90f, 0.89f, 0.86f); groutC = new Color(0.70f, 0.69f, 0.66f); var = 0.018f; tileSmooth = 0.86f; }
            else if (set.Contains("entrancetile")) { coverM = 1.2f; tw = 0.3f; th = 0.3f; grout = 0.004f; baseC = new Color(0.42f, 0.40f, 0.37f); groutC = new Color(0.25f, 0.24f, 0.22f); var = 0.05f; tileSmooth = 0.45f; }
            else { coverM = 1.0f; tw = 0.2f; th = 0.2f; grout = 0.004f; baseC = new Color(0.56f, 0.57f, 0.57f); groutC = new Color(0.30f, 0.30f, 0.29f); var = 0.04f; tileSmooth = 0.35f; }
            int N = 2048;
            var albedo = new Color32[N * N]; var height = new float[N * N]; var ms = new Color32[N * N];
            var rnd = new System.Random(set.GetHashCode());
            int cols = Mathf.RoundToInt(coverM / tw), rows = Mathf.RoundToInt(coverM / th);
            var tone = new float[cols * rows];
            for (int i = 0; i < tone.Length; i++) tone[i] = (float)(rnd.NextDouble() * 2 - 1) * var;
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float mx = x / (float)N * coverM, my = y / (float)N * coverM;
                    int cx = Mathf.Min(cols - 1, (int)(mx / tw)), cy = Mathf.Min(rows - 1, (int)(my / th));
                    float dx = Mathf.Min(mx - cx * tw, (cx + 1) * tw - mx), dy = Mathf.Min(my - cy * th, (cy + 1) * th - my);
                    float d = Mathf.Min(dx, dy);
                    float g = Mathf.Clamp01((d - grout * 0.5f) / (grout * 0.6f));   // 0 grout .. 1 tile
                    float noise = Mathf.PerlinNoise(mx * 37f, my * 37f) * 0.03f - 0.015f;
                    Color c = Color.Lerp(groutC, baseC * (1 + tone[cy * cols + cx]), g) + new Color(noise, noise, noise);
                    albedo[y * N + x] = c;
                    float bevel = Mathf.Clamp01(d / (grout * 2.2f));
                    height[y * N + x] = Mathf.Lerp(0f, 1f, Mathf.SmoothStep(0, 1, bevel));
                    float sm = Mathf.Lerp(0.15f, tileSmooth, g);
                    ms[y * N + x] = new Color32(0, 0, 0, (byte)(sm * 255));
                }
            var nrm = new Color32[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float hl = height[y * N + (x + N - 1) % N], hr = height[y * N + (x + 1) % N];
                    float hd = height[((y + N - 1) % N) * N + x], hu = height[((y + 1) % N) * N + x];
                    var n = new Vector3((hl - hr) * 3f, (hd - hu) * 3f, 1f).normalized;
                    nrm[y * N + x] = new Color(n.x * 0.5f + 0.5f, n.y * 0.5f + 0.5f, n.z * 0.5f + 0.5f, 1);
                }
            void Save(Color32[] px, string map, bool linear)
            {
                var t = new Texture2D(N, N, TextureFormat.RGBA32, false, linear);
                t.SetPixels32(px); t.Apply();
                File.WriteAllBytes(Path.Combine(dir, $"{set}_{map}_2k.png"), t.EncodeToPNG());
                Object.DestroyImmediate(t);
            }
            Save(albedo, "diff", false); Save(nrm, "nor_gl", true); Save(ms, "metalsmooth", true);
            AssetDatabase.Refresh();
        }

        /// <summary>URP needs smoothness in the alpha of a metallic map: pack (1 - roughness).</summary>
        static Texture2D PackSmoothness(string set, float metal)
        {
            string outPath = $"{TexDir}/{set}/{set}_metalsmooth_2k.png";
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, outPath);
            if (!File.Exists(full))
            {
                string rp = $"{TexDir}/{set}/{set}_rough_2k.jpg";
                var ti = (TextureImporter)AssetImporter.GetAtPath(rp);
                if (!ti) return null;
                ti.isReadable = true; ti.sRGBTexture = false; ti.textureCompression = TextureImporterCompression.Uncompressed; ti.SaveAndReimport();
                var r = AssetDatabase.LoadAssetAtPath<Texture2D>(rp);
                var px = r.GetPixels32();
                var o = new Color32[px.Length];
                byte m = (byte)(metal * 255);
                for (int i = 0; i < px.Length; i++) o[i] = new Color32(m, 0, 0, (byte)(255 - px[i].r));
                var t = new Texture2D(r.width, r.height, TextureFormat.RGBA32, false, true);
                t.SetPixels32(o); t.Apply();
                File.WriteAllBytes(full, t.EncodeToPNG());
                Object.DestroyImmediate(t);
                ti.isReadable = false; ti.textureCompression = TextureImporterCompression.Compressed; ti.SaveAndReimport();
                AssetDatabase.ImportAsset(outPath);
                var oi = (TextureImporter)AssetImporter.GetAtPath(outPath);
                oi.sRGBTexture = false; oi.maxTextureSize = 2048; oi.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(outPath);
        }

        // ------------------------------------------------------------------ pipeline
        static void ConfigurePipeline()
        {
            var rp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/Settings/PC_RPAsset.asset");
            if (rp)
            {
                var so = new SerializedObject(rp);
                void Set(string p, int v) { var x = so.FindProperty(p); if (x != null) x.intValue = v; }
                void SetF(string p, float v) { var x = so.FindProperty(p); if (x != null) x.floatValue = v; }
                Set("m_MSAA", 4); Set("m_AdditionalLightsShadowmapResolution", 4096); Set("m_MainLightShadowmapResolution", 2048);
                SetF("m_ShadowDistance", 18f); Set("m_AdditionalLightsPerObjectLimit", 8); Set("m_SoftShadowQuality", 3);
                so.ApplyModifiedPropertiesWithoutUndo();
            }
            var rd = AssetDatabase.LoadAssetAtPath<ScriptableRendererData>("Assets/Settings/PC_Renderer.asset");
            if (rd)
            {
                foreach (var f in rd.rendererFeatures)
                {
                    if (f == null || !f.GetType().Name.Contains("AmbientOcclusion")) continue;
                    var so = new SerializedObject(f);
                    var s = so.FindProperty("m_Settings");
                    if (s != null)
                    {
                        var i = s.FindPropertyRelative("Intensity"); if (i != null) i.floatValue = 0.9f;
                        var r = s.FindPropertyRelative("Radius"); if (r != null) r.floatValue = 0.22f;
                        so.ApplyModifiedPropertiesWithoutUndo();
                    }
                }
            }
            QualitySettings.SetQualityLevel(QualitySettings.names.ToList().FindIndex(n => n.Contains("PC")) >= 0 ? QualitySettings.names.ToList().FindIndex(n => n.Contains("PC")) : QualitySettings.GetQualityLevel());
        }

        // ------------------------------------------------------------------ manifest
        class PropDef { public string id, zone, label, type, parent, gate, rig; public float dist; }
        static Dictionary<string, PropDef> LoadManifest()
        {
            var text = File.ReadAllText(Path.Combine(RepoRoot, "data", "room302_interaction_manifest.json"), Encoding.UTF8);
            var wrap = JsonUtility.FromJson<ManifestWrap>(text);
            var d = wrap.props.ToDictionary(p => p.prop_id, p => new PropDef
            { id = p.prop_id, zone = p.zone, label = p.label_ko, type = p.interaction_type, parent = p.parent_container, gate = p.gate, rig = p.required_rig, dist = p.interaction_distance_m });
            var notesPath = Path.Combine(RepoRoot, "data", "room302_scene_notes.json");
            if (File.Exists(notesPath))
            {
                var notes = JsonUtility.FromJson<NotesWrap>(File.ReadAllText(notesPath, Encoding.UTF8));
                foreach (var x in notes.extra_props)
                    d[x.prop_id] = new PropDef { id = x.prop_id, zone = x.zone, label = x.label_ko, type = x.interaction_type, dist = 1.75f };
            }
            return d;
        }
        [System.Serializable] class ManifestProp { public string prop_id, zone, label_ko, interaction_type, parent_container, gate, required_rig; public float interaction_distance_m; }
        [System.Serializable] class ManifestWrap { public ManifestProp[] props; }
        [System.Serializable] class NotesWrap { public ManifestProp[] extra_props; }

        static void SetupColliders(Dictionary<string, GameObject> objs)
        {
            foreach (var kv in objs)
            {
                var go = kv.Value;
                var mf = go.GetComponent<MeshFilter>(); if (!mf) continue;
                bool arch = kv.Key.StartsWith("arch_") || kv.Key.StartsWith("fix_");
                var mc = TZB.GetOrAdd<MeshCollider>(go);
                mc.sharedMesh = mf.sharedMesh;
                if (arch)
                {
                    GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.ContributeGI | StaticEditorFlags.OccluderStatic |
                        StaticEditorFlags.OccludeeStatic | StaticEditorFlags.BatchingStatic | StaticEditorFlags.ReflectionProbeStatic);
                }
                var r = go.GetComponent<MeshRenderer>();
                if (r) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
            }
            // thin decals should not cast shadows or block rays oddly
            foreach (var n in new[] { "living_floor_blood", "living_footprint", "living_broken_glass" })
                if (objs.TryGetValue(n, out var g)) { var r = g.GetComponent<MeshRenderer>(); if (r) r.shadowCastingMode = ShadowCastingMode.Off; }
        }

        // motion presets: (kind, axis, amount, duration)
        static readonly Dictionary<string, (TZMotionKind k, Vector3 axis, float amt, float dur)> Motions = new Dictionary<string, (TZMotionKind, Vector3, float, float)>
        {
            {"entrance_door", (TZMotionKind.Hinge, Vector3.up, -100, 1.1f)},  // Korean front doors open outward
            {"entrance_shoe_cabinet", (TZMotionKind.Hinge, Vector3.up, 105, 0.6f)},
            {"kitchen_fridge_door", (TZMotionKind.Hinge, Vector3.up, -110, 0.8f)},
            {"kitchen_fridge_freezer", (TZMotionKind.Hinge, Vector3.up, -105, 0.7f)},
            {"kitchen_drawer_utensils", (TZMotionKind.Slide, Vector3.left, 0.36f, 0.45f)},
            {"kitchen_drawer_misc", (TZMotionKind.Slide, Vector3.left, 0.40f, 0.5f)},
            {"kitchen_under_sink_left", (TZMotionKind.Hinge, Vector3.up, 100, 0.55f)},
            {"kitchen_under_sink_right", (TZMotionKind.Hinge, Vector3.up, -100, 0.55f)},
            {"kitchen_overhead_cabinet1", (TZMotionKind.Hinge, Vector3.up, 100, 0.55f)},
            {"kitchen_overhead_cabinet2", (TZMotionKind.Hinge, Vector3.up, -100, 0.55f)},
            {"kitchen_microwave_door", (TZMotionKind.Hinge, Vector3.up, 95, 0.5f)},
            {"living_table_drawer", (TZMotionKind.Slide, Vector3.forward, 0.18f, 0.35f)},
            {"living_window", (TZMotionKind.Slide, Vector3.left, 0.55f, 1.0f)},
            {"sleep_bedside_drawer", (TZMotionKind.Slide, Vector3.forward, 0.26f, 0.4f)},
            {"sleep_drawer_top", (TZMotionKind.Slide, Vector3.forward, 0.30f, 0.45f)},
            {"sleep_drawer_mid", (TZMotionKind.Slide, Vector3.forward, 0.30f, 0.45f)},
            {"sleep_drawer_bottom", (TZMotionKind.Slide, Vector3.forward, 0.30f, 0.45f)},
            {"sleep_wardrobe_left", (TZMotionKind.Hinge, Vector3.up, -100, 0.7f)},
            {"sleep_wardrobe_right", (TZMotionKind.Hinge, Vector3.up, 100, 0.7f)},
            {"bath_bath_door", (TZMotionKind.Hinge, Vector3.up, 95, 0.9f)},
            {"bath_toilet_lid", (TZMotionKind.Lift, Vector3.forward, 100, 0.6f)},
            {"bath_toilet_seat", (TZMotionKind.Lift, Vector3.forward, 100, 0.6f)},
            {"bath_mirror_cabinet", (TZMotionKind.Hinge, Vector3.up, 100, 0.5f)},
            {"bath_lower_cabinet", (TZMotionKind.Hinge, Vector3.up, 100, 0.5f)},
            {"bath_window", (TZMotionKind.Hinge, Vector3.forward, 25, 0.7f)},
            {"bath_ceiling", (TZMotionKind.Lift, Vector3.forward, -75, 0.8f)},
            {"bath_drain", (TZMotionKind.Slide, Vector3.up, 0.03f, 0.4f)},
            {"hall_mailbox", (TZMotionKind.Hinge, Vector3.forward, 70, 0.5f)},
            {"sleep_suitcase", (TZMotionKind.None, Vector3.up, 0, 0.5f)},
            {"kitchen_bin", (TZMotionKind.None, Vector3.up, 0, 0.3f)},
            {"living_box_storage", (TZMotionKind.None, Vector3.up, 0, 0.3f)},
            {"sleep_laundry", (TZMotionKind.None, Vector3.up, 0, 0.3f)},
            {"bath_laundry_bin", (TZMotionKind.None, Vector3.up, 0, 0.3f)},
        };
        static readonly HashSet<string> Handheld = new HashSet<string>
        {
            "kitchen_mug","kitchen_plate","kitchen_spoon","kitchen_chopsticks","kitchen_kitchen_knife","kitchen_dish_soap","kitchen_sponge",
            "kitchen_instant_noodle1","kitchen_instant_noodle2","kitchen_fridge_bottle","kitchen_fridge_milk","kitchen_fridge_container","kitchen_fridge_egg",
            "kitchen_fridge_magnet","kitchen_pot","kitchen_pan","kitchen_cutting_board","living_food_container1","living_food_container2","living_disposable_spoon",
            "living_cola_can","living_napkin","living_aircon_remote","living_envelope","living_pen","living_notepad","living_photo_frame","living_book1","living_book2",
            "living_paper_stack","sleep_shirt","bath_soap","bath_toothbrush","bath_toothpaste","bath_cup","bath_shampoo","bath_body_wash","entrance_shoes1",
            "entrance_shoes2","entrance_shoes3","entrance_umbrella","sleep_pillow1","sleep_pillow2","bath_toilet_paper"
        };

        static Dictionary<string, TZInspectableProp> SetupProps(Dictionary<string, GameObject> objs, Dictionary<string, PropDef> manifest)
        {
            var result = new Dictionary<string, TZInspectableProp>();
            var art = LoadArtStatus();
            foreach (var def in manifest.Values)
            {
                if (!objs.TryGetValue(def.id, out var go)) { Debug.LogWarning("[TZBuilder] missing prop mesh " + def.id); continue; }
                var p = TZB.GetOrAdd<TZInspectableProp>(go);
                p.propId = def.id; p.KoreanLabel = def.label; p.interactionDistanceMeters = Mathf.Clamp(def.dist + 0.25f, 0.6f, 2.8f);
                p.kind = def.type switch
                {
                    "container" => TZPropKind.Container, "door" => TZPropKind.Door, "switch" => TZPropKind.Switch,
                    "move" => TZPropKind.Move, "evidence_anchor" => TZPropKind.EvidenceAnchor, _ => TZPropKind.Inspect
                };
                if (def.id == "hall_neighbor_door") p.kind = TZPropKind.Inspect;  // never open a neighbour's door
                p.handheld = Handheld.Contains(def.id);
                if (p.kind == TZPropKind.Move && !p.handheld) p.kind = TZPropKind.Inspect; // large items: observe in place (no fake lift)
                p.artStatus = art.TryGetValue(def.id, out var st) ? st : "UNASSIGNED_NEEDS_QUALITY_ASSET";
                p.artApproved = p.artStatus == "APPROVED";
                p.interactionCollider = go.GetComponent<Collider>();
                if (Motions.TryGetValue(def.id, out var m))
                {
                    var mo = TZB.GetOrAdd<TZPropMotion>(go);
                    mo.kind = m.k; mo.localAxis = m.axis; mo.amount = m.amt; mo.duration = m.dur;
                    p.motion = mo;
                }
                else if (p.kind == TZPropKind.Container || p.kind == TZPropKind.Door)
                {
                    Debug.LogWarning("[TZBuilder] MOTION_MISSING " + def.id + " -> observe only");
                    p.kind = TZPropKind.Inspect;
                }
                p.startActive = def.id == "living_lamp" || def.id == "kitchen_hood" || def.id == "hall_sensor";
                p.startOpen = def.id == "entrance_door";   // found ajar (canon t09), must match server INITIAL_OPEN
                result[def.id] = p;
            }
            foreach (var def in manifest.Values)
                if (!string.IsNullOrEmpty(def.parent) && result.TryGetValue(def.id, out var c) && result.TryGetValue(def.parent, out var par))
                {
                    c.parentContainer = par;
                    // drawer contents travel with the drawer
                    if (par.motion && par.motion.kind == TZMotionKind.Slide) c.transform.SetParent(par.transform, true);
                }
            return result;
        }

        static Dictionary<string, string> LoadArtStatus()
        {
            var d = new Dictionary<string, string>();
            var path = Path.Combine(RepoRoot, "data", "asset_verification.json");
            if (!File.Exists(path)) return d;
            foreach (var line in File.ReadAllLines(path))
            {
                var t = line.Trim().TrimEnd(',');
                if (!t.StartsWith("\"")) continue;
                var parts = t.Split(new[] { "\":" }, System.StringSplitOptions.None);
                if (parts.Length == 2) d[parts[0].Trim('"', ' ')] = parts[1].Trim().Trim('"');
            }
            return d;
        }

        // ------------------------------------------------------------------ lighting
        static Light MkLight(string name, LightType type, Vector3 pos, Color c, float intensity, float range, Transform parent = null, float angle = 90, bool shadows = true)
        {
            var go = new GameObject(name); go.transform.position = pos; if (parent) go.transform.SetParent(parent, true);
            var l = go.AddComponent<Light>(); l.type = type; l.color = c; l.intensity = intensity; l.range = range;
            l.spotAngle = angle; l.innerSpotAngle = angle * 0.55f;
            l.shadows = shadows ? LightShadows.Soft : LightShadows.None; l.shadowStrength = 0.92f; l.shadowBias = 0.02f; l.shadowNormalBias = 0.2f;
            var ad = go.AddComponent<UniversalAdditionalLightData>();
            return l;
        }

        static Vector3 Center(Dictionary<string, GameObject> objs, string n)
        {
            if (!objs.TryGetValue(n, out var g)) return Vector3.zero;
            var r = g.GetComponent<Renderer>(); return r ? r.bounds.center : g.transform.position;
        }
        static Bounds B(Dictionary<string, GameObject> objs, string n)
        {
            return objs.TryGetValue(n, out var g) && g.GetComponent<Renderer>() ? g.GetComponent<Renderer>().bounds : new Bounds();
        }

        static Dictionary<string, Light> SetupLighting(Dictionary<string, GameObject> objs, Dictionary<string, TZInspectableProp> props)
        {
            var L = new Dictionary<string, Light>();
            var lroot = new GameObject("Lighting").transform;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.020f, 0.024f, 0.032f);
            RenderSettings.ambientEquatorColor = new Color(0.014f, 0.014f, 0.016f);
            RenderSettings.ambientGroundColor = new Color(0.008f, 0.007f, 0.006f);
            RenderSettings.skybox = null;
            RenderSettings.reflectionIntensity = 0.6f;
            RenderSettings.fog = false;
            // no default blue sky in mirrors/chrome: environment reflections come from the room probes only
            string cubePath = Root + "/Art/Rendering/BlackCube.cubemap";
            var cube = AssetDatabase.LoadAssetAtPath<Cubemap>(cubePath);
            if (!cube) { cube = new Cubemap(16, TextureFormat.RGBA32, false); for (int f = 0; f < 6; f++) cube.SetPixels(Enumerable.Repeat(Color.black, 256).ToArray(), (CubemapFace)f); cube.Apply(); Directory.CreateDirectory(Path.Combine(Directory.GetParent(Application.dataPath).FullName, Root, "Art/Rendering")); AssetDatabase.CreateAsset(cube, cubePath); }
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.customReflectionTexture = cube;

            var ceil = B(objs, "fix_ceiling_light");
            L["ceiling"] = MkLight("L_CeilingLED", LightType.Spot, ceil.center + Vector3.down * 0.06f, new Color(1f, 0.97f, 0.92f), 9f, 7f, lroot, 155);
            L["ceiling"].transform.rotation = Quaternion.LookRotation(Vector3.down);
            var lamp = B(objs, "living_lamp");
            L["lamp"] = MkLight("L_StandLamp", LightType.Point, new Vector3(lamp.center.x, lamp.max.y - 0.12f, lamp.center.z), new Color(1f, 0.72f, 0.45f), 1.6f, 4.5f, lroot);
            var hood = B(objs, "kitchen_hood");
            L["hood"] = MkLight("L_HoodLamp", LightType.Spot, new Vector3(hood.center.x, hood.min.y - 0.02f, hood.center.z), new Color(1f, 0.82f, 0.6f), 2.2f, 2.2f, lroot, 120);
            L["hood"].transform.rotation = Quaternion.LookRotation(Vector3.down);
            var bl = B(objs, "xprop_bath_light");
            L["bath"] = MkLight("L_Bath", LightType.Point, bl.center + Vector3.down * 0.12f, new Color(0.95f, 0.97f, 1f), 2.4f, 3.5f, lroot);
            var hs = B(objs, "hall_sensor");
            L["hall"] = MkLight("L_HallSensor", LightType.Point, hs.center + Vector3.down * 0.15f, new Color(1f, 0.80f, 0.55f), 1.7f, 6f, lroot);
            var fr = B(objs, "fix_fridge_body");
            L["fridge"] = MkLight("L_FridgeInside", LightType.Point, new Vector3(fr.center.x, fr.min.y + 0.8f, fr.center.z), new Color(0.92f, 0.96f, 1f), 0.9f, 1.0f, lroot, 90, false);
            var ent = B(objs, "entrance_mat");
            L["entrance"] = MkLight("L_EntranceCeil", LightType.Point, new Vector3(ent.center.x, 2.15f, ent.center.z), new Color(1f, 0.9f, 0.75f), 1.4f, 3f, lroot);
            // street light through the window (cool sodium-mix), the reason the room is never pitch black
            var win = B(objs, "living_window");
            var roomC = B(objs, "arch_floor_main").center;
            Vector3 outDir = (new Vector3(win.center.x, 0, win.center.z) - new Vector3(roomC.x, 0, roomC.z)).normalized;
            L["street"] = MkLight("L_StreetThroughWindow", LightType.Spot, win.center + outDir * 2.6f + Vector3.up * 2.2f, new Color(0.62f, 0.70f, 0.92f), 2.2f, 12f, lroot, 34);
            L["street"].transform.LookAt(win.center + Vector3.down * 1.3f - outDir * 1.5f);
            L["fridge"].enabled = false;
            if (props.TryGetValue("kitchen_fridge_door", out var fd) && fd.motion) fd.motion.lightsWhenOpen = new[] { L["fridge"] };

            // reflection probes
            var rp = new GameObject("ReflectionProbe_Room").AddComponent<ReflectionProbe>();
            rp.transform.position = roomC + Vector3.up * 1.3f; rp.size = new Vector3(3.7f, 2.4f, 5.5f); rp.boxProjection = true;
            rp.mode = ReflectionProbeMode.Realtime; rp.refreshMode = ReflectionProbeRefreshMode.OnAwake; rp.resolution = 256;
            var bathC = B(objs, "arch_floor_bath").center;
            var rp2 = new GameObject("ReflectionProbe_Bath").AddComponent<ReflectionProbe>();
            rp2.transform.position = bathC + Vector3.up * 1.2f; rp2.size = new Vector3(1.7f, 2.3f, 1.9f); rp2.boxProjection = true;
            rp2.mode = ReflectionProbeMode.Realtime; rp2.refreshMode = ReflectionProbeRefreshMode.OnAwake; rp2.resolution = 256;

            // post processing
            var vol = new GameObject("PostVolume").AddComponent<Volume>(); vol.isGlobal = true;
            string pp = Root + "/Art/Rendering/Room302_Volume.asset";
            Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(Directory.GetParent(Application.dataPath).FullName, pp)));
            var prof = AssetDatabase.LoadAssetAtPath<VolumeProfile>(pp);
            if (!prof) { prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, pp); }
            foreach (var c in prof.components.ToList()) { prof.Remove(c.GetType()); }
            foreach (var sub in AssetDatabase.LoadAllAssetsAtPath(pp)) if (sub != prof) Object.DestroyImmediate(sub, true);
            var tm = prof.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.ACES);
            var ca = prof.Add<ColorAdjustments>(true); ca.postExposure.Override(0.35f); ca.contrast.Override(14f); ca.saturation.Override(-18f);
            var wb = prof.Add<WhiteBalance>(true); wb.temperature.Override(-6f); wb.tint.Override(2f);
            var bl2 = prof.Add<Bloom>(true); bl2.threshold.Override(1.1f); bl2.intensity.Override(0.25f); bl2.scatter.Override(0.6f);
            var vg = prof.Add<Vignette>(true); vg.intensity.Override(0.24f); vg.smoothness.Override(0.45f);
            var fg = prof.Add<FilmGrain>(true); fg.type.Override(FilmGrainLookup.Thin1); fg.intensity.Override(0.18f); fg.response.Override(0.85f);
            var smh = prof.Add<ShadowsMidtonesHighlights>(true); smh.shadows.Override(new Vector4(0.96f, 0.98f, 1.06f, 0f));
            foreach (var c in prof.components) AssetDatabase.AddObjectToAsset(c, prof);
            EditorUtility.SetDirty(prof); AssetDatabase.SaveAssets();
            vol.sharedProfile = prof;
            return L;
        }

        // ------------------------------------------------------------------ switches / water
        static void AssignSwitches(Dictionary<string, TZInspectableProp> props, Dictionary<string, Light> L)
        {
            void Bind(string id, params Behaviour[] b) { if (props.TryGetValue(id, out var p)) p.switchTargets = b; }
            Bind("living_wall_switch", L["ceiling"]);
            Bind("living_lamp", L["lamp"]);
            Bind("kitchen_hood", L["hood"]);
            Bind("bath_light_switch", L["bath"]);
            Bind("hall_sensor", L["hall"]);
            Bind("entrance_switch", L["entrance"]);
            L["ceiling"].enabled = false; L["bath"].enabled = false; L["entrance"].enabled = false;
            foreach (var id in new[] { "kitchen_faucet", "bath_sink_faucet", "bath_shower_tap" })
            {
                if (!props.TryGetValue(id, out var p)) continue;
                var water = MakeWater(id == "bath_shower_tap" ? FindShowerHead() : p.transform, id);
                p.switchObjects = new[] { water };
                water.SetActive(false);
            }
        }

        static Transform FindShowerHead() => GameObject.Find("bath_shower_head")?.transform;

        static GameObject MakeWater(Transform at, string id)
        {
            var go = new GameObject("FX_Water_" + id);
            var r = at.GetComponent<Renderer>();
            Vector3 p = r ? r.bounds.center : at.position;
            if (id == "kitchen_faucet" && r) p = new Vector3(r.bounds.max.x - 0.01f, r.bounds.max.y - 0.07f, r.bounds.center.z);
            if (id == "bath_sink_faucet" && r) p = new Vector3(r.bounds.center.x, r.bounds.max.y - 0.04f, r.bounds.min.z + 0.01f);
            go.transform.position = p;
            go.transform.rotation = Quaternion.LookRotation(Vector3.down);
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main; main.startSpeed = 1.2f; main.startLifetime = 0.45f; main.startSize = 0.012f; main.maxParticles = 600;
            main.startColor = new Color(0.85f, 0.92f, 1f, 0.55f); main.gravityModifier = 1f; main.simulationSpace = ParticleSystemSimulationSpace.World;
            var em = ps.emission; em.rateOverTime = id == "bath_shower_tap" ? 380 : 260;
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = id == "bath_shower_tap" ? 14 : 1.5f; sh.radius = id == "bath_shower_tap" ? 0.04f : 0.004f;
            var col = ps.collision; col.enabled = true; col.type = ParticleSystemCollisionType.World; col.bounce = 0.05f; col.lifetimeLoss = 0.6f; col.quality = ParticleSystemCollisionQuality.Low;
            var pr = go.GetComponent<ParticleSystemRenderer>(); pr.renderMode = ParticleSystemRenderMode.Stretch; pr.velocityScale = 0.06f; pr.lengthScale = 1.5f;
            var m = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            m.SetColor("_BaseColor", new Color(0.8f, 0.88f, 1f, 0.35f));
            m.SetFloat("_Surface", 1); m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); m.renderQueue = 3000;
            string mp = $"{MatDir}/FX_Water.mat";
            if (!AssetDatabase.LoadAssetAtPath<Material>(mp)) AssetDatabase.CreateAsset(m, mp);
            pr.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(mp);
            return go;
        }

        // ------------------------------------------------------------------ player + UI
        static void SetupPlayerAndUI(Dictionary<string, GameObject> objs)
        {
            var door = B(objs, "entrance_door");
            var roomC = B(objs, "arch_floor_main").center;
            Vector3 outDir = new Vector3(door.center.x - roomC.x, 0, door.center.z - roomC.z).normalized;
            var hallFloor = B(objs, "arch_hall_floor");
            Vector3 spawn = new Vector3(door.center.x + 0.15f, hallFloor.max.y + 0.02f, door.center.z) + outDir * 1.15f;

            var player = new GameObject("Player");
            player.transform.position = spawn;
            player.transform.rotation = Quaternion.LookRotation(-outDir, Vector3.up);
            var cc = player.AddComponent<CharacterController>(); cc.radius = 0.24f; cc.height = 1.75f; cc.center = new Vector3(0, 0.875f, 0); cc.stepOffset = 0.25f; cc.skinWidth = 0.02f;
            var camGo = new GameObject("FPCamera"); camGo.transform.SetParent(player.transform, false); camGo.transform.localPosition = new Vector3(0, 1.62f, 0);
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black; cam.nearClipPlane = 0.03f; cam.farClipPlane = 60; cam.fieldOfView = 62; cam.allowHDR = true; cam.allowMSAA = true;
            var ucd = camGo.AddComponent<UniversalAdditionalCameraData>(); ucd.renderPostProcessing = true; ucd.antialiasing = AntialiasingMode.TemporalAntiAliasing;
            camGo.AddComponent<AudioListener>();
            var flash = MkLight("Flashlight", LightType.Spot, camGo.transform.position + camGo.transform.right * 0.18f - camGo.transform.up * 0.2f, new Color(1f, 0.96f, 0.9f), 8f, 10f, camGo.transform, 50);
            flash.transform.localRotation = Quaternion.Euler(1.5f, -2f, 0);
            flash.innerSpotAngle = 18;
            var pc = player.AddComponent<TZPlayerController>(); pc.cam = cam; pc.flashlight = flash;
            var steps = player.AddComponent<AudioSource>(); steps.spatialBlend = 0; steps.playOnAwake = false; pc.footsteps = steps;
            var dir = player.AddComponent<TZInteractionDirector>(); dir.cam = cam; dir.player = pc;
            dir.uiAudio = player.AddComponent<AudioSource>();

            new GameObject("TZServer").AddComponent<TZServer>();

            // threshold trigger at the 302 door
            var trig = new GameObject("Threshold_302");
            trig.transform.position = new Vector3(door.center.x, door.center.y, door.center.z) - outDir * 0.25f;
            var bc = trig.AddComponent<BoxCollider>(); bc.isTrigger = true; bc.size = new Vector3(1.4f, 2.2f, 1.4f);
            var zt = trig.AddComponent<TZSceneZoneTrigger>();
            var rc = new GameObject("RoomCenter"); rc.transform.position = roomC; zt.roomCenter = rc.transform;

            // HUD
            var ui = new GameObject("HUD");
            var doc = ui.AddComponent<UIDocument>();
            doc.panelSettings = PanelSettingsAsset();
            var hud = ui.AddComponent<TZHud>();
            hud.koreanFont = KoreanFont("NotoSansKR-Variable", "NotoSansKR_SDF");
            hud.documentFont = KoreanFont("NotoSerifKR-Variable", "NotoSerifKR_SDF");
        }

        static PanelSettings PanelSettingsAsset()
        {
            string tss = Root + "/UI/TZRuntimeTheme.tss";
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, tss);
            if (!File.Exists(full)) { File.WriteAllText(full, "@import url(\"unity-theme://default\");\n"); AssetDatabase.ImportAsset(tss); }
            string ps = Root + "/UI/TZPanelSettings.asset";
            var s = AssetDatabase.LoadAssetAtPath<PanelSettings>(ps);
            if (!s) { s = ScriptableObject.CreateInstance<PanelSettings>(); AssetDatabase.CreateAsset(s, ps); }
            s.themeStyleSheet = AssetDatabase.LoadAssetAtPath<ThemeStyleSheet>(tss);
            s.scaleMode = PanelScaleMode.ScaleWithScreenSize; s.referenceResolution = new Vector2Int(1920, 1080); s.match = 0.5f;
            EditorUtility.SetDirty(s); AssetDatabase.SaveAssets();
            return s;
        }

        static FontAsset KoreanFont(string ttf, string assetName)
        {
            string fa = $"{Root}/Art/Fonts/{assetName}.asset";
            var existing = AssetDatabase.LoadAssetAtPath<FontAsset>(fa);
            if (existing) return existing;
            var font = AssetDatabase.LoadAssetAtPath<Font>($"{Root}/Art/Fonts/{ttf}.ttf");
            if (!font) return null;
            var asset = FontAsset.CreateFontAsset(font, 90, 9, UnityEngine.TextCore.LowLevel.GlyphRenderMode.SDFAA, 2048, 2048, AtlasPopulationMode.Dynamic, true);
            AssetDatabase.CreateAsset(asset, fa);
            if (asset.atlasTextures != null) foreach (var t in asset.atlasTextures) if (t) { t.name = assetName + "_Atlas"; AssetDatabase.AddObjectToAsset(t, asset); }
            if (asset.material) { asset.material.name = assetName + "_Mat"; AssetDatabase.AddObjectToAsset(asset.material, asset); }
            AssetDatabase.SaveAssets();
            return asset;
        }

        // ------------------------------------------------------------------ outputs
        static void AddToBuild(string path)
        {
            var list = EditorBuildSettings.scenes.ToList();
            if (!list.Any(s => s.path == path)) list.Insert(0, new EditorBuildSettingsScene(path, true));
            EditorBuildSettings.scenes = list.ToArray();
        }

        static void DumpPositions(Dictionary<string, GameObject> objs)
        {
            var sb = new StringBuilder("{\n");
            bool first = true;
            foreach (var kv in objs.OrderBy(k => k.Key))
            {
                var r = kv.Value.GetComponent<Renderer>(); if (!r) continue;
                var c = r.bounds.center; var p = kv.Value.transform.position;
                if (!first) sb.Append(",\n"); first = false;
                sb.Append($"\"{kv.Key}\": {{\"pivot\": [{p.x:F4}, {p.y:F4}, {p.z:F4}], \"center\": [{c.x:F4}, {c.y:F4}, {c.z:F4}]}}");
            }
            sb.Append("\n}\n");
            File.WriteAllText(Path.Combine(RepoRoot, "data", "room302_prop_positions.json"), sb.ToString(), new UTF8Encoding(false));
        }

        static void WriteCoverage(Dictionary<string, GameObject> objs, Dictionary<string, PropDef> manifest)
        {
            var sb = new StringBuilder("renderer\tclass\tprop_component\tmotion\tart_status\n");
            foreach (var kv in objs.OrderBy(k => k.Key))
            {
                if (!kv.Value.GetComponent<Renderer>()) continue;
                string cls = manifest.ContainsKey(kv.Key) ? "MANIFEST_PROP" : kv.Key.StartsWith("xprop_") ? "EXTRA_PROP" :
                             kv.Key.StartsWith("arch_") ? "ARCHITECTURE" : kv.Key.StartsWith("fix_") ? "FIXED_FURNITURE" : "UNREGISTERED";
                var p = kv.Value.GetComponent<TZInspectableProp>();
                var m = kv.Value.GetComponent<TZPropMotion>();
                sb.Append($"{kv.Key}\t{cls}\t{(p ? p.kind.ToString() : "-")}\t{(m ? m.kind.ToString() : "-")}\t{(p ? p.artStatus : "-")}\n");
            }
            Directory.CreateDirectory(Path.Combine(RepoRoot, "qa", "logs"));
            File.WriteAllText(Path.Combine(RepoRoot, "qa", "logs", "room302_renderer_coverage.tsv"), sb.ToString(), new UTF8Encoding(false));
        }
    }
}

namespace TableZero.EditorTools
{
    static class TZB
    {
        public static T GetOrAdd<T>(GameObject go) where T : Component
        {
            var c = go.GetComponent<T>();
            return c ? c : go.AddComponent<T>();
        }
    }
}
