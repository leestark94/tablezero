using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TableZero.EditorTools
{
    /// <summary>Offline 1080p renders of the seated suspect (no Play Mode): "room" = detective seat view, "face" = close-up, "bust" = chest-up.</summary>
    public static class TZSuspectShot
    {
        public static string Shoot(string outPath, string mode)
        {
            var sc = EditorSceneManager.GetActiveScene();
            if (sc.name != "Case001_Interrogation") sc = EditorSceneManager.OpenScene("Assets/TableZero/Scenes/Case001_Interrogation.unity");
            var actor = GameObject.Find("Actor_s2"); if (!actor) return "no Actor_s2";
            var room = Object.FindFirstObjectByType<TZInterrogationRoom3D>();
            var head = actor.GetComponentsInChildren<Transform>().FirstOrDefault(t => t.name == "mixamorig:Head" || t.name == "Head");
            var go = new GameObject("_shot"); var cam = go.AddComponent<Camera>(); cam.fieldOfView = 36; cam.nearClipPlane = 0.05f;
            var main = room && room.detectiveCamera ? room.detectiveCamera : Camera.main;
            if (mode == "room" && main) { go.transform.SetPositionAndRotation(main.transform.position, main.transform.rotation); cam.fieldOfView = main.fieldOfView; }
            else if (head)
            {
                Vector3 c = head.position + new Vector3(0, mode == "face" ? 0.06f : -0.12f, 0);
                Vector3 toCam = (room ? room.detectiveCamera.transform.position : actor.transform.position + actor.transform.forward) - c; toCam.y = 0; toCam.Normalize();
                float d = mode == "face" ? 0.75f : 1.35f;
                go.transform.position = c + toCam * d; go.transform.LookAt(c); cam.fieldOfView = mode == "face" ? 22 : 30;
            }
            var data = cam.GetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>() ?? cam.gameObject.AddComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>();
            data.renderPostProcessing = true; data.antialiasing = UnityEngine.Rendering.Universal.AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32); cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); tex.Apply();
            File.WriteAllBytes(outPath, tex.EncodeToPNG()); RenderTexture.active = null;
            Object.DestroyImmediate(go); rt.Release(); Object.DestroyImmediate(tex);
            return "shot " + outPath;
        }
    }
}
