using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;
using static TableZero.TZUIKit;

namespace TableZero
{
    /// <summary>
    /// HQ_DESK (수사본부): the strategic hub between the scene and the interview room. Everything shown comes from the
    /// authoritative server: acquired evidence (with source and limits), record/forensic requests (cost, real-world
    /// turnaround, why blocked), case clock. Actions: summon a suspect, request records, revisit 302, notebook,
    /// final report (draft freely, submit once) → ending. No identity hint anywhere on this screen.
    /// </summary>
    public sealed class TZHQDesk : MonoBehaviour
    {
        public FontAsset koreanFont;
        public const string RoomScene = "Case001_Room302", InterrogationScene = "Case001_Interrogation", MenuScene = "Case001_MainMenu";

        [Serializable] class SceneReq { public string scene; }
        [Serializable] class ReqReq { public string request_id; }
        [Serializable] class EvidenceCard { public string id, name, detail, source, limitation, strength; }
        [Serializable] class EvidenceList { public EvidenceCard[] evidence; }
        [Serializable] class EvidenceResp { public bool ok; public EvidenceList data; public string error; }
        [Serializable] class ReqOpt { public string request_id, label, blocked_reason; public int cost, minutes; public bool available, done; }
        [Serializable] class Options { public int budget_left, budget_total; public ReqOpt[] requests; public string clock; }
        [Serializable] class OptionsResp { public bool ok; public Options data; public string error; }
        [Serializable] class Beat { public string location, staging, subtitle; }
        [Serializable] class Reaction { public string variant_id; public Beat[] beats; }
        [Serializable] class ReportData { public string ending_code, result; public bool report_accepted, may_continue; public string[] missing_proof_axes; public Beat[] beats; public Reaction reaction; }
        [Serializable] class ReportResp { public bool ok; public ReportData data; public string error; }
        
        // draft survives scene hops inside one run (save/load is P2)
        static string draftNote = "", draftAccused = "";
        static readonly Dictionary<string, HashSet<string>> draftAxes = new Dictionary<string, HashSet<string>>();
        static readonly Dictionary<string, string> draftClaims = new Dictionary<string, string>();
        static bool reportSubmitted;
        static Vector2 keepScroll;   // scroll offset to restore after an in-place rebuild (report evidence picks, request list)

        /// <summary>Drop everything that belongs to the previous investigation (called when the server session changes / Play starts).</summary>
        public static void ResetDraft()
        {
            draftNote = ""; draftAccused = ""; draftAxes.Clear(); draftClaims.Clear(); reportSubmitted = false; keepScroll = Vector2.zero;
        }

        static readonly (string id, string title, string hint)[] Axes =
        {
            ("presence_or_timing", "1. 접근 및 시간", "누가 언제 그 자리에 있을 수 있었나"),
            ("motive", "2. 갈등과 동기", "무엇이 대면과 충돌로 이어졌나"),
            ("physical_link", "3. 치명상과 행위의 연결", "부상과 그 사람의 행동을 잇는 물증 (서로 다른 출처)"),
            ("exclude_alternative", "4. 다른 두 사람의 대안 검토", "나머지 두 사람이 치명상을 낼 수 없었던 근거"),
        };
        static readonly Dictionary<string, string> AxisKo = Axes.ToDictionary(a => a.id, a => a.title);

        VisualElement root, page; Label toast, clockLbl, budgetLbl;
        EvidenceCard[] evidence = new EvidenceCard[0]; Options opts; bool busy;

        // build after every OnEnable has run: the UIDocument may attach its panel after this component on scene load
        IEnumerator Start()
        {
            yield return null;
            root = GetComponent<UIDocument>().rootVisualElement; root.Clear(); root.style.flexGrow = 1;
            if (koreanFont) root.style.unityFontDefinition = FontDefinition.FromSDFFont(koreanFont);
            root.style.backgroundColor = Bg;
            page = new VisualElement(); Full(page); root.Add(page);
            toast = Toast(root);
            UnityEngine.Cursor.lockState = CursorLockMode.None; UnityEngine.Cursor.visible = true;
            StartCoroutine(Enter());
        }

        IEnumerator Enter()
        {
            float w = 0; while (TZServer.I == null || !TZServer.I.Online) { w += Time.unscaledDeltaTime; if (w > 20) break; yield return null; }
            bool synced = false; TZSession.Sync(() => synced = true); while (!synced) yield return null;   // adopt the server's session (drops a stale draft/submitted flag)
            yield return Post("/v1/scene", JsonUtility.ToJson(new SceneReq { scene = "desk" }), null);   // already at desk → idempotent
            yield return Refresh();
            Hub();
        }

