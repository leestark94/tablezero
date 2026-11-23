using System;
using System.IO;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Real in-game latency of every interview turn, from the CLIENT's clock: input accepted -> first character on screen -> line complete,
    /// plus what the server measured (plan / model first token / performer: LLM vs authored fallback). One CSV row per turn
    /// (Editor: repo qa/logs/perf/latency_unity.csv; player: persistentDataPath). Not a model benchmark: this is what the player waited.
    /// </summary>
    public static class TZLatencyLog
    {
        static string path;
        public static void Write(string actor, int qLen, float acceptedS, float firstShownS, float completeS, object receipt, float reactionS = -1f, float subtitleDoneS = -1f)
        {
            try
            {
                if (path == null)
                {
                    string dir = Application.isEditor ? Path.Combine(TZServer.RepoRoot, "qa", "logs", "perf") : Application.persistentDataPath;
                    Directory.CreateDirectory(dir); path = Path.Combine(dir, "latency_unity.csv");
                    if (!File.Exists(path)) File.AppendAllText(path, "utc,session,actor,q_len,accepted_s,reaction_s,first_shown_s,generation_complete_s,subtitle_done_s,performer,model,server_first_token_ms,server_plan_ms,server_latency_ms,fps,editor\n");
                }
                var t = receipt.GetType();
                string F(string n) { var f = t.GetField(n); return f == null ? "" : Convert.ToString(f.GetValue(receipt), System.Globalization.CultureInfo.InvariantCulture); }
                File.AppendAllText(path, string.Join(",", DateTime.UtcNow.ToString("o"), TZSession.Id, actor, qLen, acceptedS.ToString("0.000"), reactionS.ToString("0.000"), firstShownS.ToString("0.000"), completeS.ToString("0.000"), subtitleDoneS.ToString("0.000"),
                    F("performer"), "\"" + F("model") + "\"", F("first_token_ms"), F("plan_ms"), F("latency_ms"), (1f / Mathf.Max(0.0001f, Time.unscaledDeltaTime)).ToString("0"), Application.isEditor) + "\n");
            }
            catch { }
        }
    }
}
