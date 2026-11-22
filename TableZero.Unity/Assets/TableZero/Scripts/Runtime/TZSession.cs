using System;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// The investigation session the client is bound to. The server owns the id (new case => new id). Anything the client keeps
    /// about a case (scene zone cache, report draft, "report submitted") belongs to ONE session id and is dropped when it changes.
    /// Also reset on every Play start so Enter-Play-Mode-without-domain-reload cannot carry the previous run into a new one.
    /// </summary>
    public static class TZSession
    {
        public static string Id { get; private set; } = "";
        public static event Action Changed;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetOnPlay() { Id = ""; Changed = null; TZSceneZoneTrigger.ServerScene = "hall"; TZHQDesk.ResetDraft(); }

        /// <summary>Bind to the server's session. Returns true when this is a different investigation than before.</summary>
        public static bool Adopt(string id, string serverScene = null)
        {
            if (string.IsNullOrEmpty(id)) return false;
            bool changed = id != Id;
            if (changed) { Id = id; TZHQDesk.ResetDraft(); TZEventLog.Lines.Clear(); }
            if (!string.IsNullOrEmpty(serverScene)) TZSceneZoneTrigger.ServerScene = serverScene;
            if (changed) Changed?.Invoke();
            return changed;
        }

        [Serializable] class SessionState { public string session_id, scene; }
        [Serializable] class StateEnvelope { public SessionState state; }
        [Serializable] class NewCaseData { public string session_id, scene; }
        [Serializable] class NewCaseEnvelope { public bool ok; public NewCaseData data; }

        /// <summary>Ask the server which session/scene it is in and adopt it (zone cache follows the server, never the other way round).</summary>
        public static void Sync(Action done = null)
        {
            if (TZServer.I == null) { done?.Invoke(); return; }
            TZServer.I.Get("/v1/state", (ok, text) =>
            {
                if (ok) { try { var s = JsonUtility.FromJson<StateEnvelope>(text)?.state; if (s != null) Adopt(s.session_id, s.scene); } catch { } }
                done?.Invoke();
            });
        }

        /// <summary>Main menu "new case": the server starts a fresh investigation (evidence, budget, interview memory, report) and we adopt it.</summary>
        public static void StartNewCase(Action<bool> done)
        {
            if (TZServer.I == null) { done?.Invoke(false); return; }
            TZServer.I.Post("/v1/case/new", "{}", (ok, text) =>
            {
                bool good = false;
                if (ok) { try { var d = JsonUtility.FromJson<NewCaseEnvelope>(text)?.data; if (d != null) { Id = ""; Adopt(d.session_id, d.scene); good = true; } } catch { } }
                done?.Invoke(good);
            }, 30);
        }
    }
}
