using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

namespace TableZero
{
    /// <summary>
    /// Scene investigation loop: look → (server) approve → physical motion / hands-on examine → observation.
    /// Keys: E = open/close/switch or pick up, Q = look closely, C = photograph, X (hold) = collect & seal,
    /// G = gloves on/off. Every mutation waits for the server; a pending intent blocks duplicates.
    /// </summary>
    public sealed class TZInteractionDirector : MonoBehaviour
    {
        public Camera cam;
        public TZPlayerController player;
        public LayerMask mask = ~0;
        public float reach = 2.2f;
        public float collectHoldSeconds = 0.7f;
        public AudioSource uiAudio;
        public AudioClip shutterClip, glovesClip;

        TZInspectableProp current;
        bool pending;
        bool glovesOn;
        float collectHeld;
        // hands-on examine
        TZInspectableProp examining;
        Vector3 exPos; Quaternion exRot; Transform exParent;
        Vector2 exSpin;

        [Serializable] class PropReq { public string prop_id, verb, action_id; public float[] player_pos; }
        [Serializable] class ProcReq { public string prop_id, action; public float[] player_pos; }
        [Serializable] class GloveReq { public bool on; }
        [Serializable] class PropData { public string prop_id, verb, observation, label, art_status; public bool opened, active, moved; public string[] procedure_actions; }
        [Serializable] class PropResp { public bool ok; public PropData data; public string error; }
        [Serializable] class ProcData { public string prop_id, note; public bool photographed, collected, duplicate; public int marker_no; public string[] defects; }
        [Serializable] class ProcResp { public bool ok; public ProcData data; public string error; }

        static string Verb(TZPropAction a) =>
            a == TZPropAction.Open ? "open" : a == TZPropAction.Close ? "close" : a == TZPropAction.Activate ? "activate" :
            a == TZPropAction.Deactivate ? "deactivate" : a == TZPropAction.Move ? "move" : "inspect";

        static string VerbKo(TZInspectableProp p)
        {
            switch (p.PrimaryAction())
            {
                case TZPropAction.Open: return p.kind == TZPropKind.Door ? "E 열기" : "E 열기";
                case TZPropAction.Close: return "E 닫기";
                case TZPropAction.Activate: return "E 켜기";
                case TZPropAction.Deactivate: return "E 끄기";
                case TZPropAction.Move: return p.handheld ? "E 들어 보기" : "E 들추기";
                default: return "E 살펴보기";
            }
        }

