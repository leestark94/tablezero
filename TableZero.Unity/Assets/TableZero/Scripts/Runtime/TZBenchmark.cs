using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Player-build frame-time benchmark. Active only with the command-line flag `-tzbench &lt;out.csv&gt;`:
    /// walks the detective along a fixed path through 302 (entrance → kitchen → table → bed → bathroom door) with the
    /// flashlight on, records every frame's unscaled delta for `-tzbenchsec` seconds after a warm-up, writes a CSV and
    /// a summary line (avg FPS, 1% low, 0.1% low, max frame), then quits. No gameplay authority.
    /// </summary>
    public sealed class TZBenchmark : MonoBehaviour
    {
        string outPath; float seconds = 40f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            var args = System.Environment.GetCommandLineArgs();
            int i = System.Array.IndexOf(args, "-tzbench");
            if (i < 0) return;
            var go = new GameObject("TZBenchmark"); DontDestroyOnLoad(go);
            var b = go.AddComponent<TZBenchmark>();
            b.outPath = i + 1 < args.Length ? args[i + 1] : Path.Combine(Application.persistentDataPath, "tzbench.csv");
            int s = System.Array.IndexOf(args, "-tzbenchsec");
            if (s >= 0 && s + 1 < args.Length && float.TryParse(args[s + 1], out var v)) b.seconds = v;
        }

        static Vector3 U(float bx, float by, float bz) => new Vector3(-bx, bz, -by);

        IEnumerator Start()
        {
            QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1;
            var args = System.Environment.GetCommandLineArgs();
            bool Has(string f) => System.Array.IndexOf(args, f) >= 0;
            var notes = new List<string>();
            if (Has("-tzstaticprobes"))
            {   // probes render once (after lights settle) instead of every frame
                foreach (var rp in FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None)) rp.refreshMode = UnityEngine.Rendering.ReflectionProbeRefreshMode.ViaScripting;
                notes.Add("static_probes");
            }
            if (Has("-tznoshadowfill"))
            {   // only the flashlight keeps realtime shadows; fixtures rely on baked/indirect shading
                foreach (var l in FindObjectsByType<Light>(FindObjectsSortMode.None)) if (l.name != "Flashlight") l.shadows = LightShadows.None;
                notes.Add("flashlight_shadows_only");
            }
            if (Has("-tznotaa"))
            {
                foreach (var c in FindObjectsByType<Camera>(FindObjectsSortMode.None))
                { var d = c.GetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>(); if (d) d.antialiasing = UnityEngine.Rendering.Universal.AntialiasingMode.SubpixelMorphologicalAntiAliasing; }
                notes.Add("smaa");
            }
            yield return new WaitForSecondsRealtime(2f);
            if (Has("-tzstaticprobes")) foreach (var rp in FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None)) rp.RenderProbe();
            yield return new WaitForSecondsRealtime(2f);   // warm-up: shaders, probes, lightmaps
            var pc = FindAnyObjectByType<TZPlayerController>();
            var path = new List<(Vector3 p, float yaw, float pitch)>
            {
                (U(0.60f, 0.70f, -0.12f), -156, 10), (U(1.00f, 1.60f, 0f), 120, 20), (U(1.25f, 2.60f, 0f), 95, 25),
                (U(1.60f, 3.20f, 0f), 170, 35), (U(2.60f, 3.40f, 0f), -150, 30), (U(2.40f, 4.70f, 0f), -120, 20),
                (U(1.70f, 5.00f, 0f), 0, 10), (U(1.80f, 1.70f, 0f), -70, 10), (U(0.60f, 0.70f, -0.12f), -156, 10),
            };
            var dts = new List<float>(8192);
            float t = 0, seg = seconds / (path.Count - 1);
            while (t < seconds)
            {
                float u = t / seg; int k = Mathf.Min((int)u, path.Count - 2); float f = Mathf.SmoothStep(0, 1, u - k);
                var a = path[k]; var b = path[k + 1];
                if (pc) pc.Place(Vector3.Lerp(a.p, b.p, f), Mathf.LerpAngle(a.yaw, b.yaw, f), Mathf.Lerp(a.pitch, b.pitch, f));
                yield return null;
                float dt = Time.unscaledDeltaTime; dts.Add(dt); t += dt;
            }
            var ms = dts.Select(d => d * 1000f).ToList();
            var sorted = ms.OrderByDescending(x => x).ToList();
            float avg = ms.Average();
            float p1 = sorted.Take(Mathf.Max(1, sorted.Count / 100)).Average();
            float p01 = sorted.Take(Mathf.Max(1, sorted.Count / 1000)).Average();
            var sb = new StringBuilder("frame,ms\n");
            for (int i = 0; i < ms.Count; i++) sb.Append(i).Append(',').Append(ms[i].ToString("F3")).Append('\n');
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath)));
            File.WriteAllText(outPath, sb.ToString());
            string summary = $"variant={string.Join("+", notes)} frames={ms.Count} avg_fps={1000f / avg:F1} avg_ms={avg:F2} low1_fps={1000f / p1:F1} low01_fps={1000f / p01:F1} max_ms={sorted[0]:F1} " +
                             $"res={Screen.width}x{Screen.height} gpu={SystemInfo.graphicsDeviceName} mem_mb={(System.GC.GetTotalMemory(false) / 1048576)}";
            File.WriteAllText(outPath + ".summary.txt", summary);
            Debug.Log("[tzbench] " + summary);
            Application.Quit();
        }
    }
}
