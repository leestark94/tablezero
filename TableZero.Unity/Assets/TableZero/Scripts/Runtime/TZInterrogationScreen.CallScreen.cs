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
    /// 조사 대상 호출 — the detective stands at the observation monitor of the 진술녹화실 wing. Right: live waiting-room
    /// feed of the selected person (user-approved original). Left: the paper call ledger lying flat on the desk (no
    /// rotation, so text is sampled 1:1 and stays crisp). Only what a detective legitimately holds is shown: name, age,
    /// occupation, relation, what the person told officers at the scene (canon starting claims), this session's
    /// interview record and whether the person can be called now. No private facts, no truth flags, no hints.
    /// Interview chrome stays hidden until the detective is seated.
    /// </summary>
    public sealed partial class TZInterrogationScreen
    {
        [Serializable] class PublicState { public string scene, clock, active_interview; public bool case_closed; public Person[] known_people; }
        [Serializable] class Person { public string id, name; }
        [Serializable] class PublicStateResp { public string mode; public PublicState state; }

        static readonly Color PaperInk = new Color(0.10f, 0.095f, 0.09f), PaperMid = new Color(0.27f, 0.25f, 0.22f),
                              PaperRule = new Color(0.22f, 0.19f, 0.16f, 0.30f), StampRed = new Color(0.62f, 0.09f, 0.09f, 0.9f),
                              Marker = new Color(1f, 0.87f, 0.40f, 0.40f), OkInk = new Color(0.10f, 0.33f, 0.18f);

        bool in3D;
        VisualElement ledgerLayer, paperEl, paperShadow, rowsBox, dossier, feedLabel, callCta, ctaBar, blackout, bgB, deskShade, recBadge;
        ScrollView dossierScroll;
        Label feedRoom, feedTime, recDot, ctaTitle, ctaSub, entryCaption, entrySub, recLabel;
        readonly List<VisualElement> rows = new List<VisualElement>();
        readonly Dictionary<string, int> interviews = new Dictionary<string, int>();
        readonly Dictionary<string, List<string>> records = new Dictionary<string, List<string>>();
        readonly Dictionary<string, string> calledAt = new Dictionary<string, string>();
        int sel;
        bool ledgerOpen, entering, recordOpen, caseClosed;
        string activeOnServer;
        string clockText = "";
        AudioSource sfx, room;
        Coroutine swapCo;

        // ------------------------------------------------------------------ build
        void BuildCallScreen()
        {
            if (suspects == null || suspects.Length == 0) return;
            SetupAudio();
            bgB = new VisualElement(); Abs(bgB, 0, 0, 0, 0); bgB.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Cover);
            bgB.style.opacity = 0; bgB.pickingMode = PickingMode.Ignore; bg.parent.Insert(bg.parent.IndexOf(bg) + 1, bgB);

            ledgerLayer = new VisualElement(); Abs(ledgerLayer, 0, 0, 0, 0); ledgerLayer.pickingMode = PickingMode.Ignore;
            deskShade = new VisualElement(); Abs(deskShade, 0, float.NaN, 0, 0); deskShade.style.width = Length.Percent(46);
            deskShade.style.backgroundImage = Ramp(); deskShade.style.backgroundSize = new BackgroundSize(Length.Percent(100), Length.Percent(100));
            deskShade.pickingMode = PickingMode.Ignore; ledgerLayer.Add(deskShade);

            BuildFeedOverlay();
            BuildPaper();
            BuildCta();
            root.Add(ledgerLayer);

            blackout = new VisualElement(); Abs(blackout, 0, 0, 0, 0); blackout.style.backgroundColor = Color.black; blackout.style.opacity = 0; blackout.pickingMode = PickingMode.Ignore;
            var cap = new VisualElement(); Abs(cap, 0, 0, 0, 0); cap.style.alignItems = Align.Center; cap.style.justifyContent = Justify.Center; cap.pickingMode = PickingMode.Ignore;
            entryCaption = L("", 34, Ink); entrySub = L("", 18, Dim);
            if (serifFont) entryCaption.style.unityFontDefinition = FontDefinition.FromSDFFont(serifFont);
            entryCaption.style.letterSpacing = 6; entrySub.style.marginTop = 10; entrySub.style.letterSpacing = 1;
            cap.Add(entryCaption); cap.Add(entrySub); blackout.Add(cap);
            root.Add(blackout);

            recBadge = new VisualElement(); Abs(recBadge, 84, float.NaN, float.NaN, float.NaN); recBadge.style.left = Length.Percent(50); recBadge.style.marginLeft = -90;
            recBadge.style.flexDirection = FlexDirection.Row; recBadge.style.alignItems = Align.Center; recBadge.style.opacity = 0; recBadge.pickingMode = PickingMode.Ignore;
            var rd = L("●", 14, new Color(0.95f, 0.25f, 0.25f)); rd.style.marginRight = 8; recBadge.Add(rd);
            recLabel = L("영상 녹화 중", 15, new Color(1, 1, 1, 0.8f)); recBadge.Add(recLabel);
            root.Add(recBadge);

            sel = -1; Select(1, true);   // 이서연: the person in the approved reference
            ledgerOpen = true;
            StartCoroutine(RefreshLedgerFromServer());
            StartCoroutine(FadeIn(ledgerLayer, 0.6f));
        }

        void SetupAudio()
        {
            room = gameObject.AddComponent<AudioSource>(); room.clip = TZProcAudio.RoomTone(); room.loop = true; room.volume = 0.22f; room.playOnAwake = false; room.spatialBlend = 0; room.Play();
            sfx = gameObject.AddComponent<AudioSource>(); sfx.playOnAwake = false; sfx.spatialBlend = 0;
        }

        void BuildFeedOverlay()
        {
            feedLabel = new VisualElement(); Abs(feedLabel, 40, 52, float.NaN, float.NaN); feedLabel.style.alignItems = Align.FlexEnd; feedLabel.pickingMode = PickingMode.Ignore;
            var top = new VisualElement(); top.style.flexDirection = FlexDirection.Row; top.style.alignItems = Align.Center;
            recDot = L("●", 15, new Color(0.95f, 0.22f, 0.22f)); recDot.style.marginRight = 8; top.Add(recDot);
            feedRoom = L("", 18, new Color(1, 1, 1, 0.9f)); feedRoom.style.letterSpacing = 2; top.Add(feedRoom);
            feedLabel.Add(top);
            feedTime = L("", 16, new Color(1, 1, 1, 0.70f)); feedTime.style.letterSpacing = 1; feedTime.style.marginTop = 4; feedLabel.Add(feedTime);
            var fs = L("대기실 실시간 영상 · 음성 없음", 16, new Color(1, 1, 1, 0.62f)); fs.style.marginTop = 2; feedLabel.Add(fs);
            ledgerLayer.Add(feedLabel);
        }

        void BuildPaper()
        {
            paperShadow = new VisualElement(); Abs(paperShadow, 44, float.NaN, float.NaN, 98);
            paperShadow.style.width = 676; paperShadow.style.height = 1000; paperShadow.style.backgroundColor = new Color(0, 0, 0, 0.5f);
            Radius(paperShadow, 4); paperShadow.pickingMode = PickingMode.Ignore; ledgerLayer.Add(paperShadow);

            paperEl = new VisualElement(); Abs(paperEl, 36, float.NaN, float.NaN, 88);
            paperEl.style.width = 676; paperEl.style.height = 1000;
            if (paper) paperEl.style.backgroundImage = paper; else paperEl.style.backgroundColor = new Color(0.89f, 0.86f, 0.81f);
            paperEl.style.backgroundSize = new BackgroundSize(Length.Percent(100), Length.Percent(100));
            paperEl.style.paddingLeft = 54; paperEl.style.paddingRight = 50; paperEl.style.paddingTop = 42; paperEl.style.paddingBottom = 30;
            paperEl.pickingMode = PickingMode.Position;
            ledgerLayer.Add(paperEl);

            var head = new VisualElement(); head.style.flexDirection = FlexDirection.Row; head.style.justifyContent = Justify.SpaceBetween; head.style.alignItems = Align.FlexStart;
            var org = new VisualElement();
            org.Add(P("○○경찰서 형사과 강력1팀", 17, PaperMid));
            var cs = P("CASE 001 · 빌라 302호 여성 사망 경위 조사", 17, PaperMid); cs.style.marginTop = 3; org.Add(cs);
            head.Add(org);
            var stamp = new VisualElement(); stamp.style.width = 90; stamp.style.height = 90; Radius(stamp, 45);
            Border(stamp, 3, StampRed); stamp.style.alignItems = Align.Center; stamp.style.justifyContent = Justify.Center; stamp.style.rotate = new Rotate(-12f); stamp.style.marginTop = -8;
            var st = P("수사중", 22, StampRed); st.style.unityFontStyleAndWeight = FontStyle.Bold; stamp.Add(st);
            head.Add(stamp);
            paperEl.Add(head);

            var title = P("조사 대상 호출 대장", 38, PaperInk); title.style.unityFontStyleAndWeight = FontStyle.Bold; title.style.marginTop = 4; title.style.letterSpacing = 2;
            paperEl.Add(title);
            paperEl.Add(Rule(10, 2));
            var hdr = Row4("연번", "성명", "관계", "현재 상태", 16, PaperMid); hdr.style.marginBottom = 4; paperEl.Add(hdr);
            paperEl.Add(Rule(0, 1));
            rowsBox = new VisualElement(); paperEl.Add(rowsBox);
            for (int i = 0; i < suspects.Length; i++)
            {
                int idx = i; var s = suspects[i];
                var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.alignItems = Align.Center; r.style.height = 64;
                r.style.borderBottomWidth = 1; r.style.borderBottomColor = PaperRule; r.style.paddingLeft = 10;
                var n = P($"0{i + 1}", 19, PaperMid); n.style.width = 54; r.Add(n);
                var nameBox = new VisualElement(); nameBox.style.width = 176; nameBox.style.flexDirection = FlexDirection.Row; nameBox.style.alignItems = Align.FlexEnd;
                var nm = P(s.name, 28, PaperInk); nm.style.unityFontStyleAndWeight = FontStyle.Bold; nameBox.Add(nm);
                var ag = P($"{s.age}세", 17, PaperMid); ag.style.marginLeft = 8; ag.style.marginBottom = 4; nameBox.Add(ag);
                r.Add(nameBox);
                var rel = P(ShortRelation(s.relation), 16, PaperInk); rel.style.width = 214; rel.style.flexShrink = 0; rel.style.whiteSpace = WhiteSpace.Normal; r.Add(rel);
                var state = P("", 16, OkInk); state.name = "state"; state.style.flexGrow = 1; state.style.flexShrink = 1; state.style.flexBasis = 0; state.style.whiteSpace = WhiteSpace.Normal; r.Add(state);
                var mark = new VisualElement(); mark.name = "mark"; Abs(mark, 10, float.NaN, 10, -4); mark.style.width = 4; mark.style.backgroundColor = StampRed; mark.style.opacity = 0;
                r.Add(mark);
                var called = P("호출", 17, StampRed); called.name = "called"; Abs(called, 16, 6, float.NaN, float.NaN); Border(called, 2, StampRed); Pad(called, 2);
                called.style.paddingLeft = called.style.paddingRight = 8; called.style.rotate = new Rotate(-8f); called.style.opacity = 0; r.Add(called);
                r.RegisterCallback<PointerEnterEvent>(_ => Hover(idx, true));
                r.RegisterCallback<PointerLeaveEvent>(_ => Hover(idx, false));
                r.RegisterCallback<PointerDownEvent>(_ => Select(idx));
                rowsBox.Add(r); rows.Add(r);
            }
            dossierScroll = new ScrollView(ScrollViewMode.Vertical); dossierScroll.style.flexGrow = 1; dossierScroll.style.flexShrink = 1; dossierScroll.style.marginTop = 10;
            dossierScroll.horizontalScrollerVisibility = ScrollerVisibility.Hidden; dossierScroll.verticalScrollerVisibility = ScrollerVisibility.Hidden;   // wheel scroll, no default UI scrollbar on paper
            dossierScroll.mouseWheelScrollSize = 60;
            dossier = new VisualElement(); dossierScroll.contentContainer.Add(dossier);
            paperEl.Add(dossierScroll);
            NoShrink(head); title.style.flexShrink = 0; rowsBox.style.flexShrink = 0; hdr.style.flexShrink = 0;
        }

        void BuildCta()
        {
            callCta = new VisualElement(); Abs(callCta, float.NaN, 60, 60, float.NaN); callCta.style.alignItems = Align.FlexEnd;
            callCta.pickingMode = PickingMode.Position;
            ctaSub = L("", 17, new Color(1, 1, 1, 0.72f)); ctaSub.style.marginBottom = 8; callCta.Add(ctaSub);
            var line = new VisualElement(); line.style.flexDirection = FlexDirection.Row; line.style.alignItems = Align.Center;
            ctaTitle = L("", 34, Ink); if (serifFont) ctaTitle.style.unityFontDefinition = FontDefinition.FromSDFFont(serifFont);
            ctaTitle.style.letterSpacing = 2; line.Add(ctaTitle);
            var key = L("Enter", 15, new Color(1, 1, 1, 0.8f)); key.style.marginLeft = 18; Pad(key, 6); key.style.paddingLeft = key.style.paddingRight = 10;
            Border(key, 1, new Color(1, 1, 1, 0.45f)); Radius(key, 4); line.Add(key); callCta.Add(line);
            ctaBar = new VisualElement(); ctaBar.style.height = 2; ctaBar.style.marginTop = 10; ctaBar.style.backgroundColor = Red; ctaBar.style.width = Length.Percent(28); ctaBar.style.alignSelf = Align.FlexEnd;
            callCta.Add(ctaBar);
            callCta.RegisterCallback<PointerEnterEvent>(_ => { ctaBar.style.width = Length.Percent(100); ctaTitle.style.color = Color.white; });
            callCta.RegisterCallback<PointerLeaveEvent>(_ => { ctaBar.style.width = Length.Percent(28); ctaTitle.style.color = Ink; });
            callCta.RegisterCallback<PointerDownEvent>(_ => CallSelected());
            ledgerLayer.Add(callCta);
            // back to the HQ desk (records, forensics, report) — the ledger is reached from there
            var back = L("← 수사본부   Backspace", 16, new Color(1, 1, 1, 0.75f)); Abs(back, float.NaN, float.NaN, 40, 760);
            back.pickingMode = PickingMode.Position; Pad(back, 8);
            back.RegisterCallback<PointerEnterEvent>(_ => back.style.color = Color.white);
            back.RegisterCallback<PointerLeaveEvent>(_ => back.style.color = new Color(1, 1, 1, 0.75f));
            back.RegisterCallback<PointerDownEvent>(_ => BackToHQ());
            ledgerLayer.Add(back);
        }

        // ------------------------------------------------------------------ state
        void Select(int i, bool instant = false)
        {
            if (suspects == null || i < 0 || i >= suspects.Length) return;
            bool changed = i != sel; sel = i; var s = suspects[i];
            for (int k = 0; k < rows.Count; k++)
            {
                bool on = k == i;
                rows[k].style.backgroundColor = on ? Marker : new Color(0, 0, 0, 0);
                rows[k].Q("mark").style.opacity = on ? 1 : 0;
            }
            if (changed) recordOpen = false;
            if (instant) { bg.style.backgroundImage = s.feed ? s.feed : s.background; bgB.style.opacity = 0; }
            else if (changed) { if (swapCo != null) StopCoroutine(swapCo); swapCo = StartCoroutine(SwapFeed(s)); }
            feedRoom.text = $"{s.room} · CAM 0{i + 1}";
            RenderDossier(s, !instant && changed);
            RenderCta(s);
        }

        void Hover(int i, bool on)
        {
            if (i == sel) return;
            rows[i].style.backgroundColor = on ? new Color(0, 0, 0, 0.06f) : new Color(0, 0, 0, 0);
        }

        /// <summary>0.35 s cross-fade of the waiting-room feed (no black dip, no flash, no shake).</summary>
        IEnumerator SwapFeed(Suspect s)
        {
            var tex = s.feed ? s.feed : s.background;
            bgB.style.backgroundImage = tex; bgB.style.opacity = 0;
            float t = 0; const float D = 0.35f;
            while (t < D) { t += Time.unscaledDeltaTime; bgB.style.opacity = Mathf.SmoothStep(0, 1, t / D); yield return null; }
            bg.style.backgroundImage = tex; bgB.style.opacity = 0;
        }

        void RenderDossier(Suspect s, bool animate)
        {
            dossier.Clear();
            dossier.Add(Section("인적 사항"));
            dossier.Add(KV("성명", $"{s.name} ({s.age}세)"));
            dossier.Add(KV("직업", s.job));
            dossier.Add(KV("관계", s.relation));
            dossier.Add(Section("현장 탐문 시 진술 (요지)"));
            if (s.statements != null)
                foreach (var line in s.statements)
                {
                    var q = P("“" + line + "”", 19, PaperInk); q.style.whiteSpace = WhiteSpace.Normal; q.style.marginBottom = 5; q.style.marginLeft = 4;
                    dossier.Add(q);
                }
            dossier.Add(Section("조사 이력"));
            int n = interviews.TryGetValue(s.id, out var c) ? c : 0;
            var hist = new VisualElement(); hist.style.flexDirection = FlexDirection.Row; hist.style.alignItems = Align.Center;
            hist.Add(P(n == 0 ? "진술녹화실 조사 기록 없음" : $"진술녹화실 조사 {n}회 (이번 수사)", 18, PaperInk));
            records.TryGetValue(s.id, out var rec);
            if (rec != null && rec.Count > 0)
            {
                var open = P(recordOpen ? "면담 기록 접기 ▴" : "면담 기록 열람 ▾", 17, new Color(0.15f, 0.25f, 0.55f));
                open.style.marginLeft = 16; open.style.borderBottomWidth = 1; open.style.borderBottomColor = new Color(0.15f, 0.25f, 0.55f, 0.6f);
                open.RegisterCallback<PointerDownEvent>(_ => { recordOpen = !recordOpen; RenderDossier(s, false); });
                hist.Add(open);
            }
            dossier.Add(hist);
            if (recordOpen && rec != null)
                foreach (var line in rec)
                {
                    var l = P(line, 17, line.StartsWith("형사") ? PaperMid : PaperInk); l.style.whiteSpace = WhiteSpace.Normal; l.style.marginTop = 4; l.style.marginLeft = 4;
                    dossier.Add(l);
                }
            dossier.Add(Section("호출"));
            string why = CallBlockReason(s);
            dossier.Add(P(why ?? $"호출 가능 · {s.room} 대기 중", 18, why == null ? OkInk : StampRed));
            var cost = P(interviews.Count > 0 ? "호출 시 사건 시간 10분 경과 · 추가 면담은 데스크 요청 예산 1 소모" : "호출 시 사건 시간 10분 경과", 16, PaperMid);
            cost.style.marginTop = 4; cost.style.whiteSpace = WhiteSpace.Normal; dossier.Add(cost);
            NoShrink(dossier);
            if (animate) StartCoroutine(RecordIn());
        }

        IEnumerator RecordIn()
        {
            float t = 0; const float D = 0.28f;
            while (t < D) { t += Time.unscaledDeltaTime; float k = Mathf.SmoothStep(0, 1, t / D); dossier.style.opacity = k; dossier.style.translate = new Translate(0, 8 * (1 - k)); yield return null; }
            dossier.style.opacity = 1; dossier.style.translate = new Translate(0, 0);
        }

        /// <summary>World-state reasons only (server state), never story hints.</summary>
        string CallBlockReason(Suspect s)
        {
            if (caseClosed) return "수사보고 제출로 사건이 종결되어 호출할 수 없음";
            if (!string.IsNullOrEmpty(activeOnServer) && activeOnServer != s.id) return "다른 대상 조사 진행 중 — 종료 후 호출 가능";
            if (TZServer.I == null || !TZServer.I.Online) return "로컬 수사 서버 연결 대기 중";
            return null;
        }

        void RenderCta(Suspect s)
        {
            ctaTitle.text = $"{s.name} — {s.room}로 호출";
            var why = CallBlockReason(s);
            ctaSub.text = why ?? "↑ ↓ 대상 선택   ·   호출 즉시 영상 녹화 시작";
            callCta.style.opacity = why == null ? 1f : 0.5f;
        }

        void RefreshRowStates()
        {
            for (int i = 0; i < suspects.Length && i < rows.Count; i++)
            {
                var s = suspects[i]; var l = rows[i].Q<Label>("state");
                int n = interviews.TryGetValue(s.id, out var c) ? c : 0;
                l.text = n == 0 ? $"미조사 · {RoomShort(s.room)}" : $"조사 {n}회 · 대기";
                l.style.color = n == 0 ? OkInk : PaperInk;
                rows[i].Q<Label>("called").style.opacity = calledAt.ContainsKey(s.id) && activeOnServer == s.id ? 1 : 0;
            }
        }

        IEnumerator RefreshLedgerFromServer()
        {
            while (TZServer.I == null || !TZServer.I.Online) { if (suspects != null && sel >= 0) RenderCta(suspects[sel]); yield return new WaitForSecondsRealtime(0.5f); }
            yield return Call("GET", "/v1/state", null, (ok, t) =>
            {
                var r = JsonUtility.FromJson<PublicStateResp>(t);
                if (r?.state == null) return;
                activeOnServer = r.state.active_interview; caseClosed = r.state.case_closed;
                clockText = r.state.clock ?? clockText;
                if (r.state.known_people != null) foreach (var p in r.state.known_people) if (!interviews.ContainsKey(p.id)) interviews[p.id] = 1;
            });
            RefreshRowStates(); RenderDossier(suspects[sel], false); RenderCta(suspects[sel]);
        }

        void CallScreenUpdate()
        {
            if (bgB != null && bg != null) { bgB.style.scale = bg.style.scale; bgB.style.translate = bg.style.translate; }
            if (recDot != null) recDot.style.opacity = (Time.unscaledTime % 1.4f) < 0.9f ? 1 : 0.15f;
            if (feedTime != null) feedTime.text = "2026. 10. 16 (금)  " + (string.IsNullOrEmpty(clockText) ? "--:--" : clockText) + ":" + ((int)(Time.unscaledTime % 60)).ToString("00");
            if (!ledgerOpen || entering || Keyboard.current == null || suspects == null) return;
            if (Keyboard.current.upArrowKey.wasPressedThisFrame) Select((sel + suspects.Length - 1) % suspects.Length);
            if (Keyboard.current.downArrowKey.wasPressedThisFrame) Select((sel + 1) % suspects.Length);
            if (Keyboard.current.enterKey.wasPressedThisFrame || Keyboard.current.numpadEnterKey.wasPressedThisFrame) CallSelected();
            if (Keyboard.current.backspaceKey.wasPressedThisFrame) BackToHQ();
        }

        public void BackToHQ()
        {
            if (!ledgerOpen || entering || busy) return;
            UnityEngine.SceneManagement.SceneManager.LoadScene("Case001_HQ");
        }

        void CallSelected()
        {
            if (!ledgerOpen || entering || busy || sel < 0) return;
            var s = suspects[sel];
            var why = CallBlockReason(s);
            if (why != null) { Toast(why); return; }
            Begin(s);
        }

        /// <summary>Called by the interview flow to keep this session's record (shown under 조사 이력).</summary>
        void RecordTurn(string sid, string who, string line)
        {
            if (string.IsNullOrEmpty(sid)) return;
            if (!records.TryGetValue(sid, out var l)) records[sid] = l = new List<string>();
            l.Add($"{who}: {line}");
        }

        // ------------------------------------------------------------------ transitions
        void SetChrome(bool show, bool instant)
        {
            foreach (var e in new[] { leftCol, rightCol }) if (e != null) e.style.display = DisplayStyle.None;   // on demand only (Tab / R)
            foreach (var e in new[] { topBar, dock })
            {
                if (e == null) continue;
                if (instant) { e.style.display = show ? DisplayStyle.Flex : DisplayStyle.None; e.style.opacity = show ? 1 : 0; }
                else if (show) StartCoroutine(FadeIn(e, 0.5f)); else e.style.display = DisplayStyle.None;
            }
            if (!show && subtitleBox != null) subtitleBox.style.opacity = 0;
            if (!show && recBadge != null) recBadge.style.opacity = 0;
        }

        /// <summary>
        /// Call sequence (interim, 2D): confirm stamp on the ledger → folder closed → corridor steps → door → seated view of
        /// the room shot → recorder click, a beat of silence → question input enabled.
        /// INCOMPLETE vs directive: no 3D interrogation room / 3D suspect entry-and-sit animation exists yet (RELEASE_BLOCKED_ASSET);
        /// no Timeline/Cinemachine sequence (com.unity.timeline not installed). Recorded in 미완성작업.md.
        /// </summary>
        IEnumerator EnterRoom(Suspect s)
        {
            entering = true; ledgerOpen = false;
            calledAt[s.id] = clockText; activeOnServer = s.id; RefreshRowStates();
            var stampEl = rows[sel].Q<Label>("called");
            float t = 0;
            while (t < 0.22f) { t += Time.unscaledDeltaTime; float k = t / 0.22f; stampEl.style.opacity = k; stampEl.style.scale = new Scale(Vector3.one * Mathf.Lerp(1.6f, 1f, k)); yield return null; }
            yield return new WaitForSecondsRealtime(0.45f);
            sfx.PlayOneShot(TZProcAudio.PaperClose(), 0.8f);
            t = 0;
            while (t < 0.5f) { t += Time.unscaledDeltaTime; float k = Mathf.SmoothStep(0, 1, t / 0.5f); ledgerLayer.style.opacity = 1 - k; blackout.style.opacity = k * 0.92f; yield return null; }
            ledgerLayer.style.display = DisplayStyle.None;
            entryCaption.text = s.room; entrySub.text = $"{s.name} ({s.age}세)  ·  {(string.IsNullOrEmpty(clockText) ? "" : clockText + "  ")}조사관 입실";
            for (int i = 0; i < 4; i++) { sfx.PlayOneShot(TZProcAudio.Step(), 0.55f - i * 0.06f); yield return new WaitForSecondsRealtime(0.42f); }
            sfx.PlayOneShot(TZProcAudio.Door(), 0.7f);
            yield return new WaitForSecondsRealtime(0.5f);
            entryCaption.text = ""; entrySub.text = "";
            var r3d = TZInterrogationRoom3D.Instance;
            if (r3d && r3d.CanShow(s.id))
            {   // real 3D room: the photo layer goes away, the detective camera walks in and sits down
                in3D = true;
                bg.style.backgroundImage = null; bgB.style.opacity = 0; stageEl.style.backgroundColor = Color.clear;
                flicker.style.opacity = 0; vignette.style.opacity = 0;
                r3d.Show(s.id);
                var sit = StartCoroutine(r3d.SitDown(2.1f));
                t = 0;
                while (t < 1.2f) { t += Time.unscaledDeltaTime; blackout.style.opacity = 0.92f * (1 - Mathf.SmoothStep(0, 1, t / 1.2f)); yield return null; }
                blackout.style.opacity = 0;
                yield return sit;
            }
            else
            {
            in3D = false;
            bg.style.backgroundImage = s.feed ? s.feed : s.background; bgB.style.opacity = 0;
            bgZoom = 1.12f; bgShiftY = 26f;
            t = 0; const float D = 1.6f;
            while (t < D)
            {
                t += Time.unscaledDeltaTime; float k = Mathf.SmoothStep(0, 1, Mathf.Clamp01(t / D));
                blackout.style.opacity = 0.92f * (1 - Mathf.Clamp01(t / 0.9f));
                bgZoom = Mathf.Lerp(1.12f, 1f, k); bgShiftY = Mathf.Lerp(26f, 0f, k);
                yield return null;
            }
            blackout.style.opacity = 0; bgZoom = 1f; bgShiftY = 0;
            }
            room.volume = 0.16f;
            sfx.PlayOneShot(TZProcAudio.Recorder(), 0.6f);
            recBadge.style.opacity = 1; recLabel.text = $"영상 녹화 중 · {s.room}";
            yield return new WaitForSecondsRealtime(1.4f);   // a beat of silence before the first question
            interviews[s.id] = (interviews.TryGetValue(s.id, out var c) ? c : 0) + 1;
            entering = false;
        }

        void OnInterviewEnded(Suspect ended)
        {
            activeOnServer = null;
            if (in3D)
            {
                in3D = false; TZInterrogationRoom3D.Instance?.Hide();
                stageEl.style.backgroundColor = Color.black; vignette.style.opacity = 1;
            }
            if (ledgerLayer == null) { if (legacyPicker) ShowPicker(true); return; }
            room.volume = 0.22f;
            ledgerLayer.style.display = DisplayStyle.Flex;
            ledgerOpen = true;
            RefreshRowStates(); Select(sel, true);
            StartCoroutine(FadeIn(ledgerLayer, 0.5f));
            StartCoroutine(RefreshLedgerFromServer());
        }

        IEnumerator FadeIn(VisualElement e, float d)
        {
            e.style.display = DisplayStyle.Flex; float t = 0;
            while (t < d) { t += Time.unscaledDeltaTime; e.style.opacity = Mathf.SmoothStep(0, 1, t / d); yield return null; }
            e.style.opacity = 1;
        }

        // ------------------------------------------------------------------ paper typography
        // paper text is all serif (document voice); the sans atlas renders too thin/pale as dark-on-light body text
        Label P(string t, int size, Color c)
        {
            var l = L(t, size, c);
            if (serifFont) l.style.unityFontDefinition = FontDefinition.FromSDFFont(serifFont);   // flat paper → 1:1 sampling, serif reads crisp and dark
            if (size <= 20) l.style.unityFontStyleAndWeight = FontStyle.Bold;   // variable Noto default instance is thin: synth-bold body for print-like ink weight
            return l;
        }
        VisualElement Rule(float top, float h)
        {
            var r = new VisualElement(); r.style.height = h; r.style.marginTop = top; r.style.marginBottom = 8; r.style.backgroundColor = PaperRule; r.style.flexShrink = 0; return r;
        }
        VisualElement Row4(string a, string b, string c, string d, int size, Color col)
        {
            var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.paddingLeft = 10;
            var la = P(a, size, col); la.style.width = 54; r.Add(la);
            var lb = P(b, size, col); lb.style.width = 176; r.Add(lb);
            var lc = P(c, size, col); lc.style.width = 150; r.Add(lc);
            r.Add(P(d, size, col));
            return r;
        }
        Label Section(string t)
        {
            var l = P(t, 16, PaperMid); l.style.marginTop = 14; l.style.marginBottom = 5; l.style.letterSpacing = 1; l.style.unityFontStyleAndWeight = FontStyle.Bold;
            return l;
        }
        VisualElement KV(string k, string v)
        {
            var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.marginBottom = 5;
            var a = P(k, 18, PaperMid); a.style.width = 62; r.Add(a);
            var b = P(v, 18, PaperInk); b.style.whiteSpace = WhiteSpace.Normal; b.style.flexShrink = 1; r.Add(b);
            return r;
        }
        static void Border(VisualElement e, float w, Color c)
        {
            e.style.borderTopWidth = e.style.borderBottomWidth = e.style.borderLeftWidth = e.style.borderRightWidth = w;
            e.style.borderTopColor = e.style.borderBottomColor = e.style.borderLeftColor = e.style.borderRightColor = c;
        }
        static void NoShrink(VisualElement e) { e.style.flexShrink = 0; foreach (var ch in e.Children()) NoShrink(ch); }
        static string ShortRelation(string rel) => rel.Replace("피해자의 ", "").Replace("피해자", "");
        static string RoomShort(string room) => string.IsNullOrEmpty(room) ? "대기실" : room.Replace("진술녹화실", "녹화실");

        static Texture2D rampTex;
        static Texture2D Ramp()
        {
            if (rampTex) return rampTex;
            rampTex = new Texture2D(256, 1, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int x = 0; x < 256; x++) { float u = x / 255f; rampTex.SetPixel(x, 0, new Color(0, 0, 0, Mathf.Lerp(0.82f, 0f, Mathf.SmoothStep(0.55f, 1f, u)))); }
            rampTex.Apply();
            return rampTex;
        }
    }
}