        void Awake()
        {
            foreach (var p in FindObjectsByType<TZInspectableProp>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                p.OnInteractionRequested += OnRequested;
        }

        void Update()
        {
            var kb = Keyboard.current; if (kb == null) return;
            if (examining) { UpdateExamine(kb); return; }
            UpdateFocus();
            if (kb.gKey.wasPressedThisFrame) ToggleGloves();
            if (current == null || pending) { collectHeld = 0; return; }
            if (kb.eKey.wasPressedThisFrame) current.TryRequest(current.PrimaryAction());
            else if (kb.qKey.wasPressedThisFrame) Send(current, TZPropAction.Inspect);
            else if (kb.cKey.wasPressedThisFrame && !kb.leftShiftKey.isPressed) Procedure(current, "photograph");
            if (kb.xKey.isPressed)
            {
                collectHeld += Time.deltaTime;
                if (collectHeld >= collectHoldSeconds) { collectHeld = -999; Procedure(current, "collect"); }
            }
            else collectHeld = 0;
        }

        void UpdateFocus()
        {
            TZInspectableProp next = null;
            if (cam && Physics.Raycast(cam.transform.position, cam.transform.forward, out var hit, reach, mask, QueryTriggerInteraction.Ignore))
            {
                var c = hit.collider.GetComponentInParent<TZInspectableProp>();
                if (c && c.CanTarget() && hit.distance <= c.interactionDistanceMeters) next = c;
            }
            // same target but its state changed (door closed/opened, switch toggled): the prompt must follow at once, not on the next retarget
            string label = next != null ? PromptFor(next) : null;
            if (next == current && label == lastPrompt) return;
            current = next; lastPrompt = label;
            if (TZHud.I)
            {
                if (current == null) TZHud.I.SetFocus(null, null);
                else
                {
                    TZHud.I.SetFocus(current.KoreanLabel, label);
                }
            }
        }

        string lastPrompt;
        static string PromptFor(TZInspectableProp p)
        {
            string extra = p.kind == TZPropKind.Inspect || p.kind == TZPropKind.EvidenceAnchor ? "" : "   Q 자세히";
            // same verbs for mundane and case-relevant objects: the HUD never hints which matters
            string collect = p.kind == TZPropKind.Move || p.kind == TZPropKind.EvidenceAnchor || p.handheld ? "   X 길게 채취" : "";
            return VerbKo(p) + extra + "   C 촬영" + collect;
        }

        void OnRequested(TZInspectableProp p, TZPropAction a) => Send(p, a);

        float[] PlayerPos()
        {
            var v = cam ? cam.transform.position : transform.position;
            return new[] { v.x, v.y, v.z };
        }

        void Send(TZInspectableProp p, TZPropAction a)
        {
            if (pending || TZServer.I == null) return;
            pending = true;
            var body = JsonUtility.ToJson(new PropReq { prop_id = p.propId, verb = Verb(a), action_id = TZServer.NewActionId(), player_pos = PlayerPos() });
            TZServer.I.Post("/v1/prop/interact", body, (ok, text) =>
            {
                pending = false;
                if (!ok) { Fail(text); return; }
                var r = JsonUtility.FromJson<PropResp>(text);
                if (r == null || !r.ok || r.data == null) { Fail(text); return; }
                p.ApplyServerApproved(a);
                if (a == TZPropAction.Move && p.handheld) BeginExamine(p);
                if (!string.IsNullOrEmpty(r.data.observation) && TZHud.I) TZHud.I.ShowSubtitle(r.data.observation);
                TZEventLog.Record("prop_" + Verb(a), p.propId);
            });
        }

        void Procedure(TZInspectableProp p, string action)
        {
            if (pending || TZServer.I == null) return;
            pending = true;
            if (action == "photograph" && uiAudio && shutterClip) uiAudio.PlayOneShot(shutterClip, 0.6f);
            var body = JsonUtility.ToJson(new ProcReq { prop_id = p.propId, action = action, player_pos = PlayerPos() });
            TZServer.I.Post("/v1/prop/procedure", body, (ok, text) =>
            {
                pending = false;
                if (!ok) { Fail(text); return; }
                var r = JsonUtility.FromJson<ProcResp>(text);
                if (r?.data == null) { Fail(text); return; }
                if (TZHud.I) TZHud.I.Toast(r.data.note);
                if (action == "photograph")
                {
                    StartCoroutine(Flash());
                    if (TZEvidenceMarkers.I && r.data.marker_no > 0) TZEvidenceMarkers.I.Place(r.data.marker_no, p, cam ? cam.transform.position : p.transform.position);
                }
                if (action == "collect" && r.data.collected && !r.data.duplicate)
                {
                    // bagged: the object leaves the scene physically (chain of custody)
                    foreach (var rd in p.GetComponentsInChildren<Renderer>()) rd.enabled = false;
                    foreach (var cl in p.GetComponentsInChildren<Collider>()) cl.enabled = false;
                }
                TZEventLog.Record("procedure_" + action, p.propId);
            });
        }

        void ToggleGloves()
        {
            if (pending || TZServer.I == null) return;
            pending = true;
            TZServer.I.Post("/v1/player/gloves", JsonUtility.ToJson(new GloveReq { on = !glovesOn }), (ok, text) =>
            {
                pending = false;
                if (!ok) { Fail(text); return; }
                glovesOn = !glovesOn;
                if (uiAudio && glovesClip) uiAudio.PlayOneShot(glovesClip, 0.5f);
                if (TZHud.I) TZHud.I.Toast(glovesOn ? "니트릴 장갑 착용" : "장갑 벗음");
            });
        }

        IEnumerator Flash()
        {
            var l = cam ? cam.GetComponentInChildren<Light>() : null;
            if (!l) yield break;
            float i0 = l.intensity; bool was = l.enabled;
            l.enabled = true; l.intensity = i0 * 6f;
            yield return new WaitForSecondsRealtime(0.06f);
            l.intensity = i0; l.enabled = was;
        }

        void Fail(string raw)
        {
            string msg = raw ?? "";
            if (msg.Contains("Open parent container")) msg = "먼저 열어야 손이 닿는다";
            else if (msg.Contains("Too far")) msg = "조금 더 가까이";
            else if (msg.Contains("permission required")) msg = "절차상 허가가 필요하다";
            else if (msg.Contains("Authored mesh")) msg = "이 물체는 아직 조사 에셋 검수 전이다";
            else if (msg.Contains("not in current scene")) msg = "지금 위치에서는 손댈 수 없다";
            else if (msg.Contains("not collectable")) msg = "이건 채취할 대상이 아니다";
            else if (!TZServer.I || !TZServer.I.Online) msg = "로컬 수사 서버 연결 대기 중";
            if (TZHud.I) TZHud.I.Toast(msg);
            Debug.Log("[interaction] " + raw);
        }

        // ---------- hands-on examine (pick up, turn over, put back exactly) ----------
        void BeginExamine(TZInspectableProp p)
        {
            examining = p;
            exParent = p.transform.parent; exPos = p.transform.position; exRot = p.transform.rotation;
            exSpin = Vector2.zero;
            if (player) player.inputLocked = true;
            StartCoroutine(MoveTo(p.transform, cam.transform.position + cam.transform.forward * 0.42f - cam.transform.up * 0.05f, 0.35f));
            if (TZHud.I) TZHud.I.SetFocus(p.KoreanLabel, "마우스로 돌려 보기   E 내려놓기");
        }

        void UpdateExamine(Keyboard kb)
        {
            var m = Mouse.current;
            if (m != null)
            {
                Vector2 d = m.delta.ReadValue() * 0.25f;
                examining.transform.Rotate(cam.transform.up, -d.x, Space.World);
                examining.transform.Rotate(cam.transform.right, d.y, Space.World);
            }
            if (kb.eKey.wasPressedThisFrame || kb.escapeKey.wasPressedThisFrame) StartCoroutine(PutBack());
        }

        IEnumerator MoveTo(Transform t, Vector3 target, float dur)
        {
            Vector3 a = t.position;
            for (float k = 0; k < 1; k += Time.deltaTime / dur)
            {
                t.position = Vector3.Lerp(a, target, Mathf.SmoothStep(0, 1, k));
                yield return null;
            }
            t.position = target;
        }

        IEnumerator PutBack()
        {
            var p = examining; if (!p) yield break;
            Vector3 a = p.transform.position; Quaternion ra = p.transform.rotation;
            for (float k = 0; k < 1; k += Time.deltaTime / 0.35f)
            {
                float e = Mathf.SmoothStep(0, 1, k);
                p.transform.SetPositionAndRotation(Vector3.Lerp(a, exPos, e), Quaternion.Slerp(ra, exRot, e));
                yield return null;
            }
            p.transform.SetPositionAndRotation(exPos, exRot);
            examining = null;
            if (player) player.inputLocked = false;
            current = null;
        }
    }

    /// <summary>Local QA trace of player actions (server keeps the authoritative log).</summary>
    public static class TZEventLog
    {
        public static readonly System.Collections.Generic.List<string> Lines = new System.Collections.Generic.List<string>();
        public static void Record(string kind, string id)
        {
            string l = $"{Time.realtimeSinceStartup:F2}\t{kind}\t{id}";
            Lines.Add(l);
            Debug.Log("[tz-event] " + l);
        }
    }
}
