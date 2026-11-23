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
        float exDist = 0.42f; Quaternion exStartRot; Vector3 exThin, exLong; float exFrontSign = 1f;
        ObsInfo exInfo; bool exBusy;
        [Serializable] class ObsReq { public string prop_id, point_id; public float[] player_pos; }
        [Serializable] class ObsPoint { public string id, label, face; public bool observed; }
        [Serializable] class ObsInfo { public string prop_id, label, intro; public int total, done; public bool photographed; public ObsPoint[] points; }
        [Serializable] class ObsInfoResp { public bool ok; public ObsInfo data; public string error; }
        [Serializable] class ObsData { public string point, label, text, limit, note; public bool first, complete; public int done, total; }
        [Serializable] class ObsResp { public bool ok; public ObsData data; public string error; }
        [Serializable] class HintData { public string hint; public int level; }
        [Serializable] class HintResp { public bool ok; public HintData data; }
        // overlapping targets (a receipt lying on a bag): all candidates under the crosshair, Tab cycles
        readonly System.Collections.Generic.List<TZInspectableProp> cands = new System.Collections.Generic.List<TZInspectableProp>(); int candIx;

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
            if (kb.tabKey.wasPressedThisFrame && cands.Count > 1) { candIx = (candIx + 1) % cands.Count; current = null; }   // cycle overlapped targets
            UpdateFocus();
            if (kb.gKey.wasPressedThisFrame) ToggleGloves();
            if (current == null || pending) { collectHeld = 0; return; }
            if (kb.eKey.wasPressedThisFrame) current.TryRequest(current.PrimaryAction());
            else if (kb.qKey.wasPressedThisFrame) Send(current, TZPropAction.Inspect);
            else if (kb.vKey.wasPressedThisFrame && ExaminableKind(current)) StartCoroutine(BeginExamineServer(current));
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
            cands.Clear();
            if (cam)
            {
                // aim tolerance scales with the screen (a fixed pixel-size crosshair on a small window is a bigger cone): ~1.2 degrees per 100 px of half-height
                float tol = Mathf.Clamp(0.05f + 0.00005f * (1080f - Mathf.Min(Screen.height, 1080)), 0.05f, 0.11f);
                var hits = Physics.SphereCastAll(cam.transform.position, tol, cam.transform.forward, reach, mask, QueryTriggerInteraction.Ignore);
                var seen = new System.Collections.Generic.Dictionary<TZInspectableProp, float>();
                foreach (var h in hits)
                {
                    var c = h.collider.GetComponentInParent<TZInspectableProp>();
                    if (!c || !c.CanTarget() || h.distance > c.interactionDistanceMeters) continue;
                    // angular distance from the crosshair ray to the object's nearest point (the ray itself hitting it counts as 0)
                    Vector3 near = h.collider.ClosestPoint(cam.transform.position + cam.transform.forward * Mathf.Max(0.2f, h.distance));
                    float ang = Vector3.Angle(cam.transform.forward, near - cam.transform.position);
                    if (Physics.Raycast(cam.transform.position, cam.transform.forward, out var direct, reach, mask, QueryTriggerInteraction.Ignore) && direct.collider.GetComponentInParent<TZInspectableProp>() == c) ang = 0f;
                    if (!seen.TryGetValue(c, out var old) || ang < old) seen[c] = ang;
                }
                foreach (var kv in seen) cands.Add(kv.Key);
                cands.Sort((x, y) => seen[x].CompareTo(seen[y]));
                if (cands.Count > 0)
                {
                    // hysteresis: keep the current target while it is still a near-best candidate (no flicker between bag and receipt)
                    if (current != null && cands.Contains(current) && seen[current] <= seen[cands[0]] + 2.5f) candIx = cands.IndexOf(current);
                    else if (candIx >= cands.Count || current == null || !cands.Contains(current)) candIx = 0;
                    next = cands[Mathf.Clamp(candIx, 0, cands.Count - 1)];
                }
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
                    TZHud.I.SetFocus(current.KoreanLabel + (cands.Count > 1 ? $"  ({cands.IndexOf(current) + 1}/{cands.Count})" : ""), label + (cands.Count > 1 ? "   Tab 겹친 대상 전환" : ""));
                }
            }
        }

        string lastPrompt;
        static bool ExaminableKind(TZInspectableProp p) => p != null && (p.handheld || p.kind == TZPropKind.Move || p.kind == TZPropKind.EvidenceAnchor);

        static string PromptFor(TZInspectableProp p)
        {
            string extra = p.kind == TZPropKind.Inspect || p.kind == TZPropKind.EvidenceAnchor ? "" : "   Q 자세히";
            // same verbs for mundane and case-relevant objects: the HUD never hints which matters
            string collect = p.kind == TZPropKind.Move || p.kind == TZPropKind.EvidenceAnchor || p.handheld ? "   X 길게 채취" : "";
            return VerbKo(p) + extra + (ExaminableKind(p) ? "   V 확대 조사" : "") + "   C 촬영" + collect;
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
                if (a == TZPropAction.Move && p.handheld) StartCoroutine(BeginExamineServer(p));
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

        // ---------- hands-on examine: drag to rotate, wheel to zoom, R = original pose, F = record what faces the camera, H = hint, E = put back ----------
        IEnumerator BeginExamineServer(TZInspectableProp p)
        {
            if (pending || TZServer.I == null || examining) yield break;
            pending = true; ObsInfo info = null; string raw = "";
            TZServer.I.Post("/v1/prop/observe_info", JsonUtility.ToJson(new ObsReq { prop_id = p.propId, player_pos = PlayerPos() }), (ok, t) => { raw = t; if (ok) { try { info = JsonUtility.FromJson<ObsInfoResp>(t)?.data; } catch { } } });
            while (raw == "") yield return null;
            pending = false;
            if (info == null) { Fail(raw); yield break; }
            exInfo = info; BeginExamine(p);
        }

        void BeginExamine(TZInspectableProp p)
        {
            examining = p;
            exParent = p.transform.parent; exPos = p.transform.position; exRot = p.transform.rotation; exStartRot = exRot;
            exSpin = Vector2.zero; exDist = 0.42f; exBusy = false;
            // thin axis = the face normal of a phone / receipt / sheet; the face that points up while it lies on the floor is its "front"
            var rends = p.GetComponentsInChildren<MeshFilter>();
            Bounds lb = new Bounds(); bool first = true;
            foreach (var mf in rends) { if (!mf.sharedMesh) continue; var b = mf.sharedMesh.bounds; var t = mf.transform;
                Vector3 c = p.transform.InverseTransformPoint(t.TransformPoint(b.center)); var bb = new Bounds(c, p.transform.InverseTransformVector(t.TransformVector(b.size))); if (first) { lb = bb; first = false; } else lb.Encapsulate(bb); }
            Vector3 e = lb.extents; int thin = 0, lng = 0; float[] ev = { Mathf.Abs(e.x), Mathf.Abs(e.y), Mathf.Abs(e.z) };
            for (int i = 1; i < 3; i++) { if (ev[i] < ev[thin]) thin = i; if (ev[i] > ev[lng]) lng = i; }
            Vector3 ax(int i) => i == 0 ? p.transform.right : i == 1 ? p.transform.up : p.transform.forward;
            exThin = ax(thin).normalized; exLong = ax(lng).normalized; exFrontSign = Vector3.Dot(exThin, Vector3.up) >= 0 ? 1f : -1f;
            if (player) player.inputLocked = true;
            StartCoroutine(HoldInFront());
            UpdateExamineHud();
            if (TZHud.I && exInfo != null && !string.IsNullOrEmpty(exInfo.intro)) TZHud.I.ShowSubtitle(exInfo.intro, 5f);
        }

        IEnumerator HoldInFront()
        {
            var p = examining; if (!p) yield break;
            Vector3 a = p.transform.position;
            for (float k = 0; k < 1 && examining == p; k += Time.deltaTime / 0.35f) { p.transform.position = Vector3.Lerp(a, ExTarget(), Mathf.SmoothStep(0, 1, k)); yield return null; }
        }
        Vector3 ExTarget() => cam.transform.position + cam.transform.forward * exDist - cam.transform.up * 0.05f;

        void UpdateExamineHud()
        {
            if (!TZHud.I || examining == null) return;
            string prog = exInfo != null ? $"관찰 {exInfo.done}/{exInfo.total}   " : "";
            TZHud.I.SetFocus(examining.KoreanLabel, prog + "드래그 회전 · 휠 확대 · F 이 면 기록 · H 힌트 · R 처음 방향 · E 내려놓기(현장 복귀)");
        }

        // which recorded point is the camera looking at right now? (front/back by the face that was up, edge by the long axis, any = always)
        string FacingPointId()
        {
            if (exInfo?.points == null) return null;
            Vector3 toCam = (cam.transform.position - examining.transform.position).normalized;
            float face = Vector3.Dot(exThin, toCam) * exFrontSign;          // >0 => the original front faces the camera
            bool edgeOn = Mathf.Abs(Vector3.Dot(exThin, toCam)) < 0.45f;
            foreach (var pt in exInfo.points)
            {
                if (pt.observed) continue;
                bool ok = pt.face == "any" || (pt.face == "front" && face > 0.8f) || (pt.face == "back" && face < -0.8f) || (pt.face == "edge" && edgeOn);
                if (ok && exDist <= 0.46f) return pt.id;
            }
            return null;
        }

        void UpdateExamine(Keyboard kb)
        {
            var m = Mouse.current;
            if (m != null)
            {
                if (m.leftButton.isPressed)   // rotate only while dragging (no accidental spin)
                {
                    Vector2 d = m.delta.ReadValue() * 0.3f;
                    examining.transform.Rotate(cam.transform.up, -d.x, Space.World);
                    examining.transform.Rotate(cam.transform.right, d.y, Space.World);
                }
                float w = m.scroll.ReadValue().y;
                if (Mathf.Abs(w) > 0.01f) { exDist = Mathf.Clamp(exDist - Mathf.Sign(w) * 0.04f, 0.2f, 0.7f); examining.transform.position = ExTarget(); }
            }
            if (kb.rKey.wasPressedThisFrame) StartCoroutine(ResetPose());
            if (kb.fKey.wasPressedThisFrame && !exBusy) StartCoroutine(RecordFacing());
            if (kb.hKey.wasPressedThisFrame && !exBusy) StartCoroutine(AskHint());
            if (kb.eKey.wasPressedThisFrame || kb.escapeKey.wasPressedThisFrame) StartCoroutine(PutBack());
        }

        IEnumerator ResetPose()
        {
            var p = examining; if (!p) yield break; Quaternion a = p.transform.rotation;
            for (float k = 0; k < 1 && examining == p; k += Time.deltaTime / 0.3f) { p.transform.rotation = Quaternion.Slerp(a, exStartRot, Mathf.SmoothStep(0, 1, k)); yield return null; }
        }

        IEnumerator RecordFacing()
        {
            string id = FacingPointId();
            if (id == null) { if (TZHud.I) TZHud.I.Toast("아직 눈에 띄는 곳을 찾지 못했다 — 돌려 보거나 가까이 당겨 보자 (H 힌트)"); yield break; }
            exBusy = true; string raw = ""; ObsData od = null;
            TZServer.I.Post("/v1/prop/observe", JsonUtility.ToJson(new ObsReq { prop_id = examining.propId, point_id = id, player_pos = PlayerPos() }), (ok, t) => { raw = t; if (ok) { try { od = JsonUtility.FromJson<ObsResp>(t)?.data; } catch { } } });
            while (raw == "") yield return null; exBusy = false;
            if (od == null) { Fail(raw); yield break; }
            if (exInfo != null) { exInfo.done = od.done; foreach (var pt in exInfo.points) if (pt.id == od.point) { pt.observed = true; pt.label = od.label; } }
            if (TZHud.I)
            {
                TZHud.I.ShowSubtitle((od.first ? "[기록] " + od.label + " — " : "") + od.text + (string.IsNullOrEmpty(od.limit) ? "" : "\n한계: " + od.limit), 8f);
                if (!string.IsNullOrEmpty(od.note) && od.first) TZHud.I.Toast(od.note, 4f);
                if (od.complete) TZHud.I.Toast("이 물건에서 볼 수 있는 곳을 모두 기록했다", 3f);
            }
            TZEventLog.Record("observe_" + id, examining.propId); UpdateExamineHud();
        }

        IEnumerator AskHint()
        {
            exBusy = true; string raw = ""; string h = null;
            TZServer.I.Post("/v1/prop/hint", JsonUtility.ToJson(new ObsReq { prop_id = examining.propId, player_pos = PlayerPos() }), (ok, t) => { raw = t; if (ok) { try { h = JsonUtility.FromJson<HintResp>(t)?.data?.hint; } catch { } } });
            while (raw == "") yield return null; exBusy = false;
            if (TZHud.I && !string.IsNullOrEmpty(h)) TZHud.I.ShowSubtitle("힌트: " + h, 5f);
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
