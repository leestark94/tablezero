using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace TableZero.EditorTools
{
    /// <summary>Attaches the generated first-person hand (Higgsfield/Tripo H3.1 → Blender decimated FBX) to the FP camera.</summary>
    public static class TZViewModelSetup
    {
        const string Dir = "Assets/TableZero/Art/Characters/Hands";
        public static Vector3 RestPos = new Vector3(0.20f, -0.185f, 0.42f);
        public static Vector3 RestEuler = new Vector3(4.01f, 183.24f, 301.91f);   // measured in Play Mode: lens forward, knuckles up, wrist from lower-right
        public const float Scale = 0.27f;

        static Texture2D Tex(string n, bool linear, bool normal = false)
        {
            string p = $"{Dir}/{n}.png";
            var ti = (TextureImporter)AssetImporter.GetAtPath(p);
            if (ti)
            {
                bool dirty = false;
                if (normal && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; dirty = true; }
                if (linear && !normal && ti.sRGBTexture) { ti.sRGBTexture = false; dirty = true; }
                if (dirty) ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
        }

        public static Material HandMaterial()
        {
            string mp = $"{Dir}/M_FPHand.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(mp);
            if (!m) { m = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(m, mp); }
            m.SetTexture("_BaseMap", Tex("fp_hand_albedo", false)); m.SetColor("_BaseColor", Color.white);
            m.SetTexture("_BumpMap", Tex("fp_hand_normal", true, true)); m.SetFloat("_BumpScale", 1f); m.EnableKeyword("_NORMALMAP");
            m.SetTexture("_MetallicGlossMap", Tex("fp_hand_metalsmooth", true)); m.SetFloat("_Smoothness", 0.85f); m.EnableKeyword("_METALLICSPECGLOSSMAP");
            m.SetTexture("_OcclusionMap", Tex("fp_hand_ao", true)); m.SetFloat("_OcclusionStrength", 1f); m.EnableKeyword("_OCCLUSIONMAP");
            EditorUtility.SetDirty(m);
            return m;
        }

        public static GameObject Attach(Camera cam)
        {
            var fbx = AssetDatabase.LoadAssetAtPath<GameObject>($"{Dir}/fp_hand_right.fbx");
            if (!fbx || !cam) { Debug.LogWarning("[TZViewModel] hand FBX or camera missing"); return null; }
            var old = cam.transform.Find("FP_RightHand"); if (old) Object.DestroyImmediate(old.gameObject);
            var pivot = new GameObject("FP_RightHand");
            pivot.transform.SetParent(cam.transform, false);
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(fbx);
            PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            inst.transform.SetParent(pivot.transform, false);
            inst.transform.localScale = Vector3.one * Scale;
            var mat = HandMaterial();
            foreach (var r in inst.GetComponentsInChildren<Renderer>())
            {
                r.sharedMaterial = mat; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true;
                r.lightProbeUsage = LightProbeUsage.BlendProbes;
            }
            // centre the mesh on the pivot so rotation tuning turns it about the grip
            // faint spill from the flashlight body so the hand is never a black silhouette (no shadows, tiny range)
            var spill = new GameObject("Flashlight_Spill").AddComponent<Light>();
            spill.transform.SetParent(pivot.transform, false); spill.transform.localPosition = new Vector3(-0.06f, 0.10f, -0.02f);
            spill.type = LightType.Point; spill.range = 0.42f; spill.intensity = 0.09f; spill.color = new Color(1f, 0.95f, 0.88f); spill.shadows = LightShadows.None;
            var vm = pivot.AddComponent<TZViewModel>(); vm.restPosition = RestPos; vm.restEuler = RestEuler;
            pivot.transform.localPosition = RestPos; pivot.transform.localRotation = Quaternion.Euler(RestEuler);
            return pivot;
        }
    }
}
