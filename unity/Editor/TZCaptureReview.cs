#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace TableZero.Editor
{
    public static class TZCaptureReview
    {
        [MenuItem("Tools/TABLE ZERO/Capture Play Mode Screenshot")]
        public static void Capture()
        {
            if(!EditorApplication.isPlaying)
            {
                Debug.LogError("Enter Play Mode and stage the camera before screenshot capture");return;
            }
            string folder=Path.Combine(Directory.GetCurrentDirectory(),"ReviewShots");
            Directory.CreateDirectory(folder);
            string scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().name.Replace(" ","_");
            string stamp=DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff");
            string path=Path.Combine(folder,scene+"_"+stamp+".png");
            ScreenCapture.CaptureScreenshot(path,1);
            Debug.Log("TABLE ZERO REVIEW SHOT: " + path + " | verify image actually exists next frames");
        }
    }
}
#endif
