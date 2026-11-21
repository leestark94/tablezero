using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TableZero.EditorTools
{
    /// <summary>
    /// Adds the real 3D 진술녹화실 2 (blender/out/Interrogation2.fbx from build_interrogation.py) to the interrogation scene:
    /// materials (CC0 PolyHaven sets + procedural), the practical lighting that keeps a seated suspect's eyes under the
    /// pendant shade's cut-off (no overlay tricks), detective camera at seated eye height, one reflection probe, post volume.
    /// Called from TZInterrogationBuilder.Build(); never hand-edit the scene.
    /// </summary>
    public static class TZInterrogationRoomBuilder
    {
        const string Root = "Assets/TableZero";
        const string FbxDst = Root + "/Art/Models/Interrogation2.fbx";
        const string MatDir = Root + "/Art/Materials/Interrogation";
        static string RepoRoot => Directory.GetParent(Application.dataPath).Parent.FullName;
        static Color C(float r, float g, float b, float a = 1) => new Color(r, g, b, a);
        static TZRoom302Builder.MatSpec S(string tex, float uv, Color c, float smooth, float metal = 0, bool tr = false, float em = 0, float nrm = 1)
            => TZRoom302Builder.S(tex, uv, c, smooth, metal, tr, em, nrm);

        static readonly Dictionary<string, TZRoom302Builder.MatSpec> Specs = new Dictionary<string, TZRoom302Builder.MatSpec>
        {
            {"M_IRFloor", S("worn_tile_floor", 0.9f, C(0.46f,0.46f,0.45f), 0.30f)},
            {"M_IRWainscot", S("oak_veneer_01", 1.2f, C(0.20f,0.19f,0.19f), 0.42f, 0, false, 0, 0.5f)},
            {"M_IRAcoustic", S("plastered_wall", 0.8f, C(0.50f,0.48f,0.45f), 0.08f)},
            {"M_IRSeam", S(null, 1, C(0.04f,0.04f,0.04f), 0.05f)},
            {"M_IRCeilTile", S("white_plaster_02", 1.2f, C(0.55f,0.55f,0.53f), 0.05f)},
            {"M_IRCeilGrid", S(null, 1, C(0.62f,0.62f,0.60f), 0.45f, 0.5f)},
            {"M_IRAlu", S(null, 1, C(0.20f,0.20f,0.21f), 0.55f, 0.8f)},
            {"M_IRGlass", S(null, 1, C(0.30f,0.34f,0.38f,0.10f), 0.92f, 0, true)},
            {"M_IRBlind", S(null, 1, C(0.52f,0.51f,0.48f), 0.45f, 0.3f)},
            {"M_IRNightCity", S("gen_nightwin", 1, C(0.75f,0.78f,0.9f), 0.1f, 0, false, 2.6f)},
            {"M_IRTableTop", S("oak_veneer_01", 3.2f, C(0.075f,0.062f,0.055f), 0.58f, 0, false, 0, 0.25f)},
            {"M_IRTableEdge", S(null, 1, C(0.025f,0.025f,0.025f), 0.45f)},
            {"M_IRSteelBlack", S(null, 1, C(0.035f,0.035f,0.04f), 0.45f, 0.75f)},
            {"M_IRChrome", S(null, 1, C(0.8f,0.8f,0.82f), 0.88f, 1)},
            {"M_IRChairFabric", S("rough_linen", 2.5f, C(0.10f,0.10f,0.11f), 0.08f)},
            {"M_IRLampShade", S(null, 1, C(0.05f,0.05f,0.05f), 0.55f, 0.85f)},
            {"M_IRLampInner", S(null, 1, C(0.95f,0.92f,0.85f), 0.4f, 0, false, 1.4f)},
            {"M_IRBulb", S(null, 1, C(1f,0.80f,0.55f), 0.4f, 0, false, 6f)},
            {"M_IRCord", S(null, 1, C(0.02f,0.02f,0.02f), 0.4f)},
            {"M_IRGunmetal", S(null, 1, C(0.11f,0.11f,0.12f), 0.55f, 0.8f)},
            {"M_IRLCD", S(null, 1, C(0.05f,0.09f,0.07f), 0.85f, 0, false, 0.25f)},
            {"M_IRLedRed", S(null, 1, C(1f,0.06f,0.04f), 0.5f, 0, false, 5f)},
            {"M_IRManila", S(null, 1, C(0.58f,0.46f,0.30f), 0.18f)},
            {"M_IRPaper", S(null, 1, C(0.70f,0.69f,0.65f), 0.12f)},
            {"M_IRInk", S(null, 1, C(0.04f,0.04f,0.05f), 0.25f)},
            {"M_IRRule", S(null, 1, C(0.50f,0.50f,0.53f), 0.2f)},
            {"M_IRStampRed", S(null, 1, C(0.55f,0.06f,0.05f), 0.2f)},
            {"M_IRPaperCup", S(null, 1, C(0.86f,0.85f,0.81f), 0.25f)},
            {"M_IRWater", S(null, 1, C(0.55f,0.62f,0.66f,0.30f), 0.96f, 0, true)},
            {"M_IRCabinetGrey", S(null, 1, C(0.34f,0.35f,0.35f), 0.38f, 0.45f)},
            {"M_IRRubber", S(null, 1, C(0.02f,0.02f,0.02f), 0.2f)},
            {"M_IRDoor", S("oak_veneer_01", 1f, C(0.42f,0.36f,0.30f), 0.35f)},
            {"M_IRPlate", S(null, 1, C(0.72f,0.70f,0.65f), 0.6f, 0.8f)},
            {"M_IRCameraBody", S(null, 1, C(0.04f,0.04f,0.045f), 0.4f, 0.2f)},
            {"M_IRLensGlass", S(null, 1, C(0.02f,0.025f,0.03f), 0.95f)},
            {"M_IRSkirting", S(null, 1, C(0.08f,0.08f,0.08f), 0.4f)},
        };

        // Blender (x, y, z) -> Unity
        static Vector3 U(float bx, float by, float bz) => new Vector3(-bx, bz, -by);

        public static TZInterrogationRoom3D AddRoom(Camera cam)
        {
            ImportFbx();
            var mats = BuildMaterials();
            RemapMaterials();
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(FbxDst);
            var room = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            room.name = "Room3D_진술녹화실2";
            foreach (var r in room.GetComponentsInChildren<MeshRenderer>())
            {
                r.gameObject.isStatic = true;
                string n = r.gameObject.name;
                bool castOff = n.StartsWith("arch_night_city") || n.StartsWith("arch_window_glass") || n.Contains("water") || n.StartsWith("arch_ceiling_grid");
                r.shadowCastingMode = castOff ? ShadowCastingMode.Off : ShadowCastingMode.On;
                if (n.StartsWith("fix_table_top") || n.StartsWith("fix_chair_suspect_seat") || n.StartsWith("arch_floor") || n.StartsWith("prop_statement") || n.StartsWith("prop_casefile"))
                    r.gameObject.AddComponent<MeshCollider>();
            }

            // ---------------------------------------------------- camera (seated detective, ~1.17 m eye height, 1.0 m from the table edge)
            cam.transform.SetParent(room.transform.parent, false);
            cam.transform.position = U(0f, -1.02f, 1.17f);
            cam.transform.rotation = Quaternion.Euler(7.5f, 180f, 0f);
            cam.fieldOfView = 36f; cam.nearClipPlane = 0.03f; cam.farClipPlane = 30f;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
            var cd = cam.GetComponent<UniversalAdditionalCameraData>();
            cd.renderPostProcessing = true; cd.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            cd.antialiasingQuality = AntialiasingQuality.High; cd.renderShadows = true;

            // ---------------------------------------------------- lights
            var rig = new GameObject("Lights").transform; rig.SetParent(room.transform, false);
            // pendant key: warm, wide, hard-ish shadows from the shade rim; sits slightly over her side of the table
            var key = Spot(rig, "L_Pendant_Key", U(0f, 0.42f, 1.585f), Quaternion.Euler(90f, 0f, 0f), new Color(1f, 0.80f, 0.58f), 5.8f, 3.2f, 118f, 70f, LightShadows.Soft);
            key.shadowStrength = 0.92f; key.shadowNearPlane = 0.05f;
            key.GetComponent<UniversalAdditionalLightData>().softShadowQuality = SoftShadowQuality.High;
            // caged wall bulb behind-left of her: hair / shoulder rim
            var rim = Point(rig, "L_WallBulb_Rim", U(-1.25f, 1.93f, 1.80f), new Color(1f, 0.72f, 0.45f), 0.85f, 2.6f, LightShadows.Soft);
            // night window through the blinds: cool, low, shadowed (blind stripes on the wall/back)
            var win = Spot(rig, "L_Window_Night", U(0.1f, 2.9f, 1.75f), Quaternion.LookRotation(U(0f, 0.6f, 1.0f) - U(0.1f, 2.9f, 1.75f)), new Color(0.55f, 0.66f, 0.85f), 2.2f, 5f, 70f, 40f, LightShadows.Soft);
            // table bounce: what the lit tabletop throws up under the chin/hands (no shadows, very low)
            var bounce = Point(rig, "L_TableBounce", U(0f, 0.15f, 0.82f), new Color(1f, 0.78f, 0.60f), 0.32f, 1.25f, LightShadows.None);
            // detective-side spill so the near props and hands read (the pendant's rim falls off before the near edge)
            var near = Point(rig, "L_NearSpill", U(0.0f, -0.55f, 1.45f), new Color(1f, 0.84f, 0.66f), 0.45f, 1.6f, LightShadows.None);
            // recording camera tally: tiny red practical
            Point(rig, "L_RecTally", U(-1.24f, 1.32f, 1.48f), new Color(1f, 0.08f, 0.05f), 0.05f, 0.35f, LightShadows.None);

            // ---------------------------------------------------- reflection probe (rendered once at Start by TZInterrogationRoom3D)
            var pgo = new GameObject("ReflectionProbe"); pgo.transform.SetParent(room.transform, false);
            pgo.transform.position = U(0f, 0.15f, 1.25f);
            var probe = pgo.AddComponent<ReflectionProbe>();
            probe.mode = ReflectionProbeMode.Realtime; probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
            probe.timeSlicingMode = ReflectionProbeTimeSlicingMode.NoTimeSlicing;
            probe.size = new Vector3(3.4f, 2.5f, 3.7f); probe.center = U(0f, 0.0f, 0f) - pgo.transform.position + new Vector3(0, 1.25f, -0.15f);
            probe.boxProjection = true; probe.resolution = 256; probe.hdr = true; probe.intensity = 0.8f;

            // ---------------------------------------------------- suspect seat anchor
            var seat = new GameObject("SuspectSeat").transform; seat.SetParent(room.transform, false);
            seat.position = U(0f, 0.80f, 0.455f); seat.rotation = Quaternion.Euler(0f, 0f, 0f);   // Blender -Y facing = Unity +Z (toward the detective)

            // ---------------------------------------------------- ambient + post
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.030f, 0.033f, 0.042f);
            RenderSettings.ambientEquatorColor = new Color(0.024f, 0.021f, 0.019f);
            RenderSettings.ambientGroundColor = new Color(0.010f, 0.009f, 0.008f);
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.reflectionIntensity = 0.6f;
            AddVolume(room.transform);

            var r3d = room.AddComponent<TZInterrogationRoom3D>();
            r3d.detectiveCamera = cam; r3d.suspectSeat = seat; r3d.probe = probe;
            return r3d;
        }

        static Light Spot(Transform p, string n, Vector3 pos, Quaternion rot, Color c, float intensity, float range, float outer, float inner, LightShadows sh)
        {
            var go = new GameObject(n); go.transform.SetParent(p, false); go.transform.position = pos; go.transform.rotation = rot;
            var l = go.AddComponent<Light>(); l.type = LightType.Spot; l.color = c; l.intensity = intensity; l.range = range;
            l.spotAngle = outer; l.innerSpotAngle = inner; l.shadows = sh; l.lightmapBakeType = LightmapBakeType.Realtime;
            go.AddComponent<UniversalAdditionalLightData>();
            return l;
        }

        static Light Point(Transform p, string n, Vector3 pos, Color c, float intensity, float range, LightShadows sh)
        {
            var go = new GameObject(n); go.transform.SetParent(p, false); go.transform.position = pos;
            var l = go.AddComponent<Light>(); l.type = LightType.Point; l.color = c; l.intensity = intensity; l.range = range; l.shadows = sh;
            l.lightmapBakeType = LightmapBakeType.Realtime;
            go.AddComponent<UniversalAdditionalLightData>();
            return l;
        }

        static void AddVolume(Transform parent)
        {
            string path = Root + "/Art/Rendering/Interrogation_Volume.asset";
            var prof = AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (!prof) { prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, path); }
            foreach (var c in prof.components.ToList()) prof.Remove(c.GetType());
            var tm = prof.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.ACES);
            var ca = prof.Add<ColorAdjustments>(true); ca.postExposure.Override(0.55f); ca.contrast.Override(12f); ca.saturation.Override(-14f);
            var wb = prof.Add<WhiteBalance>(true); wb.temperature.Override(4f); wb.tint.Override(2f);
            var bl = prof.Add<Bloom>(true); bl.threshold.Override(1.1f); bl.intensity.Override(0.35f); bl.scatter.Override(0.6f);
            var vg = prof.Add<Vignette>(true); vg.intensity.Override(0.32f); vg.smoothness.Override(0.45f);
            var fg = prof.Add<FilmGrain>(true); fg.type.Override(FilmGrainLookup.Thin1); fg.intensity.Override(0.05f); fg.response.Override(0.85f);
            var sm = prof.Add<ShadowsMidtonesHighlights>(true); sm.shadows.Override(new Vector4(0.96f, 0.98f, 1.04f, -0.02f));
            var dof = prof.Add<DepthOfField>(true); dof.mode.Override(DepthOfFieldMode.Bokeh); dof.focusDistance.Override(1.85f);
            dof.aperture.Override(2.8f); dof.focalLength.Override(50f); dof.bladeCount.Override(7);
            EditorUtility.SetDirty(prof); AssetDatabase.SaveAssets();
            var go = new GameObject("PostVolume"); go.transform.SetParent(parent, false);
            var v = go.AddComponent<Volume>(); v.isGlobal = true; v.priority = 1; v.sharedProfile = prof;
        }

        static void ImportFbx()
        {
            string src = Path.Combine(RepoRoot, "blender", "out", "Interrogation2.fbx");
            string dst = Path.Combine(Directory.GetParent(Application.dataPath).FullName, FbxDst);
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            File.Copy(src, dst, true);
            AssetDatabase.ImportAsset(FbxDst, ImportAssetOptions.ForceUpdate);
            var mi = (ModelImporter)AssetImporter.GetAtPath(FbxDst);
            mi.globalScale = 1; mi.useFileScale = true; mi.bakeAxisConversion = false;
            mi.importAnimation = false; mi.importCameras = false; mi.importLights = false;
            mi.importNormals = ModelImporterNormals.Import; mi.importTangents = ModelImporterTangents.CalculateMikk;
            mi.generateSecondaryUV = false; mi.meshCompression = ModelImporterMeshCompression.Off;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            mi.SaveAndReimport();
        }

        static Dictionary<string, Material> BuildMaterials()
        {
            Directory.CreateDirectory(Path.Combine(Directory.GetParent(Application.dataPath).FullName, MatDir));
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var all = new Dictionary<string, Material>();
            var names = AssetDatabase.LoadAllAssetsAtPath(FbxDst).OfType<Material>().Select(m => m.name).Distinct().ToList();
            foreach (var n in Specs.Keys) if (!names.Contains(n)) names.Add(n);
            foreach (var name in names)
            {
                var path = $"{MatDir}/{name}.mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (!mat) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
                mat.shader = shader;
                if (!Specs.TryGetValue(name, out var s)) s = S(null, 1, Color.gray, 0.3f);
                TZRoom302Builder.ApplySpec(mat, name, s);
                EditorUtility.SetDirty(mat); all[name] = mat;
            }
            AssetDatabase.SaveAssets();
            return all;
        }

        static void RemapMaterials()
        {
            var mi = (ModelImporter)AssetImporter.GetAtPath(FbxDst);
            foreach (var m in AssetDatabase.LoadAllAssetsAtPath(FbxDst).OfType<Material>())
            {
                var proj = AssetDatabase.LoadAssetAtPath<Material>($"{MatDir}/{m.name}.mat");
                if (proj) mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), m.name), proj);
            }
            mi.SaveAndReimport();
        }
    }
}