        IEnumerator Post(string path, string body, Action<bool, string> done)
        {
            bool fin = false, ok = false; string text = "";
            if (TZServer.I == null) { done?.Invoke(false, "server offline"); yield break; }
            TZServer.I.Post(path, body ?? "{}", (o, t) => { ok = o; text = t; fin = true; });
            while (!fin) yield return null;
            done?.Invoke(ok, text);
        }

        IEnumerator Refresh()
        {
            yield return Post("/v1/evidence/list", "{}", (o, t) => { try { evidence = JsonUtility.FromJson<EvidenceResp>(t)?.data?.evidence ?? new EvidenceCard[0]; } catch { } });
            yield return Post("/v1/desk/options", "{}", (o, t) => { try { opts = JsonUtility.FromJson<OptionsResp>(t)?.data; } catch { } });
        }

        void Say(string m) { StopCoroutine(nameof(ToastCo)); StartCoroutine(ToastCo(m)); }
        IEnumerator ToastCo(string m) { toast.text = m; toast.style.display = DisplayStyle.Flex; yield return new WaitForSecondsRealtime(3.6f); toast.style.display = DisplayStyle.None; }

        VisualElement Shell(string crumb)
        {
            var s = new VisualElement(); Full(s); s.style.paddingLeft = 50; s.style.paddingRight = 50; s.style.paddingTop = 34;
            var top = new VisualElement(); top.style.flexDirection = FlexDirection.Row; top.style.alignItems = Align.Center;
            var brand = L("TABLE//ZERO", 22, Ink, true); brand.style.letterSpacing = 5; top.Add(brand);
            var c = L("CASE 001  ·  " + crumb, 13, Dim); c.style.marginLeft = 22; c.style.flexGrow = 1; top.Add(c);
            clockLbl = L("사건 시각 " + (opts?.clock ?? "--:--"), 15, Ink); clockLbl.style.marginRight = 26; top.Add(clockLbl);
            budgetLbl = L(opts != null ? $"수사 자원 {opts.budget_left}/{opts.budget_total}" : "", 15, Accent, true); top.Add(budgetLbl);
            s.Add(top); s.Add(Divider());
            return s;
        }

        void Show(VisualElement v) { page.Clear(); page.Add(v); }

        ScrollView curScroll;
        /// <summary>Remember/restore a ScrollView's offset across the rebuilds this screen does after every action.</summary>
        void KeepScroll(ScrollView sv)
        {
            curScroll = sv;
            var want = keepScroll;
            sv.RegisterCallback<GeometryChangedEvent>(_ => { if (want != Vector2.zero) { sv.scrollOffset = want; want = Vector2.zero; } });
            sv.verticalScroller.valueChanged += v => { keepScroll = new Vector2(0, v); };
        }

