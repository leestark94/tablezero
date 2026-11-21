using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace TableZero.EditorTools
{
    /// <summary>Builds Case001_Interrogation (진술녹화실): the approved dark interrogation shots per suspect + the
    /// TABLE INDEX-style interrogation UI wired to the local case server. Re-runnable; never hand-edit the scene.</summary>
    public static class TZInterrogationBuilder
    {
        const string Root = "Assets/TableZero";
        const string ScenePath = Root + "/Scenes/Case001_Interrogation.unity";
        const string ArtDir = Root + "/Art/Interrogation";

        [MenuItem("TableZero/Build/Interrogation Scene")]
        public static string Build()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var camGo = new GameObject("UICamera"); camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
            camGo.AddComponent<UniversalAdditionalCameraData>();
            camGo.AddComponent<AudioListener>();
            camGo.name = "DetectiveCamera";
            var room3d = TZInterrogationRoomBuilder.AddRoom(cam);
            TZSuspectCharacterBuilder.Place(room3d);
            new GameObject("TZServer").AddComponent<TZServer>();

            var ui = new GameObject("InterrogationUI");
            var doc = ui.AddComponent<UIDocument>();
            doc.panelSettings = AssetDatabase.LoadAssetAtPath<PanelSettings>(Root + "/UI/TZPanelSettings.asset");
            var screen = ui.AddComponent<TZInterrogationScreen>();
            screen.koreanFont = AssetDatabase.FindAssets("NotoSansKR_SDF t:FontAsset").Select(g => AssetDatabase.LoadAssetAtPath<FontAsset>(AssetDatabase.GUIDToAssetPath(g))).FirstOrDefault();
            screen.suspects = new[]
            {
                S("s1", "강도현", "32", "물류설비 업체 야간 교대 근무", "피해자의 전 남자친구", "진술녹화실 1", "21시 20분쯤 나와 바로 직장으로 갔다", "피해자에게 손댄 적 없다"),
                S("s2", "이서연", "30", "화장품 회사 직원·공방 동업자", "피해자의 친구·동업자", "진술녹화실 2", "그날 밤 302호에 가지 않았다", "480만원은 정산이 밀린 것뿐이다"),
                S("s3", "박현수", "39", "배송 집하 계약직", "301호 이웃·최초 신고자", "진술녹화실 3", "22시 7분에 처음 발견해 신고했다", "302호 안에는 들어가지 않았다"),
            };
            screen.grain = Grain();
            screen.serifFont = AssetDatabase.FindAssets("NotoSerifKR_SDF t:FontAsset").Select(g => AssetDatabase.LoadAssetAtPath<FontAsset>(AssetDatabase.GUIDToAssetPath(g))).FirstOrDefault();
            screen.paper = Img($"{ArtDir}/paper_ledger.png");
            Vignette();

            Directory.CreateDirectory(Path.Combine(Directory.GetParent(Application.dataPath).FullName, Root, "Scenes"));
            EditorSceneManager.SaveScene(scene, ScenePath);
            var list = EditorBuildSettings.scenes.ToList();
            if (!list.Any(s => s.path == ScenePath)) { list.Add(new EditorBuildSettingsScene(ScenePath, true)); EditorBuildSettings.scenes = list.ToArray(); }
            return "interrogation scene built: " + ScenePath + " font=" + (screen.koreanFont ? screen.koreanFont.name : "MISSING");
        }

        // statements = canon starting claims (what each person told officers at the scene) — public record, never truth flags
        static TZInterrogationScreen.Suspect S(string id, string name, string age, string job, string rel, string room, params string[] statements)
        {
            return new TZInterrogationScreen.Suspect
            {
                id = id, name = name, age = age, job = job, relation = rel, room = room, statements = statements, feed = Img($"{ArtDir}/feed_{id}.png"),
                background = Img($"{ArtDir}/bg_{id}.jpg"), portrait = Img($"{ArtDir}/portrait_{id}.jpg"),
            };
        }

        static Texture2D Img(string p)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(p);
            if (ti && (ti.maxTextureSize < 4096 || ti.mipmapEnabled || ti.npotScale != TextureImporterNPOTScale.None))
            {   // UI photos: keep native aspect/resolution (no power-of-two squash), no mips, high-quality compression
                ti.maxTextureSize = 4096; ti.mipmapEnabled = false; ti.npotScale = TextureImporterNPOTScale.None;
                ti.textureCompression = TextureImporterCompression.CompressedHQ; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
        }

        static Texture2D Grain()
        {
            string p = ArtDir + "/fx_grain.png";
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, p);
            if (!File.Exists(full))
            {
                int N = 256; var t = new Texture2D(N, N, TextureFormat.RGBA32, false); var rnd = new System.Random(5);
                var px = new Color32[N * N];
                for (int i = 0; i < px.Length; i++) { byte v = (byte)rnd.Next(0, 256); px[i] = new Color32(v, v, v, 255); }
                t.SetPixels32(px); t.Apply(); File.WriteAllBytes(full, t.EncodeToPNG()); Object.DestroyImmediate(t);
                AssetDatabase.ImportAsset(p);
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
        }

        static void Vignette()
        {
            string dir = Root + "/Resources"; string p = dir + "/TZ_Vignette.png";
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, p);
            if (File.Exists(full)) return;
            Directory.CreateDirectory(Path.GetDirectoryName(full));
            int W = 512, H = 288; var t = new Texture2D(W, H, TextureFormat.RGBA32, false); var px = new Color[W * H];
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float u = x / (float)W * 2 - 1, v = y / (float)H * 2 - 1;
                    float d = Mathf.Sqrt(u * u * 0.8f + v * v);
                    px[y * W + x] = new Color(0, 0, 0, Mathf.Clamp01(Mathf.SmoothStep(0.55f, 1.35f, d)) * 0.85f);
                }
            t.SetPixels(px); t.Apply(); File.WriteAllBytes(full, t.EncodeToPNG()); Object.DestroyImmediate(t);
            AssetDatabase.ImportAsset(p);
            var ti = (TextureImporter)AssetImporter.GetAtPath(p); ti.alphaIsTransparency = true; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport();
        }
    }
}
