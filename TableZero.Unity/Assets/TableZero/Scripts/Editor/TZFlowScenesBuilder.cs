using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace TableZero.EditorTools
{
    /// <summary>Builds the V21.1 flow scenes (MainMenu, HQ desk) and sets the build order:
    /// MainMenu → Room302 → HQ → Interrogation. Re-runnable; never hand-edit these scenes.</summary>
    public static class TZFlowScenesBuilder
    {
        const string Root = "Assets/TableZero";
        public const string MenuScene = Root + "/Scenes/Case001_MainMenu.unity", HQScene = Root + "/Scenes/Case001_HQ.unity";

        [MenuItem("TableZero/Build/Flow Scenes (Menu, HQ)")]
        public static string Build()
        {
            // assets are loaded inside MakeScene, AFTER NewScene: creating a scene unloads references loaded before it
            MakeScene(MenuScene, go => go.AddComponent<TZMainMenu>().koreanFont = Font());
            MakeScene(HQScene, go => go.AddComponent<TZHQDesk>().koreanFont = Font());

            var order = new[] { MenuScene, Root + "/Scenes/Case001_Room302.unity", HQScene, Root + "/Scenes/Case001_Interrogation.unity" };
            EditorBuildSettings.scenes = order.Select(p => new EditorBuildSettingsScene(p, true)).ToArray();
            return "flow scenes built; build order: " + string.Join(" → ", order.Select(System.IO.Path.GetFileNameWithoutExtension)) + " font=" + (Font() ? Font().name : "MISSING");
        }

        static FontAsset Font() => AssetDatabase.FindAssets("NotoSansKR_SDF t:FontAsset").Select(g => AssetDatabase.LoadAssetAtPath<FontAsset>(AssetDatabase.GUIDToAssetPath(g))).FirstOrDefault();

        static void MakeScene(string path, System.Action<GameObject> addUi)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var panel = AssetDatabase.LoadAssetAtPath<PanelSettings>(Root + "/UI/TZPanelSettings.asset");
            var camGo = new GameObject("UICamera"); camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black; cam.cullingMask = 0;
            camGo.AddComponent<UniversalAdditionalCameraData>(); camGo.AddComponent<AudioListener>();
            new GameObject("TZServer").AddComponent<TZServer>();   // first scene starts the local case server; later copies yield to the singleton
            var ui = new GameObject("UI"); var doc = ui.AddComponent<UIDocument>(); doc.panelSettings = panel;
            addUi(ui);
            if (!doc.panelSettings) throw new System.Exception("PanelSettings missing for " + path);
            EditorSceneManager.SaveScene(scene, path);
        }
    }
}