        // ------------------------------------------------------------------ hub
        void Hub()
        {
            var s = Shell("수사본부");
            var cols = new VisualElement(); cols.style.flexDirection = FlexDirection.Row; cols.style.flexGrow = 1; cols.style.marginBottom = 30;
            // left: confirmed case facts + evidence list
            var left = Box(Panel); left.style.width = Length.Percent(34); left.style.marginRight = 14;
            left.Add(L("확보한 기록", 20, Ink, true));
            var sv = new ScrollView(); sv.style.flexGrow = 1; sv.style.marginTop = 10;
            if (evidence.Length == 0) sv.Add(L("아직 확보한 기록이 없다. 현장 촬영·채취나 기록 요청으로만 남는다", 15, Dim));
            foreach (var e in evidence)
            {
                var card = new VisualElement(); card.style.backgroundColor = new Color(1, 1, 1, 0.04f); Pad(card, 12); Radius(card, 4); card.style.marginBottom = 8;
                card.Add(L(e.name, 16, Ink, true));
                if (!string.IsNullOrEmpty(e.detail)) { var d = L(e.detail, 14, Ink); d.style.marginTop = 4; card.Add(d); }
                var src = L("출처: " + e.source, 12, Dim); src.style.marginTop = 4; card.Add(src);
                var lim = L("한계: " + e.limitation, 12, Warn); card.Add(lim);
                sv.Add(card);
            }
            left.Add(sv); cols.Add(left);
            // center: what is confirmed / what is not
            var mid = Box(Panel); mid.style.flexGrow = 1; mid.style.marginRight = 14;
            mid.Add(L("확인된 사건의 순서", 20, Ink, true));
            void Line(string t, string d) { var r = new VisualElement(); r.style.borderLeftWidth = 2; r.style.borderLeftColor = Accent; r.style.paddingLeft = 12; r.style.marginTop = 12; r.Add(L(t, 15, Accent, true)); r.Add(L(d, 15, Ink)); mid.Add(r); }
            Line("10.15 22:07", "301호 거주자 112 신고 — 의식 없는 여성 발견");
            Line("이후", "119 응급처치 · 병원 이송 · 사망 확인");
            Line("10.16 00:10", "302호 현장 도착 (피해자 부재)");
            var gap = L("그 사이에 무슨 일이 있었는지는 기록과 진술로만 세울 수 있다. 확보한 기록의 시각은 왼쪽 카드에서 확인한다", 14, Dim); gap.style.marginTop = 18; mid.Add(gap);
            mid.Add(Divider());
            mid.Add(L("사건 수첩 (내 가설 · 비용 없음)", 16, Ink, true));
            var note = DarkInput(new TextField { multiline = true, value = draftNote }); note.style.height = 150; note.style.marginTop = 8; note.style.whiteSpace = WhiteSpace.Normal;
            note.RegisterValueChangedCallback(ev => draftNote = ev.newValue); mid.Add(note);
            cols.Add(mid);
            // right: actions
            var right = Box(Panel); right.style.width = 330;
            right.Add(L("수사 행동", 20, Ink, true));
            right.Add(Btn("용의자 호출 → 진술녹화실", () => SceneManager.LoadScene(InterrogationScene), primary: true));
            right.Add(Btn("기록 요청 · 감식 의뢰", () => { keepScroll = Vector2.zero; Requests(); }));
            right.Add(Btn("302호 현장 재방문", () => StartCoroutine(Revisit())));
            right.Add(Btn("최종 수사보고서", () => { keepScroll = Vector2.zero; Report(); }, enabled: !reportSubmitted, whyDisabled: "보고서는 이미 제출됐습니다"));
            right.Add(Divider());
            right.Add(L("현장 재방문은 이동·서류 처리로 사건 시각이 흐른다. 기록 요청은 수사 자원을 쓴다", 13, Dim));
            cols.Add(right);
            s.Add(cols);
            Show(s);
        }

        IEnumerator Revisit()
        {
            if (busy) yield break; busy = true;
            bool ok = false; string err = "";
            yield return Post("/v1/scene", JsonUtility.ToJson(new SceneReq { scene = "room302" }), (o, t) => { ok = o && t.Contains("\"ok\": true") || t.Contains("\"ok\":true"); err = t; });
            busy = false;
            if (!ok) { Say("지금은 현장으로 이동할 수 없습니다"); yield break; }
            TZCaseFlow.SkipBriefing = true;
            SceneManager.LoadScene(RoomScene);
        }

        // ------------------------------------------------------------------ requests
        void Requests()
        {
            var s = Shell("기록 요청 · 감식 의뢰");
            s.Add(L("확인되지 않은 사실은 요청과 감식으로만 검증한다", 26, Ink));
            var sub = L("각 요청은 수사 자원을 쓰고, 실제 회신까지 걸리는 시간이 있다. 대상·절차 요건이 안 되면 이유가 표시된다", 14, Dim); sub.style.marginBottom = 14; s.Add(sub);
            var sv = new ScrollView(); sv.style.flexGrow = 1; sv.style.marginBottom = 16; KeepScroll(sv);
            foreach (var r in opts?.requests ?? new ReqOpt[0])
            {
                bool afford = opts == null || r.cost <= opts.budget_left;
                var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.alignItems = Align.Center;
                row.style.backgroundColor = Panel; Pad(row, 12); Radius(row, 5); row.style.marginBottom = 8;
                var info = new VisualElement(); info.style.flexGrow = 1;
                info.Add(L(r.label, 17, Ink, true));
                var meta = L($"수사 자원 {r.cost}  ·  회신까지 약 {r.minutes}분 (사건 시각 기준)", 13, Dim); info.Add(meta);
                if (!string.IsNullOrEmpty(r.blocked_reason)) info.Add(L("요건 미충족: " + r.blocked_reason, 13, Warn));
                else if (!r.done && !afford) info.Add(L($"수사 자원이 부족합니다 (필요 {r.cost}, 남음 {opts.budget_left}). 확보한 기록만으로 보고서를 쓸 수 있습니다", 13, Warn));
                row.Add(info);
                var id = r.request_id; bool can = r.available && afford;
                Button b = r.done ? Btn("확보됨", null, enabled: false) : Btn(!afford && r.available ? "자원 부족" : "요청", () => { keepScroll = curScroll != null ? curScroll.scrollOffset : keepScroll; StartCoroutine(DoRequest(id)); }, primary: can, enabled: can, whyDisabled: r.blocked_reason ?? "수사 자원 부족");
                b.style.width = 120; row.Add(b);
                sv.Add(row);
            }
            s.Add(sv);
            var back = Btn("수사본부로", Hub); back.style.width = 160; back.style.marginBottom = 30; s.Add(back);
            Show(s);
        }

