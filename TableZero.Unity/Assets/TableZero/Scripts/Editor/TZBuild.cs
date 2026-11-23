using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace TableZero.EditorTools
{
    /// <summary>Windows64 player builds for measurement (release config, no dev overlay).</summary>
    public static class TZBuild
    {
        /// <summary>Whole game (menu -> 302 -> HQ -> interrogation -> ending) as a DEVELOPMENT standalone: it launches the local Python server itself
        /// (RepoRoot is found by walking up to the folder that holds server/api.py) and writes the Pipeline connection so tests can drive it.</summary>
        [MenuItem("TableZero/Build/Windows Full Game (dev standalone)")]
        public static string BuildFull()
        {
            string root = Directory.GetParent(Application.dataPath).Parent.FullName;
            string outDir = Path.Combine(root, "Builds", "Full");
            Directory.CreateDirectory(outDir);
            var scenes = new System.Collections.Generic.List<string>();
            foreach (var sc in EditorBuildSettings.scenes) if (sc.enabled && File.Exists(sc.path)) scenes.Add(sc.path);
            var opts = new BuildPlayerOptions { scenes = scenes.ToArray(), locationPathName = Path.Combine(outDir, "TableZero.exe"), target = BuildTarget.StandaloneWindows64, options = BuildOptions.Development };
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed; PlayerSettings.defaultScreenWidth = 1280; PlayerSettings.defaultScreenHeight = 720; PlayerSettings.runInBackground = true;
            var s = BuildPipeline.BuildPlayer(opts).summary;
            return $"result={s.result} size_mb={s.totalSize / 1048576} secs={s.totalTime.TotalSeconds:F0} errors={s.totalErrors} scenes={scenes.Count} out={opts.locationPathName}";
        }

        [MenuItem("TableZero/Build/Windows Bench Build (302)")]
        public static string BuildBench302()
        {
            string root = Directory.GetParent(Application.dataPath).Parent.FullName;
            string outDir = Path.Combine(root, "Builds", "Bench302");
            Directory.CreateDirectory(outDir);
            var opts = new BuildPlayerOptions
            {
                scenes = new[] { "Assets/TableZero/Scenes/Case001_Room302.unity" },
                locationPathName = Path.Combine(outDir, "TableZero.exe"),
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            };
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1920; PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.runInBackground = true;
            var rep = BuildPipeline.BuildPlayer(opts);
            var s = rep.summary;
            return $"result={s.result} size_mb={s.totalSize / 1048576} secs={s.totalTime.TotalSeconds:F0} errors={s.totalErrors} out={opts.locationPathName}";
        }
    }
}
