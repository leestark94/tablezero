using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace TableZero.EditorTools
{
    /// <summary>
    /// Imports blender/out/Seoyeon.fbx (build_seoyeon.py, MPFB2 + CC0 MakeHuman assets) as a Humanoid, builds URP materials
    /// from the exported textures, seats her in the 3D 진술녹화실 and registers her as suspect s2 with a TZSuspectActor.
    /// </summary>
    public static class TZSuspectCharacterBuilder
    {
        const string Dir = "Assets/TableZero/Art/Characters/Seoyeon";
        const string Fbx = Dir + "/Seoyeon.fbx";
        static string Full(string p) => Path.Combine(Directory.GetParent(Application.dataPath).FullName, p);
        static string RepoRoot => Directory.GetParent(Application.dataPath).Parent.FullName;

        public static string Import()
        {
            string src = Path.Combine(RepoRoot, "blender", "out", "seoyeon");
            Directory.CreateDirectory(Full(Dir));
            File.Copy(Path.Combine(src, "Seoyeon.fbx"), Full(Fbx), true);
            string texSrc = Path.Combine(src, "textures");
            if (Directory.Exists(texSrc))
            {
                Directory.CreateDirectory(Full(Dir + "/Textures"));
                foreach (var f in Directory.GetFiles(texSrc)) File.Copy(f, Full(Dir + "/Textures/" + Path.GetFileName(f)), true);
            }
            AssetDatabase.Refresh();
            foreach (var g in AssetDatabase.FindAssets("t:Texture2D", new[] { Dir + "/Textures" }))
            {
                var p = AssetDatabase.GUIDToAssetPath(g); var ti = (TextureImporter)AssetImporter.GetAtPath(p);
                string n = Path.GetFileNameWithoutExtension(p).ToLower();
                bool normal = n.Contains("normal") || n.EndsWith("_nm") || n.Contains("_nor");
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = !(normal || n.Contains("rough") || n.Contains("spec") || n.Contains("ao"));
                ti.alphaIsTransparency = !normal; ti.maxTextureSize = 4096; ti.anisoLevel = 4; ti.mipmapEnabled = true;
                ti.SaveAndReimport();
            }
            var mi = (ModelImporter)AssetImporter.GetAtPath(Fbx);
            mi.animationType = ModelImporterAnimationType.Human; mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            mi.importBlendShapes = true; mi.importBlendShapeNormals = ModelImporterNormals.Calculate;
            mi.importAnimation = false; mi.importCameras = false; mi.importLights = false;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            mi.optimizeGameObjects = false; mi.SaveAndReimport();
            var avatar = AssetDatabase.LoadAllAssetsAtPath(Fbx).OfType<Avatar>().FirstOrDefault();
            return $"imported: avatar={(avatar ? avatar.isHuman + "/" + avatar.isValid : "none")}";
        }

        static Texture2D Tex(params string[] needles)
        {
            foreach (var g in AssetDatabase.FindAssets("t:Texture2D", new[] { Dir + "/Textures" }))
            {
                var p = AssetDatabase.GUIDToAssetPath(g); string n = Path.GetFileName(p).ToLower();
                if (needles.All(x => n.Contains(x))) return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
            }
            return null;
        }

        /// <summary>Material per mesh: skin (diffuse+normal, low spec), eyes, cutout cards for brows/lashes/hair, cloth.</summary>
        static void BuildMaterials(GameObject inst)
        {
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            Directory.CreateDirectory(Full(Dir + "/Materials"));
            foreach (var r in inst.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                string n = r.name.ToLower();
                var mats = r.sharedMaterials.Select((src, i) =>
                {
                    string mname = $"M_Seoyeon_{r.name}_{i}";
                    string path = $"{Dir}/Materials/{mname}.mat";
                    var m = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (!m) { m = new Material(lit); AssetDatabase.CreateAsset(m, path); }
                    m.shader = lit;
                    Texture2D d = null, nm = null; float smooth = 0.35f; bool cut = false; Color tint = Color.white; float metal = 0f; bool matte = false;
                    string sn = src ? src.name.ToLower() : "";
                    m.SetTextureScale("_BaseMap", Vector2.one); m.SetFloat("_BumpScale", 1f);
                    if (n.Contains("haircap")) { smooth = 0.1f; tint = new Color(0.07f, 0.055f, 0.048f); matte = true; }
                    else if (n.Contains("fringe")) { d = Tex("seoyeon_fringe"); smooth = 0.12f; cut = true; tint = new Color(0.7f, 0.66f, 0.64f); matte = true; }
                    else if (n.Contains("watch"))
                    {
                        if (sn.Contains("dial")) { tint = new Color(0.05f, 0.05f, 0.06f); smooth = 0.92f; metal = 0f; }
                        else { tint = new Color(0.78f, 0.78f, 0.8f); smooth = 0.78f; metal = 1f; }
                    }
                    else if (sn.Contains("knit"))
                    {   // brown chunky cable knit (approved reference) — procedural tile from tools/gen_cloth_textures.py
                        d = Tex("seoyeon_knit_diffuse"); nm = Tex("seoyeon_knit_normal"); smooth = 0.06f;
                        m.SetTextureScale("_BaseMap", new Vector2(3f, 3f)); m.SetFloat("_BumpScale", 1.4f);
                    }
                    else if (sn.Contains("trousers"))
                    {
                        d = Tex("seoyeon_trousers_diffuse"); nm = Tex("seoyeon_trousers_normal"); smooth = 0.12f;
                        m.SetTextureScale("_BaseMap", new Vector2(6f, 6f)); m.SetFloat("_BumpScale", 0.8f);
                    }
                    else if (n.Contains("shoes")) { d = Tex("shoes04", "diffuse"); nm = Tex("shoes04", "normal"); smooth = 0.35f; tint = new Color(0.25f, 0.25f, 0.25f); }
                    else if (n.Contains("hair") || n.Contains("long01")) { d = Tex("long01", "diffuse") ?? Tex("long01"); nm = Tex("long01", "normal"); smooth = 0.12f; cut = true; tint = new Color(0.16f, 0.125f, 0.105f); matte = true; }
                    else if (n.Contains("eyebrow")) { d = Tex("eyebrow"); cut = true; smooth = 0.2f; tint = new Color(0.35f, 0.3f, 0.28f); }
                    else if (n.Contains("eyelash")) { d = Tex("eyelash"); cut = true; smooth = 0.2f; tint = new Color(0.3f, 0.3f, 0.3f); }
                    else if (n.Contains("eye") || n.Contains("high-poly") || n.Contains("low-poly") || n.Contains("_poly")) { d = Tex("brown_eye") ?? Tex("eye"); smooth = 0.9f; }
                    else { d = Tex("seoyeon_skin_diffuse") ?? Tex("lightskinned_female", "diffuse") ?? Tex("skin"); smooth = 0.36f; }
                    m.SetTexture("_BaseMap", d);
                    m.SetColor("_BaseColor", tint);
                    m.SetTexture("_BumpMap", nm);
                    if (nm) m.EnableKeyword("_NORMALMAP"); else m.DisableKeyword("_NORMALMAP");
                    m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", metal);
                    m.SetFloat("_SpecularHighlights", matte ? 0f : 1f); m.SetFloat("_EnvironmentReflections", matte ? 0f : 1f);
                    if (matte) { m.EnableKeyword("_SPECULARHIGHLIGHTS_OFF"); m.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF"); }
                    else { m.DisableKeyword("_SPECULARHIGHLIGHTS_OFF"); m.DisableKeyword("_ENVIRONMENTREFLECTIONS_OFF"); }
                    if (cut)
                    {
                        m.SetFloat("_AlphaClip", 1); m.SetFloat("_Cutoff", 0.35f); m.EnableKeyword("_ALPHATEST_ON");
                        m.SetFloat("_Cull", 0f); m.renderQueue = (int)RenderQueue.AlphaTest;
                    }
                    EditorUtility.SetDirty(m);
                    return m;
                }).ToArray();
                r.sharedMaterials = mats;
                r.updateWhenOffscreen = true;
                r.skinnedMotionVectors = false;
                r.shadowCastingMode = n.Contains("eyelash") || n.Contains("eyebrow") ? ShadowCastingMode.Off : ShadowCastingMode.On;
            }
            AssetDatabase.SaveAssets();
        }

        /// <summary>Called by TZInterrogationBuilder after the room is built.</summary>
        public static void Place(TZInterrogationRoom3D room)
        {
            if (!File.Exists(Full(Fbx))) { Debug.LogWarning("[TZSuspect] Seoyeon.fbx not imported — chair stays empty (2D shot kept)"); return; }
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Fbx);
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            inst.name = "Suspect_s2_이서연";
            var root = new GameObject("Actor_s2").transform; root.SetParent(room.transform, false);
            root.position = room.suspectSeat.position; root.rotation = room.suspectSeat.rotation;
            inst.transform.SetParent(root, false);
            BuildMaterials(inst);
            var anim = inst.GetComponent<Animator>() ?? inst.AddComponent<Animator>();
            anim.avatar = AssetDatabase.LoadAllAssetsAtPath(Fbx).OfType<Avatar>().FirstOrDefault();
            anim.runtimeAnimatorController = null; anim.cullingMode = AnimatorCullingMode.AlwaysAnimate; anim.applyRootMotion = false;
            var actor = root.gameObject.AddComponent<TZSuspectActor>();
            actor.animator = anim; actor.lookTarget = room.detectiveCamera ? room.detectiveCamera.transform : null;
            actor.face = inst.GetComponentsInChildren<SkinnedMeshRenderer>().OrderByDescending(r => r.sharedMesh ? r.sharedMesh.blendShapeCount : 0).FirstOrDefault();
            actor.seatAnchor = room.suspectSeat;
            var top = new GameObject("TableTop").transform; top.SetParent(root, false); top.position = new Vector3(0f, 0.745f, 0f);
            actor.tableTop = top;
            var rl = new GameObject("RestLeft").transform; rl.SetParent(root, false); rl.position = new Vector3(-0.13f, 0.77f, -0.25f);
            var rr = new GameObject("RestRight").transform; rr.SetParent(root, false); rr.position = new Vector3(0.12f, 0.77f, -0.22f);
            actor.restLeft = rl; actor.restRight = rr;
            actor.profile = new TZSuspectActor.Profile { breathPeriod = 4.1f, fidget = 0.55f, gazeAversion = 0.6f, headDown = 0.75f };
            room.cast = room.cast.Where(c => c.suspectId != "s2").Append(new TZInterrogationRoom3D.Cast { suspectId = "s2", character = root.gameObject }).ToArray();
        }
    }
}