        IEnumerator DoRequest(string id)
        {
            if (busy) yield break; busy = true;
            string text = ""; yield return Post("/v1/desk/request", JsonUtility.ToJson(new ReqReq { request_id = id }), (o, t) => text = t);
            busy = false;
            bool ok = text.Contains("\"ok\": true") || text.Contains("\"ok\":true");
            yield return Refresh();
            Say(ok ? "요청한 기록이 회신됐습니다" : "요청할 수 없습니다: " + Err(text));
            Requests();
        }

        static string Err(string t) { try { var i = t.IndexOf("\"error\""); if (i < 0) return t; var s = t.Substring(i + 8).Trim(' ', ':', '"'); return s.Split('"')[0]; } catch { return t; } }

        // ------------------------------------------------------------------ final report (draft freely, submit once)
        void Report()
        {
            var s = Shell("최종 수사보고서 — 초안은 언제든 수정, 정식 제출은 1회");
            var sv = new ScrollView(); sv.style.flexGrow = 1; sv.style.marginBottom = 20; KeepScroll(sv);
            var who = Box(Panel); who.style.marginBottom = 12;
            who.Add(L("피의자 가설", 18, Ink, true));
            var choices = new[] { ("s1", "강도현"), ("s2", "이서연"), ("s3", "박현수"), ("", "지목 보류") };
            var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.marginTop = 8;
            foreach (var (id, nm) in choices)
            {
                var b = Btn((draftAccused == id ? "● " : "○ ") + nm, () => { keepScroll = new Vector2(0, sv.verticalScroller.value); draftAccused = id; Report(); }, primary: draftAccused == id);
                b.style.width = 150; b.style.marginRight = 10; row.Add(b);
            }
            who.Add(row); sv.Add(who);
            var hold = L("지목 보류도 유효한 선택이다. 보류하면 네 축의 주장과 근거 없이 제출할 수 있다", 13, Dim); hold.style.marginBottom = 10; sv.Add(hold);
            foreach (var (axis, title, hint) in Axes)
            {
                if (!draftAxes.ContainsKey(axis)) draftAxes[axis] = new HashSet<string>();
                var box = Box(Panel); box.style.marginBottom = 10;
                box.Add(L(title, 18, Ink, true)); box.Add(L(hint, 13, Dim));
                var claim = DarkInput(new TextField { multiline = true, value = draftClaims.TryGetValue(axis, out var c) ? c : "" }); claim.style.marginTop = 8;
                claim.style.minHeight = 74; claim.style.whiteSpace = WhiteSpace.Normal;
                claim.textEdition.placeholder = "주장: 이 축을 어떻게 설명하는가 (여러 줄 가능)"; var ax = axis;
                claim.RegisterValueChangedCallback(ev => draftClaims[ax] = ev.newValue); box.Add(claim);
                var picks = new VisualElement(); picks.style.flexDirection = FlexDirection.Row; picks.style.flexWrap = Wrap.Wrap; picks.style.marginTop = 8;
                if (evidence.Length == 0) picks.Add(L("근거로 붙일 확보 기록이 없다", 13, Warn));
                var summary = L("", 13, Dim); summary.style.marginTop = 6;
                void Refresh() { summary.text = draftAxes[ax].Count == 0 ? "붙인 근거 없음" : "붙인 근거 " + draftAxes[ax].Count + "건: " + string.Join(" · ", evidence.Where(x => draftAxes[ax].Contains(x.id)).Select(x => x.name)); }
                foreach (var e in evidence)
                {
                    var eid = e.id; var ename = e.name;
                    var t = Btn(ename, null); t.style.fontSize = 13; t.style.height = 34; t.style.marginRight = 8;
                    void Paint() { bool on = draftAxes[ax].Contains(eid); t.text = (on ? "✓ " : "") + ename; t.style.backgroundColor = on ? Accent : new Color(0.11f, 0.14f, 0.17f); t.style.color = on ? new Color(0.05f, 0.05f, 0.05f) : Ink; }
                    t.clicked += () => { if (!draftAxes[ax].Remove(eid)) draftAxes[ax].Add(eid); Paint(); Refresh(); };   // in place: no rebuild, so the scroll position and the text focus stay
                    Paint(); picks.Add(t);
                }
                box.Add(picks); Refresh(); box.Add(summary); sv.Add(box);
            }
            s.Add(sv);
            var bar = new VisualElement(); bar.style.flexDirection = FlexDirection.Row; bar.style.marginBottom = 26;
            var sub = Btn("검토하고 제출", () => { keepScroll = Vector2.zero; ConfirmSubmit(); }, primary: true); sub.style.width = 260; sub.style.marginRight = 12; bar.Add(sub);
            var back = Btn("초안 저장하고 수사본부로", Hub); back.style.width = 260; bar.Add(back);
            s.Add(bar);
            Show(s);
        }

