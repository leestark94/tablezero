using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TableZero.EditorTools
{
    /// <summary>Offline 1080p render of the 302 scene from an explicit camera pose (edit mode, no player).</summary>
    public static class TZRoomShot
    {
        public static string Shoot(string outPath, float px, float py, float pz, float lookX, float lookY, float lookZ, float fov = 70f)
        {
            var sc = EditorSceneManager.GetActiveScene();
            if (sc.name != "Case001_Room302") sc = EditorSceneManager.OpenScene("Assets/TableZero/Scenes/Case001_Room302.unity");
            var go = new GameObject("_shot"); var cam = go.AddComponent<Camera>(); cam.fieldOfView = fov; cam.nearClipPlane = 0.05f;
            go.transform.position = new Vector3(px, py, pz); go.transform.LookAt(new Vector3(lookX, lookY, lookZ));
            var data = go.AddComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>();
            data.renderPostProcessing = true; data.antialiasing = UnityEngine.Rendering.Universal.AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32); cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); tex.Apply();
            File.WriteAllBytes(outPath, tex.EncodeToPNG()); RenderTexture.active = null;
            Object.DestroyImmediate(go); rt.Release(); Object.DestroyImmediate(tex);
            return "shot " + outPath;
        }

        public static string Bounds()
        {
            var sc = EditorSceneManager.GetActiveScene();
            if (sc.name != "Case001_Room302") sc = EditorSceneManager.OpenScene("Assets/TableZero/Scenes/Case001_Room302.unity");
            Bounds b = new Bounds(); bool first = true;
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)) { if (first) { b = r.bounds; first = false; } else b.Encapsulate(r.bounds); }
            var spawn = GameObject.Find("PlayerSpawn") ?? GameObject.Find("Player");
            return "bounds " + b.min.ToString("F2") + " " + b.max.ToString("F2") + " spawn=" + (spawn ? spawn.transform.position.ToString("F2") : "none");
        }
    }
}
