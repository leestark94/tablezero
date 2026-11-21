using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace TableZero.EditorTools
{
    /// <summary>Windows64 player builds for measurement (release config, no dev overlay).</summary>
    public static class TZBuild
    {
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