        void ConfirmSubmit()
        {
            var s = Shell("정식 제출 확인");
            var who = string.IsNullOrEmpty(draftAccused) ? "지목 보류" : draftAccused == "s1" ? "강도현" : draftAccused == "s2" ? "이서연" : "박현수";
            var sv = new ScrollView(); sv.style.flexGrow = 1; sv.style.marginBottom = 12;
            var box = Box(Panel); box.style.maxWidth = 980;
            box.Add(L("정식 제출은 사건당 한 번뿐이다. 제출하면 수사는 이 보고서로 종결된다", 22, Ink, true));
            var d = L($"피의자 가설: {who}\n이름이 맞아도 네 축이 각각 자기 근거로 입증되지 않으면 성공으로 판정되지 않는다. 한 축에 붙인 근거는 다른 축에서 대신 쓰이지 않는다", 15, Ink); d.style.marginTop = 10; box.Add(d);
            var missing = new List<string>();
            if (!string.IsNullOrEmpty(draftAccused))
                foreach (var (axis, title, _) in Axes)
                {
                    var line = new VisualElement(); line.style.marginTop = 12; line.style.borderLeftWidth = 2; line.style.borderLeftColor = Accent; line.style.paddingLeft = 12;
                    line.Add(L(title, 15, Accent, true));
                    string cl = draftClaims.TryGetValue(axis, out var cc) ? cc.Trim() : "";
                    bool noClaim = cl.Length == 0, noEv = !draftAxes.ContainsKey(axis) || draftAxes[axis].Count == 0;
                    line.Add(L(noClaim ? "(주장 없음)" : cl, 14, noClaim ? Warn : Ink));
                    line.Add(L(noEv ? "(붙인 근거 없음)" : "근거: " + string.Join(" · ", evidence.Where(x => draftAxes[axis].Contains(x.id)).Select(x => x.name)), 13, noEv ? Warn : Dim));
                    if (noClaim || noEv) missing.Add(title);
                    box.Add(line);
                }
            if (missing.Count > 0) { var w = L("제출할 수 없습니다. 주장과 근거가 비어 있는 축: " + string.Join(", ", missing) + "  (지목을 보류하면 이 항목 없이 제출할 수 있다)", 14, Warn); w.style.marginTop = 14; box.Add(w); }
            sv.Add(box); s.Add(sv);
            var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.marginBottom = 26;
            var yes = Btn("제출한다", () => StartCoroutine(Submit()), primary: true, enabled: missing.Count == 0, whyDisabled: "비어 있는 축이 있습니다"); yes.style.width = 200; yes.style.marginRight = 12; row.Add(yes);
            var no = Btn("보고서로 돌아가기", Report); no.style.width = 220; row.Add(no);
            s.Add(row);
            Show(s);
        }

        static string Q(string v) => "\"" + (v ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "").Replace("\n", "\\n").Replace("\t", " ") + "\"";

