using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>
    /// 조사 대상 호출 — the detective stands at the observation monitor of the 진술녹화실 wing. The full screen is the live
    /// waiting-room feed of the selected person (user-approved original shot); on the desk lies the paper call ledger.
    /// Only what a detective legitimately holds is shown: name, age, occupation, relation, what the person told
    /// officers at the scene (canon starting claims), interview history and whether they can be called now.
    /// No private facts, no truth flags, no hints. Interview chrome stays hidden until the detective walks in.
    /// </summary>
    public sealed partial class TZInterrogationScreen
    {
        [Serializable] class PublicState { public string scene, clock, active_interview; public Person[] known_people; }
        [Serializable] class Person { public string id, name; }
        [Serializable] class PublicStateResp { public string mode; public PublicState state; }

        static readonly Color PaperInk = new Color(0.13f, 0.12f, 0.11f), PaperDim = new Color(0.36f, 0.33f, 0.30f),
                              PaperRule = new Color(0.25f, 0.22f, 0.18f, 0.35f), StampRed = new Color(0.66f, 0.10f, 0.10f, 0.85f),
                              Marker = new Color(1f, 0.86f, 0.36f, 0.42f), OkInk = new Color(0.12f, 0.36f, 0.20f);

        VisualElement ledgerLayer, paperEl, paperShadow, rowsBox, dossier, feedLabel, callCta, ctaBar, blackout, doorL, doorR, deskShade;
        Label feedRoom, feedTime, feedState, recDot, ctaTitle, ctaSub, entryCaption, entrySub;
        readonly List<VisualElement> rows = new List<VisualElement>();
        readonly Dictionary<string, int> interviews = new Dictionary<string, int>();
        int sel;
        bool ledgerOpen, entering;
        string activeOnServer;
        string clockText = "";

        // ------------------------------------------------------------------ build
        void BuildCallScreen()
        {
            if (suspects == null || suspects.Length == 0) return;
            ledgerLayer = new VisualElement(); Abs(ledgerLayer, 0, 0, 0, 0); ledgerLayer.pickingMode = PickingMode.Ignore;

            // darken the desk side of the monitor so the paper reads; the person stays fully visible on the right
            deskShade = new VisualElement(); Abs(deskShade, 0, float.NaN, 0, 0); deskShade.style.width = Length.Percent(62);
            deskShade.style.backgroundImage = Ramp(); deskShade.style.backgroundSize = new BackgroundSize(Length.Percent(100), Length.Percent(100));
            deskShade.pickingMode = PickingMode.Ignore; ledgerLayer.Add(deskShade);

            BuildFeedOverlay();
            BuildPaper();
            BuildCta();

            root.Add(ledgerLayer);

            // transition layers above everything
            blackout = new VisualElement(); Abs(blackout, 0, 0, 0, 0); blackout.style.backgroundColor = Color.black; blackout.style.opacity = 0; blackout.pickingMode = PickingMode.Ignore;
            entryCaption = L("", 34, Ink); entrySub = L("", 17, Dim);
            var cap = new VisualElement(); Abs(cap, 0, 0, 0, 0); cap.style.alignItems = Align.Center; cap.style.justifyContent = Justify.Center; cap.pickingMode = PickingMode.Ignore;
            if (serifFont) entryCaption.style.unityFontDefinition = FontDefinition.FromSDFFont(serifFont);
            entryCaption.style.letterSpacing = 6; entrySub.style.marginTop = 10; entrySub.style.letterSpacing = 2;
            cap.Add(entryCaption); cap.Add(entrySub); blackout.Add(cap);
            doorL = Door(true); doorR = Door(false);
            root.Add(doorL); root.Add(doorR); root.Add(blackout);

            Select(1, true);   // 이서연: the person in the approved reference
            ledgerOpen = true;
            StartCoroutine(RefreshLedgerFromServer());
            StartCoroutine(FadeIn(ledgerLayer, 0.6f));
        }

        void BuildFeedOverlay()
        {
            feedLabel = new VisualElement(); Abs(feedLabel, 42, 54, float.NaN, float.NaN); feedLabel.style.alignItems = Align.FlexEnd; feedLabel.pickingMode = PickingMode.Ignore;
            var top = new VisualElement(); top.style.flexDirection = FlexDirection.Row; top.style.alignItems = Align.Center;
            recDot = L("●", 15, new Color(0.95f, 0.22f, 0.22f)); recDot.style.marginRight = 8; top.Add(recDot);
            feedRoom = L("", 17, new Color(1, 1, 1, 0.88f)); feedRoom.style.letterSpacing = 3; top.Add(feedRoom);
            feedLabel.Add(top);
            feedTime = L("", 15, new Color(1, 1, 1, 0.62f)); feedTime.style.letterSpacing = 2; feedTime.style.marginTop = 4; feedLabel.Add(feedTime);
            feedState = L("", 15, new Color(1, 1, 1, 0.62f)); feedState.style.marginTop = 2; feedLabel.Add(feedState);
            ledgerLayer.Add(feedLabel);
        }

        void BuildPaper()
        {
            paperShadow = new VisualElement(); Abs(paperShadow, 46, float.NaN, float.NaN, 104);
            paperShadow.style.width = 664; paperShadow.style.height = 968; paperShadow.style.backgroundColor = new Color(0, 0, 0, 0.55f);
            paperShadow.style.rotate = new Rotate(-1.4f); Radius(paperShadow, 6); paperShadow.pickingMode = PickingMode.Ignore;
            ledgerLayer.Add(paperShadow);

            paperEl = new VisualElement(); Abs(paperEl, 32, float.NaN, float.NaN, 92);
            paperEl.style.width = 664; paperEl.style.height = 968; paperEl.style.rotate = new Rotate(-0.8f);
            if (paper) paperEl.style.backgroundImage = paper; else paperEl.style.backgroundColor = new Color(0.89f, 0.86f, 0.81f);
            paperEl.style.backgroundSize = new BackgroundSize(Length.Percent(100), Length.Percent(100));
            paperEl.style.paddingLeft = 56; paperEl.style.paddingRight = 52; paperEl.style.paddingTop = 46;
            paperEl.pickingMode = PickingMode.Position;
            ledgerLayer.Add(paperEl);

            var head = new VisualElement(); head.style.flexDirection = FlexDirection.Row; head.style.justifyContent = Justify.SpaceBetween; head.style.alignItems = Align.FlexStart;
            var org = new VisualElement();
            org.Add(P("○○경찰서 형사과 강력1팀", 17, PaperInk));
            var cs = P("CASE 001 · 빌라 302호 정수연(29) 사망 사건", 17, new Color(0.25f, 0.22f, 0.19f)); cs.style.marginTop = 2; org.Add(cs);
            head.Add(org);
            var stamp = new VisualElement(); stamp.style.width = 92; stamp.style.height = 92; Radius(stamp, 46);
            stamp.style.borderTopWidth = stamp.style.borderBottomWidth = stamp.style.borderLeftWidth = stamp.style.borderRightWidth = 3;
            stamp.style.borderTopColor = stamp.style.borderBottomColor = stamp.style.borderLeftColor = stamp.style.borderRightColor = StampRed;
            stamp.style.alignItems = Align.Center; stamp.style.justifyContent = Justify.Center; stamp.style.rotate = new Rotate(-14f); stamp.style.marginTop = -6;
            var st = P("수사중", 21, StampRed); st.style.unityFontStyleAndWeight = FontStyle.Bold; stamp.Add(st);
            head.Add(stamp);
            paperEl.Add(head);

            var title = P("조사 대상 호출 대장", 36, PaperInk); title.style.unityFontStyleAndWeight = FontStyle.Bold; title.style.marginTop = 6; title.style.letterSpacing = 2;
            paperEl.Add(title);
            paperEl.Add(Rule(10, 2));

            var hdr = Row4("연번", "성명", "관계", "현재 상태", 16, new Color(0.25f, 0.22f, 0.19f)); hdr.style.marginBottom = 4; paperEl.Add(hdr);
            paperEl.Add(Rule(0, 1));
            rowsBox = new VisualElement(); paperEl.Add(rowsBox);
            for (int i = 0; i < suspects.Length; i++)
            {
                int idx = i; var s = suspects[i];
                var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.alignItems = Align.Center; r.style.height = 62;
                r.style.borderBottomWidth = 1; r.style.borderBottomColor = PaperRule; r.style.paddingLeft = 10;
                var n = P($"0{i + 1}", 18, PaperDim); n.style.width = 56; r.Add(n);
                var nameBox = new VisualElement(); nameBox.style.width = 170; nameBox.style.flexDirection = FlexDirection.Row; nameBox.style.alignItems = Align.FlexEnd;
                var nm = P(s.name, 26, PaperInk); nm.style.unityFontStyleAndWeight = FontStyle.Bold; nameBox.Add(nm);
                var ag = P($" {s.age}", 17, PaperDim); ag.style.marginLeft = 4; ag.style.marginBottom = 3; nameBox.Add(ag);
                r.Add(nameBox);
                var rel = P(ShortRelation(s.relation), 18, PaperInk); rel.style.width = 150; r.Add(rel);
                var state = P("", 17, OkInk); state.name = "state"; state.style.flexGrow = 1; r.Add(state);
                var mark = new VisualElement(); mark.name = "mark"; Abs(mark, 10, float.NaN, 10, -4); mark.style.width = 4; mark.style.backgroundColor = StampRed; mark.style.opacity = 0;
                r.Add(mark);
                r.RegisterCallback<PointerEnterEvent>(_ => Hover(idx, true));
                r.RegisterCallback<PointerLeaveEvent>(_ => Hover(idx, false));
                r.RegisterCallback<PointerDownEvent>(_ => Select(idx));
                rowsBox.Add(r); rows.Add(r);
            }
            dossier = new VisualElement(); dossier.style.marginTop = 14; paperEl.Add(dossier);
            NoShrink(paperEl);
        }

        void BuildCta()
        {
            callCta = new VisualElement(); Abs(callCta, float.NaN, 60, 62, float.NaN); callCta.style.alignItems = Align.FlexEnd;
            callCta.pickingMode = PickingMode.Position;
            ctaSub = L("", 16, new Color(1, 1, 1, 0.66f)); ctaSub.style.marginBottom = 6; callCta.Add(ctaSub);
            var line = new VisualElement(); line.style.flexDirection = FlexDirection.Row; line.style.alignItems = Align.Center;
            ctaTitle = L("", 34, Ink); if (serifFont) ctaTitle.style.unityFontDefinition = FontDefinition.FromSDFFont(serifFont);
            ctaTitle.style.letterSpacing = 2; line.Add(ctaTitle);
            var key = L("Enter", 14, new Color(1, 1, 1, 0.75f)); key.style.marginLeft = 18; Pad(key, 6); key.style.paddingLeft = key.style.paddingRight = 10;
            key.style.borderTopWidth = key.style.borderBottomWidth = key.style.borderLeftWidth = key.style.borderRightWidth = 1;
            key.style.borderTopColor = key.style.borderBottomColor = key.style.borderLeftColor = key.style.borderRightColor = new Color(1, 1, 1, 0.4f); Radius(key, 4);
            line.Add(key); callCta.Add(line);
            ctaBar = new VisualElement(); ctaBar.style.height = 2; ctaBar.style.marginTop = 10; ctaBar.style.backgroundColor = Red; ctaBar.style.width = Length.Percent(28); ctaBar.style.alignSelf = Align.FlexEnd;
            callCta.Add(ctaBar);
            callCta.RegisterCallback<PointerEnterEvent>(_ => { ctaBar.style.width = Length.Percent(100); ctaTitle.style.color = Color.white; });
            callCta.RegisterCallback<PointerLeaveEvent>(_ => { ctaBar.style.width = Length.Percent(28); ctaTitle.style.color = Ink; });
            callCta.RegisterCallback<PointerDownEvent>(_ => CallSelected());
            ledgerLayer.Add(callCta);
        }

        VisualElement Door(bool left)
        {
            var d = new VisualElement(); Abs(d, 0, float.NaN, 0, float.NaN); d.style.width = Length.Percent(51);
            if (left) d.style.left = 0; else d.style.right = 0;
            d.style.backgroundColor = new Color(0.035f, 0.035f, 0.04f); d.pickingMode = PickingMode.Ignore; d.style.display = DisplayStyle.None;
            var edge = new VisualElement(); Abs(edge, 0, float.NaN, 0, float.NaN); edge.style.width = 3; edge.style.backgroundColor = new Color(1f, 0.8f, 0.6f, 0.35f);
            if (left) edge.style.right = 0; else edge.style.left = 0;
            d.Add(edge);
            return d;
        }

        // ------------------------------------------------------------------ state
        void Select(int i, bool instant = false)
        {
            if (suspects == null || i < 0 || i >= suspects.Length) return;
            sel = i; var s = suspects[i];
            for (int k = 0; k < rows.Count; k++)
            {
                bool on = k == i;
                rows[k].style.backgroundColor = on ? Marker : new Color(0, 0, 0, 0);
                rows[k].Q("mark").style.opacity = on ? 1 : 0;
            }
            if (!instant) StartCoroutine(SwapFeed(s)); else { bg.style.backgroundImage = s.feed ? s.feed : s.background; bgZoom = 1.0f; }
            feedRoom.text = $"{s.room} · CAM 0{i + 1}";
            RenderDossier(s);
            RenderCta(s);
        }

        void Hover(int i, bool on)
        {
            if (i == sel) return;
            rows[i].style.backgroundColor = on ? new Color(0, 0, 0, 0.05f) : new Color(0, 0, 0, 0);
        }

        IEnumerator SwapFeed(Suspect s)
        {
            float t = 0; var tex = s.feed ? s.feed : s.background;
            while (t < 0.18f) { t += Time.unscaledDeltaTime; blackout.style.opacity = t / 0.18f * 0.55f; yield return null; }
            bg.style.backgroundImage = tex; bgZoom = 1.03f;
            t = 0;
            while (t < 0.45f) { t += Time.unscaledDeltaTime; float k = Mathf.SmoothStep(0, 1, t / 0.45f); blackout.style.opacity = 0.55f * (1 - k); bgZoom = Mathf.Lerp(1.03f, 1f, k); yield return null; }
            blackout.style.opacity = 0;
        }

        void RenderDossier(Suspect s)
        {
            dossier.Clear();
            dossier.Add(Section("인적 사항"));
            dossier.Add(KV("직업", s.job));
            dossier.Add(Section("현장 탐문 시 진술 (요지)"));
            if (s.statements != null)
                foreach (var line in s.statements)
                {
                    var q = P("“" + line + "”", 19, PaperInk); q.style.whiteSpace = WhiteSpace.Normal; q.style.marginBottom = 4; q.style.marginLeft = 4;
                    dossier.Add(q);
                }
            dossier.Add(Section("조사 이력"));
            int n = interviews.TryGetValue(s.id, out var c) ? c : 0;
            dossier.Add(P(n == 0 ? "진술녹화실 조사 기록 없음" : $"진술녹화실 조사 {n}회 (이번 수사)", 18, PaperInk));
            dossier.Add(Section("호출"));
            bool busyElse = !string.IsNullOrEmpty(activeOnServer) && activeOnServer != s.id;
            var st = P(busyElse ? "다른 대상 조사 중 — 종료 후 호출 가능" : $"호출 가능 · {s.room} 대기", 18, busyElse ? StampRed : OkInk);
            dossier.Add(st);
            NoShrink(dossier);
            var cost = P(interviews.Count > 0 ? "호출 시 사건 시간 10분 경과 · 추가 면담은 데스크 요청 예산 1 소모" : "호출 시 사건 시간 10분 경과", 15, PaperDim);
            cost.style.marginTop = 4; cost.style.flexShrink = 0; dossier.Add(cost);
        }

        void RenderCta(Suspect s)
        {
            ctaTitle.text = $"{s.name} — {s.room}로 호출";
            ctaSub.text = (TZServer.I != null && TZServer.I.Online) ? "↑ ↓ 대상 선택   ·   조사관 입실과 동시에 영상 녹화 시작" : "로컬 수사 서버 연결 중…";
        }

        void RefreshRowStates()
        {
            for (int i = 0; i < suspects.Length && i < rows.Count; i++)
            {
                var s = suspects[i]; var l = rows[i].Q<Label>("state");
                int n = interviews.TryGetValue(s.id, out var c) ? c : 0;
                bool busyElse = !string.IsNullOrEmpty(activeOnServer) && activeOnServer != s.id;
                l.text = busyElse ? "대기 (조사 중 아님)" : n == 0 ? $"대기 · {RoomShort(s.room)}" : $"조사 {n}회 · 대기";
                l.style.color = n == 0 ? OkInk : PaperInk;
            }
        }

        IEnumerator RefreshLedgerFromServer()
        {
            while (TZServer.I == null || !TZServer.I.Online) { if (suspects != null) RenderCta(suspects[sel]); yield return new WaitForSecondsRealtime(0.5f); }
            yield return Call("GET", "/v1/state", null, (ok, t) =>
            {
                var r = JsonUtility.FromJson<PublicStateResp>(t);
                if (r?.state == null) return;
                activeOnServer = r.state.active_interview;
                clockText = r.state.clock ?? clockText;
                if (r.state.known_people != null) foreach (var p in r.state.known_people) if (!interviews.ContainsKey(p.id)) interviews[p.id] = 1;
            });
            RefreshRowStates(); RenderDossier(suspects[sel]); RenderCta(suspects[sel]);
        }

        void CallScreenUpdate()
        {
            if (recDot != null) recDot.style.opacity = (Time.unscaledTime % 1.4f) < 0.9f ? 1 : 0.15f;
            if (feedTime != null) feedTime.text = "2024. 03. 16 (토)  " + (string.IsNullOrEmpty(clockText) ? "--:--" : clockText) + ":" + ((int)(Time.unscaledTime % 60)).ToString("00");
            if (feedState != null && suspects != null) feedState.text = "대기실 실시간 영상 · 음성 없음";
            if (!ledgerOpen || entering || Keyboard.current == null) return;
            if (Keyboard.current.upArrowKey.wasPressedThisFrame) Select((sel + suspects.Length - 1) % suspects.Length);
            if (Keyboard.current.downArrowKey.wasPressedThisFrame) Select((sel + 1) % suspects.Length);
            if (Keyboard.current.enterKey.wasPressedThisFrame || Keyboard.current.numpadEnterKey.wasPressedThisFrame) CallSelected();
        }

        void CallSelected()
        {
            if (!ledgerOpen || entering || busy) return;
            var s = suspects[sel];
            if (!string.IsNullOrEmpty(activeOnServer) && activeOnServer != s.id) { Toast("다른 대상의 조사가 진행 중입니다"); return; }
            if (TZServer.I == null || !TZServer.I.Online) { Toast("로컬 수사 서버에 연결 중입니다"); return; }
            Begin(s);
        }

        // ------------------------------------------------------------------ transitions
        void SetChrome(bool show, bool instant)
        {
            foreach (var e in new[] { topBar, leftCol, rightCol, dock })
            {
                if (e == null) continue;
                if (instant) { e.style.display = show ? DisplayStyle.Flex : DisplayStyle.None; e.style.opacity = show ? 1 : 0; }
                else if (show) StartCoroutine(FadeIn(e, 0.5f)); else e.style.display = DisplayStyle.None;
            }
            if (!show && subtitleBox != null) subtitleBox.style.opacity = 0;
        }

        /// <summary>Walk-in: ledger leaves, black with the room caption, the door opens and the camera steps in.</summary>
        IEnumerator EnterRoom(Suspect s)
        {
            entering = true; ledgerOpen = false;
            float t = 0;
            while (t < 0.35f) { t += Time.unscaledDeltaTime; float k = t / 0.35f; ledgerLayer.style.opacity = 1 - k; ledgerLayer.style.translate = new Translate(-60 * k, 0); blackout.style.opacity = k; yield return null; }
            ledgerLayer.style.display = DisplayStyle.None;
            entryCaption.text = s.room; entrySub.text = $"{s.name} ({s.age}) · {(string.IsNullOrEmpty(clockText) ? "" : clockText + " ")}입실";
            t = 0; while (t < 1.0f) { t += Time.unscaledDeltaTime; yield return null; }
            entryCaption.text = ""; entrySub.text = "";
            bg.style.backgroundImage = s.feed ? s.feed : s.background;
            bgZoom = 1.42f; bgShiftY = 60f;
            doorL.style.display = doorR.style.display = DisplayStyle.Flex;
            doorL.style.translate = doorR.style.translate = new Translate(0, 0);
            t = 0;
            const float D = 2.6f;
            while (t < D)
            {
                t += Time.unscaledDeltaTime; float k = Mathf.Clamp01(t / D);
                blackout.style.opacity = Mathf.Clamp01(1 - t / 0.4f);
                float open = Mathf.SmoothStep(0, 1, Mathf.Clamp01((t - 0.15f) / 1.1f));
                doorL.style.translate = new Translate(Length.Percent(-100 * open), 0);
                doorR.style.translate = new Translate(Length.Percent(100 * open), 0);
                float walk = Mathf.SmoothStep(0, 1, k);
                bgZoom = Mathf.Lerp(1.42f, 1f, walk);
                bgShiftY = Mathf.Lerp(60f, 0f, walk) + Mathf.Sin(k * Mathf.PI * 4f) * 7f * (1 - walk);   // footsteps
                yield return null;
            }
            doorL.style.display = doorR.style.display = DisplayStyle.None; blackout.style.opacity = 0; bgZoom = 1f; bgShiftY = 0;
            interviews[s.id] = (interviews.TryGetValue(s.id, out var c) ? c : 0) + 1;
            activeOnServer = s.id;
            entering = false;
        }

        void OnInterviewEnded(Suspect ended)
        {
            activeOnServer = null;
            if (ledgerLayer == null) { if (legacyPicker) ShowPicker(true); return; }
            ledgerLayer.style.display = DisplayStyle.Flex; ledgerLayer.style.translate = new Translate(0, 0);
            ledgerOpen = true;
            RefreshRowStates(); Select(sel, true);
            StartCoroutine(FadeIn(ledgerLayer, 0.5f));
        }

        IEnumerator FadeIn(VisualElement e, float d)
        {
            e.style.display = DisplayStyle.Flex; float t = 0;
            while (t < d) { t += Time.unscaledDeltaTime; e.style.opacity = Mathf.SmoothStep(0, 1, t / d); yield return null; }
            e.style.opacity = 1;
        }

        // ------------------------------------------------------------------ paper typography
        // serif only for display sizes (title, names, stamp); body text uses the sans atlas, which stays crisp at 15–19 px
        Label P(string t, int size, Color c)
        {
            var l = L(t, size, c);
            if (serifFont && size >= 21) l.style.unityFontDefinition = FontDefinition.FromSDFFont(serifFont);
            return l;
        }
        VisualElement Rule(float top, float h)
        {
            var r = new VisualElement(); r.style.height = h; r.style.marginTop = top; r.style.marginBottom = 8; r.style.backgroundColor = PaperRule; return r;
        }
        VisualElement Row4(string a, string b, string c, string d, int size, Color col)
        {
            var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.paddingLeft = 10;
            var la = P(a, size, col); la.style.width = 56; r.Add(la);
            var lb = P(b, size, col); lb.style.width = 170; r.Add(lb);
            var lc = P(c, size, col); lc.style.width = 150; r.Add(lc);
            r.Add(P(d, size, col));
            return r;
        }
        Label Section(string t)
        {
            var l = P(t, 15, new Color(0.25f, 0.22f, 0.19f)); l.style.marginTop = 12; l.style.marginBottom = 4; l.style.letterSpacing = 2; l.style.unityFontStyleAndWeight = FontStyle.Bold;
            return l;
        }
        VisualElement KV(string k, string v)
        {
            var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.marginBottom = 4;
            var a = P(k, 18, PaperDim); a.style.width = 64; r.Add(a);
            var b = P(v, 18, PaperInk); b.style.whiteSpace = WhiteSpace.Normal; b.style.flexShrink = 1; r.Add(b);
            return r;
        }
        static void NoShrink(VisualElement e) { e.style.flexShrink = 0; foreach (var ch in e.Children()) NoShrink(ch); }
        static string ShortRelation(string rel) => rel.Replace("피해자의 ", "").Replace("피해자", "");
        static string RoomShort(string room) => string.IsNullOrEmpty(room) ? "대기실" : room.Replace("진술녹화실", "녹화실");

        static Texture2D rampTex;
        static Texture2D Ramp()
        {
            if (rampTex) return rampTex;
            rampTex = new Texture2D(256, 1, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int x = 0; x < 256; x++) { float u = x / 255f; rampTex.SetPixel(x, 0, new Color(0, 0, 0, Mathf.Lerp(0.88f, 0f, Mathf.SmoothStep(0.15f, 1f, u)))); }
            rampTex.Apply();
            return rampTex;
        }
    }
}