        /// <summary>Report schema v1: per-axis claim + the evidence attached to THAT axis, bound to the server session. No union.</summary>
        static string ReportJson()
        {
            var sb = new System.Text.StringBuilder();
            sb.Append("{\"schema_version\":1,\"session_id\":").Append(Q(TZSession.Id)).Append(",\"accused_id\":");
            sb.Append(string.IsNullOrEmpty(draftAccused) ? "null" : Q(draftAccused)).Append(",\"confirm\":true,\"axes\":{");
            bool first = true;
            foreach (var (axis, _, _) in Axes)
            {
                if (!first) sb.Append(','); first = false;
                draftClaims.TryGetValue(axis, out var cl);
                var ids = draftAxes.TryGetValue(axis, out var set) ? set.OrderBy(x => x).ToArray() : new string[0];
                sb.Append(Q(axis)).Append(":{\"claim\":").Append(Q((cl ?? "").Trim())).Append(",\"evidence_ids\":[").Append(string.Join(",", ids.Select(Q))).Append("]}");
            }
            sb.Append("}}");
            return sb.ToString();
        }

        IEnumerator Submit()
        {
            if (busy) yield break; busy = true;
            bool synced = false; TZSession.Sync(() => synced = true); while (!synced) yield return null;   // a stale session id must never submit
            var body = ReportJson();
            string text = ""; yield return Post("/v1/report", body, (o, t) => text = t);
            busy = false;
            ReportResp r = null; try { r = JsonUtility.FromJson<ReportResp>(text); } catch { }
            if (r == null || !r.ok || r.data == null) { Say("제출하지 못했습니다 (수사 상태는 그대로): " + Err(text)); Report(); yield break; }
            reportSubmitted = true;
            Ending(r.data);
        }

        // ------------------------------------------------------------------ ending
        static readonly Dictionary<string, (string title, string body)> EndingText = new Dictionary<string, (string, string)>
        {
            {"SOLVED_PROVEN", ("입증된 수사 의견", "접근과 시간, 동기, 치명상과 행위의 연결, 다른 두 사람의 대안까지 서로 다른 근거로 세웠다. 이것은 법원의 판결이 아니라 형사의 수사 의견이다")},
            {"CORRECT_UNPROVEN", ("이름은 맞았지만 입증되지 않았다", "가리킨 사람은 맞았을지 모른다. 그러나 보고서는 그것을 증명하지 못했다. 사건은 다른 손으로 넘어간다")},
            {"WRONG_ACCUSATION", ("잘못된 지목", "지목된 사람에게는 그날 밤의 다른 잘못이 있었을 수 있다. 그러나 치명상은 그 사람의 것이 아니었다")},
            {"PROCEDURAL_HOLD", ("절차 문제로 보류", "확보 절차에 흠이 있는 기록이 보고서를 떠받치고 있었다. 사건은 재검증을 위해 보류된다")},
            {"UNRESOLVED", ("판단 보류", "확인되지 않은 것을 쓰지 않았다. 사건은 열린 채로 남는다")},
        };

        void Ending(ReportData d)
        {
            var s = new VisualElement(); Full(s); s.style.backgroundColor = Color.black; s.style.alignItems = Align.Center; s.style.justifyContent = Justify.Center;
            var col = new VisualElement(); col.style.maxWidth = 900;
            col.Add(L("CASE 001  ·  수사 종결", 13, Dim));
            var t = EndingText.TryGetValue(d.result ?? d.ending_code ?? "", out var e) ? e : ("수사 종결", "");
            var h = L(t.Item1, 40, Ink, true); h.style.marginTop = 12; col.Add(h);
            var b = L(t.Item2, 18, Ink); b.style.marginTop = 14; col.Add(b);
            if (d.missing_proof_axes != null && d.missing_proof_axes.Length > 0)
            {
                var m = L("입증되지 않은 축: " + string.Join(", ", d.missing_proof_axes.Select(a => AxisKo.TryGetValue(a, out var k) ? k : a)), 15, Warn);
                m.style.marginTop = 16; col.Add(m);
            }
            var beats = (d.beats ?? new Beat[0]).Concat(d.reaction?.beats ?? new Beat[0]).ToArray();
            if (beats.Length > 0)
            {
                col.Add(Divider());
                foreach (var bt in beats)
                {
                    var st = L(bt.staging, 14, Dim); st.style.marginTop = 10; col.Add(st);
                    if (!string.IsNullOrEmpty(bt.subtitle)) col.Add(L("“" + bt.subtitle + "”", 17, Ink));
                }
            }
            var menu = Btn("메인 메뉴로", () => SceneManager.LoadScene(MenuScene), primary: true); menu.style.width = 200; menu.style.marginTop = 30; col.Add(menu);
            s.Add(col); Show(s);
        }
    }
}
