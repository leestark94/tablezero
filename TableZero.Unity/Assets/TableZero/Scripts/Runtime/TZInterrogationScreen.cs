using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>
    /// 진술녹화실 심문 화면 (user concept INTERROGATION_TARGET_VISUAL). The suspect is a dark cinematic shot whose face is
    /// never readable; the camera breathes slowly, the lamp flickers, film grain + vignette sit on top. Everything the
    /// panels show comes from the authoritative server (time left, questions asked, motions observed) — no invented
    /// percentages. Free typing goes to /v1/interview/ask and the local LLM answers in character.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed partial class TZInterrogationScreen : MonoBehaviour
    {
        [Serializable] public class Suspect { public string id, name, age, job, relation, room; public string[] statements; public Texture2D background, portrait, feed; }

        public FontAsset koreanFont;
        public FontAsset serifFont;
        public Texture2D paper;
        public bool legacyPicker = false;   // V1 card picker kept for reference; the call ledger replaces it
        public Suspect[] suspects;
        public Texture2D grain;
        public int interviewSeconds = 900;

        // ---------------------------------------------------------------- server DTOs
        [Serializable] class StartReq { public string suspect_id; }
        [Serializable] class SceneReq { public string scene; }
        [Serializable] class AskReq { public string question, action_id, input_mode, evidence_id; }
        [Serializable] class StartData { public string actor_id, clock; public int budget_left; }
        [Serializable] class StartResp { public bool ok; public StartData data; public string error; }
        [Serializable] class Receipt { public string actor_id, suspect_text, motion_proposal, reply_mode, provider, performer, model, beat; public int seconds_left, seconds_spent, beat_seq; public float latency_ms, first_token_ms, plan_ms, beat_intensity; }
        [Serializable] class AskResp { public bool ok; public Receipt data; public string error, detail; }
        [Serializable] class JobData { public string job_id; }
        [Serializable] class JobResp { public bool ok; public JobData data; public string error; }
        [Serializable] class JobReq { public string job_id; }
        [Serializable] class PollData { public string partial, error; public bool done, ok; public Receipt receipt; }
        [Serializable] class PollResp { public bool ok; public PollData data; public string error; }
        [Serializable] class EvidenceCard { public string id, name, detail, source, limitation, strength; }
        [Serializable] class EvidenceList { public EvidenceCard[] evidence; }
        [Serializable] class EvidenceResp { public bool ok; public EvidenceList data; }
        [Serializable] class StateData { public string scene, clock; }
        [Serializable] class StateResp { public string mode; public StateData state; }   // GET /v1/state = {mode, state}

        static readonly Dictionary<string, string> MotionKo = new Dictionary<string, string>
        {
            {"look_down", "질문 뒤 시선을 아래로 떨군다"}, {"lean_forward", "몸을 앞으로 기울인다"}, {"jaw_tight", "턱에 힘이 들어간다"},
            {"still", "한동안 움직이지 않는다"}, {"cup_touch", "물컵을 만지작거린다"}, {"hand_stop", "손을 만지던 동작을 멈춘다"},
            {"back_in_chair", "의자 등받이로 몸을 뺀다"}, {"avert_gaze", "특정 질문에서 시선을 피한다"},
        };
        static readonly string[] Suggested = { "그날의 동선에 대해", "피해자와의 관계", "통화 기록에 대해", "현장에 있었던 이유", "마지막으로 본 시간" };
        static readonly Dictionary<string, string> SuggestedQ = new Dictionary<string, string>
        {
            {"그날의 동선에 대해", "그날 저녁 몇 시부터 몇 시까지 어디에 있었는지 순서대로 말해 주세요."},
            {"피해자와의 관계", "정수연 씨와는 어떤 사이였습니까?"},
            {"통화 기록에 대해", "그날 정수연 씨와 통화하거나 연락한 적이 있습니까?"},
            {"현장에 있었던 이유", "그날 302호 근처에 간 적이 있습니까? 있다면 왜 갔습니까?"},
            {"마지막으로 본 시간", "정수연 씨를 마지막으로 본 게 언제입니까?"},
        };

        // ---------------------------------------------------------------- UI
        VisualElement root, stageEl, bg, flicker, grainEl, vignette, picker, evidencePanel, memoList, thinking, topBar, leftCol, rightCol, dock;
        float bgZoom = 1f, bgShiftY = 0f;
        Label continueHint, roomLbl, nameLbl, metaJob, metaRel, metaStatus, clockLbl, recLbl, subName, subText, timeVal, qVal, eVal, toast;
        VisualElement timeBar, portrait, subtitleBox; readonly TZLivingPortrait2D rig2d = new TZLivingPortrait2D();
        TextField input;
        Suspect cur;
        int asked, presented;
        float recStart, secondsLeft;
        bool busy, started;
        string pendingEvidence, pendingName, pendingFragment; VisualElement attachBar; Label attachLabel, attachHint; EvidenceCard[] evCache = new EvidenceCard[0];
        Coroutine typeCo, toastCo;
        bool awaitingContinue, typing; string typingFull = "";

        static readonly Color Red = new Color(0.86f, 0.18f, 0.20f), Ink = new Color(0.93f, 0.93f, 0.92f), Dim = new Color(0.62f, 0.63f, 0.66f),
                              Panel = new Color(0.07f, 0.075f, 0.085f, 0.82f), Line = new Color(1, 1, 1, 0.10f);

        void OnEnable()
        {
            root = GetComponent<UIDocument>().rootVisualElement;
            root.Clear(); root.style.flexGrow = 1;
            if (koreanFont) root.style.unityFontDefinition = FontDefinition.FromSDFFont(koreanFont);
            BuildStage(); BuildTopBar(); BuildLeft(); BuildRight(); BuildBottom(); BuildPicker(); BuildEvidencePanel();
            toast = L("", 16, Ink); toast.style.position = Position.Absolute; toast.style.top = 132; toast.style.alignSelf = Align.Center;
            toast.style.left = Length.Percent(30); toast.style.right = Length.Percent(30); toast.style.unityTextAlign = TextAnchor.MiddleCenter;
            toast.style.backgroundColor = new Color(0, 0, 0, 0.6f); Pad(toast, 8); toast.style.opacity = 0; root.Add(toast);
            SetChrome(false, true);
            if (legacyPicker) ShowPicker(true); else { ShowPicker(false); BuildCallScreen(); }
        }

        void Update()
        {
            CallScreenUpdate(); UpdateAttachHint();
            if (bg != null)
            {   // slow "camera breathing": push-in drift, never still
                float t = Time.time;
                float s = (1.045f + 0.012f * Mathf.Sin(t * 0.21f)) * bgZoom;
                bg.style.scale = new Scale(new Vector3(s, s, 1));
                bg.style.translate = new Translate(Mathf.Sin(t * 0.13f) * 9f, Mathf.Sin(t * 0.17f + 1) * 6f + bgShiftY);
                float f = 0.02f * Mathf.PerlinNoise(t * 3.1f, 0.3f) + (Mathf.PerlinNoise(t * 0.7f, 5f) > 0.86f ? 0.06f : 0f);
                flicker.style.opacity = bg.style.backgroundImage.value.texture != null ? f : 0f;
                grainEl.style.translate = new Translate(UnityEngine.Random.Range(-40, 40), UnityEngine.Random.Range(-40, 40));
                rig2d.Tick(Time.unscaledDeltaTime, new Vector3(s, s, 1), new Vector2(Mathf.Sin(t * 0.13f) * 9f, Mathf.Sin(t * 0.17f + 1) * 6f + bgShiftY));
            }
            if (started)
            {
                float el = Time.unscaledTime - recStart;
                recLbl.text = $"REC  {(int)(el / 3600):00}:{(int)(el / 60) % 60:00}:{(int)el % 60:00}";
            }
            if (thinking != null && thinking.style.display == DisplayStyle.Flex)
                thinking.style.opacity = 0.45f + 0.45f * Mathf.Abs(Mathf.Sin(Time.time * 2.4f));
            var kb = UnityEngine.InputSystem.Keyboard.current; var ms = UnityEngine.InputSystem.Mouse.current;
            bool adv = kb != null && (kb.spaceKey.wasPressedThisFrame || kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame)
                       || ms != null && ms.leftButton.wasPressedThisFrame;
            if (typing && adv) { typing = false; }
            else if (awaitingContinue && adv) { Continue(); return; }
            if (input != null && input.focusController?.focusedElement == input && kb != null && kb.enterKey.wasPressedThisFrame && dock.style.display != DisplayStyle.None) Send();
            if (started && kb != null && (input == null || input.focusController?.focusedElement != input))
            {
                if (kb.tabKey.wasPressedThisFrame) TogglePanel(leftCol);
                if (kb.rKey.wasPressedThisFrame) TogglePanel(rightCol);
                if (kb.eKey.wasPressedThisFrame) OpenEvidence();
                if (kb.escapeKey.wasPressedThisFrame) { if (evidencePanel != null && evidencePanel.style.display == DisplayStyle.Flex) evidencePanel.style.display = DisplayStyle.None; else EndInterview(); }
            }
        }

        // ---------------------------------------------------------------- build
        void BuildStage()
        {
            var stage = new VisualElement(); Abs(stage, 0, 0, 0, 0); stageEl = stage; stage.style.overflow = Overflow.Hidden; stage.style.backgroundColor = Color.black;
            bg = new VisualElement(); Abs(bg, 0, 0, 0, 0);
            bg.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Cover);
            stage.Add(bg);
            rig2d.Build(stage, 20261123);   // moving 2D head layer for suspects without a 3D actor
            flicker = new VisualElement(); Abs(flicker, 0, 0, 0, 0); flicker.pickingMode = PickingMode.Ignore;
            flicker.style.backgroundColor = Color.black; stage.Add(flicker);   // lamp flicker = brief brightness dips, never a colour wash
            grainEl = new VisualElement(); Abs(grainEl, -60, -60, -60, -60); grainEl.pickingMode = PickingMode.Ignore;
            if (grain) { grainEl.style.backgroundImage = grain; grainEl.style.backgroundRepeat = new BackgroundRepeat(Repeat.Repeat, Repeat.Repeat); }
            grainEl.style.opacity = 0.010f; stage.Add(grainEl);
            vignette = new VisualElement(); Abs(vignette, 0, 0, 0, 0); vignette.pickingMode = PickingMode.Ignore;
            vignette.style.backgroundImage = Resources.Load<Texture2D>("TZ_Vignette"); vignette.style.backgroundSize = new BackgroundSize(Length.Percent(100), Length.Percent(100));
            stage.Add(vignette);
            root.Add(stage);
        }

        void BuildTopBar()
        {
            var bar = new VisualElement(); topBar = bar; Abs(bar, 0, 0, float.NaN, 0); bar.style.height = 56; bar.style.flexDirection = FlexDirection.Row;
            bar.style.alignItems = Align.Center; bar.style.backgroundColor = new Color(0.02f, 0.02f, 0.025f, 0.55f);
            bar.style.borderBottomWidth = 1; bar.style.borderBottomColor = Line; bar.style.paddingLeft = 28; bar.style.paddingRight = 24;
            var logo = new VisualElement(); logo.style.width = 300;
            var l1 = L("TABLE//ZERO", 22, Ink); l1.style.letterSpacing = 6; l1.style.unityFontStyleAndWeight = FontStyle.Bold;
            logo.Add(l1); logo.Add(L("CASE 001 — 302호 사망 경위 조사", 13, Dim)); bar.Add(logo);
            var tabs = new VisualElement(); tabs.style.flexDirection = FlexDirection.Row; tabs.style.flexGrow = 1; tabs.style.justifyContent = Justify.Center;
            roomLbl = L("", 15, Dim); roomLbl.style.unityTextAlign = TextAnchor.MiddleCenter; tabs.Add(roomLbl);
            bar.Add(tabs);
            var right = new VisualElement(); right.style.flexDirection = FlexDirection.Row; right.style.alignItems = Align.Center;
            clockLbl = L("2026. 10. 16 (금)", 15, Ink); clockLbl.style.marginRight = 28; right.Add(clockLbl);
            recLbl = L("REC  00:00:00", 15, Ink); recLbl.style.color = new Color(1, 0.45f, 0.45f); right.Add(recLbl);
            bar.Add(right);
            root.Add(bar);
        }

        void BuildLeft()
        {
            var col = new VisualElement(); leftCol = col; Abs(col, 88, float.NaN, float.NaN, 24); col.style.width = 384;
            var card = Box(); card.style.flexDirection = FlexDirection.Row;
            portrait = new VisualElement(); portrait.style.width = 96; portrait.style.height = 124; portrait.style.marginRight = 14;
            portrait.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Cover); Radius(portrait, 4);
            card.Add(portrait);
            var info = new VisualElement(); info.style.flexGrow = 1;
            info.Add(L("용의자", 13, Dim));
            nameLbl = L("—", 28, Ink); nameLbl.style.unityFontStyleAndWeight = FontStyle.Bold; nameLbl.style.marginTop = 2; nameLbl.style.marginBottom = 8; info.Add(nameLbl);
            metaJob = Meta(info, "직업"); metaRel = Meta(info, "관계"); metaStatus = Meta(info, "진술");
            card.Add(info); col.Add(card);

            var st = Box(); st.style.marginTop = 14;
            st.Add(Header("면담 상태"));
            var tr = Row(st, "남은 면담 시간"); timeVal = tr.Item2;
            var track = new VisualElement(); track.style.height = 6; track.style.backgroundColor = new Color(1, 1, 1, 0.12f); Radius(track, 3); track.style.marginBottom = 10;
            timeBar = new VisualElement(); timeBar.style.height = 6; timeBar.style.width = Length.Percent(100); timeBar.style.backgroundColor = Red; Radius(timeBar, 3);
            track.Add(timeBar); st.Add(track);
            qVal = Row(st, "한 질문").Item2; eVal = Row(st, "제시한 증거").Item2;
            col.Add(st);

            var memo = Box(); memo.style.marginTop = 14;
            memo.Add(Header("관찰 메모"));
            memoList = new VisualElement(); memo.Add(memoList);
            var hint = L("심문 중 관찰된 행동이 여기에 기록됩니다", 13, Dim); hint.name = "memo-hint"; memoList.Add(hint);
            col.Add(memo);
            root.Add(col);
        }

        void BuildRight()
        {
            var col = new VisualElement(); rightCol = col; Abs(col, 88, 24, float.NaN, float.NaN); col.style.width = 330;
            ActionBtn(col, "직접 질문", "자유롭게 질문을 입력합니다.", true, () => input?.Focus());
            ActionBtn(col, "증거 제시", "확보한 증거를 보여줍니다.", true, OpenEvidence);
            ActionBtn(col, "분석 / 대조", "데스크에서 진술과 기록을 대조합니다.", false, () => Toast("분석·대조는 데스크(TABLE INDEX)에서 진행합니다"));
            ActionBtn(col, "심리 압박", "침묵, 반복 추궁 등 — 녹화되며 진술 신빙성에 영향", false, () => Toast("심리 압박 전술은 아직 연결되지 않았습니다"));
            ActionBtn(col, "심문 종료", "면담을 끝내고 다른 사람을 부릅니다.", true, EndInterview);
            root.Add(col);
        }

        void BuildBottom()
        {
            subtitleBox = new VisualElement(); Abs(subtitleBox, float.NaN, Length.Percent(16), 64, Length.Percent(16)); subtitleBox.style.flexDirection = FlexDirection.Row;
            subtitleBox.style.alignItems = Align.FlexStart; subtitleBox.style.opacity = 0; subtitleBox.pickingMode = PickingMode.Ignore;
            subtitleBox.style.backgroundColor = new Color(0.01f, 0.01f, 0.012f, 0.80f); Radius(subtitleBox, 6);
            subtitleBox.style.paddingTop = 16; subtitleBox.style.paddingBottom = 18; subtitleBox.style.paddingLeft = 22; subtitleBox.style.paddingRight = 22;
            var bar = new VisualElement(); bar.style.width = 2; bar.style.height = 54; bar.style.backgroundColor = Red; bar.style.marginRight = 16; subtitleBox.Add(bar);
            subName = L("", 22, new Color(1f, 0.35f, 0.38f)); subName.style.width = 92; subName.style.unityFontStyleAndWeight = FontStyle.Bold; subtitleBox.Add(subName);
            subText = L("", 26, Ink); subText.style.whiteSpace = WhiteSpace.Normal; subText.style.flexShrink = 1; subText.style.flexGrow = 1;
            subText.style.textShadow = new TextShadow { offset = new Vector2(0, 2), blurRadius = 6, color = new Color(0, 0, 0, 0.9f) };
            subtitleBox.Add(subText);
            thinking = L("· · ·", 26, Ink); thinking.style.display = DisplayStyle.None; subtitleBox.Insert(subtitleBox.IndexOf(subText), thinking);
            continueHint = L("Space · Enter · 클릭  계속", 13, Dim); continueHint.style.position = Position.Absolute;
            continueHint.style.right = 16; continueHint.style.bottom = 6; continueHint.style.opacity = 0; subtitleBox.Add(continueHint);
            root.Add(subtitleBox);

            dock = new VisualElement(); Abs(dock, float.NaN, Length.Percent(19), 28, Length.Percent(19)); dock.style.backgroundColor = new Color(0.03f, 0.03f, 0.035f, 0.72f);
            Radius(dock, 8); dock.style.borderTopWidth = dock.style.borderBottomWidth = dock.style.borderLeftWidth = dock.style.borderRightWidth = 1;
            dock.style.borderTopColor = dock.style.borderBottomColor = dock.style.borderLeftColor = dock.style.borderRightColor = Line; Pad(dock, 10);
            var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.alignItems = Align.Center;
            var mic = new VisualElement(); mic.style.width = 52; mic.style.height = 52; Radius(mic, 26); mic.style.backgroundColor = new Color(1, 1, 1, 0.06f);
            mic.style.justifyContent = Justify.Center; mic.style.alignItems = Align.Center; mic.style.marginRight = 10;
            mic.tooltip = "음성 질문 — 준비 중"; mic.Add(L("마이크", 11, Dim)); row.Add(mic);
            input = new TextField { maxLength = 300 }; input.style.flexGrow = 1; input.style.height = 52; input.style.fontSize = 18;
            var inner = input.Q(className: TextField.inputUssClassName);
            if (inner != null)
            {
                inner.style.backgroundColor = new Color(0.08f, 0.08f, 0.09f, 0.85f); inner.style.color = Ink; Radius(inner, 6);
                inner.style.borderTopWidth = inner.style.borderBottomWidth = inner.style.borderLeftWidth = inner.style.borderRightWidth = 1;
                inner.style.borderTopColor = inner.style.borderBottomColor = inner.style.borderLeftColor = inner.style.borderRightColor = new Color(1, 1, 1, 0.14f);
                inner.style.paddingLeft = 14;
            }
            input.textEdition.placeholder = "질문을 입력하거나 마이크로 말하세요 (음성 준비 중)"; input.textEdition.hidePlaceholderOnFocus = true;
            row.Add(input);
            var send = new Button(Send) { text = "보내기" }; send.style.width = 96; send.style.height = 52; send.style.marginLeft = 12; send.style.fontSize = 17;
            send.style.backgroundColor = Red; send.style.color = Color.white; Radius(send, 6); row.Add(send);
            dock.Add(row);
            var tools = new VisualElement(); tools.style.flexDirection = FlexDirection.Row; tools.style.marginTop = 8; tools.style.alignItems = Align.Center;
            var chips = new VisualElement(); chips.style.flexDirection = FlexDirection.Row; chips.style.marginTop = 8; chips.style.alignItems = Align.Center; chips.style.display = DisplayStyle.None;
            ToolBtn(tools, "인물 기록", "Tab", () => TogglePanel(leftCol));
            ToolBtn(tools, "증거 제시", "E", OpenEvidence);
            ToolBtn(tools, "심문 행동", "R", () => TogglePanel(rightCol));
            ToolBtn(tools, "추천 질문", "Q", () => chips.style.display = chips.style.display == DisplayStyle.None ? DisplayStyle.Flex : DisplayStyle.None);
            var sp = new VisualElement(); sp.style.flexGrow = 1; tools.Add(sp);
            ToolBtn(tools, "면담 종료", "Esc", EndInterview);
            dock.Add(tools);
            foreach (var s in Suggested)
            {
                var key = s;
                var c = new Button(() => { input.value = SuggestedQ[key]; input.Focus(); }) { text = s };
                c.style.flexGrow = 1; c.style.height = 40; c.style.fontSize = 15; c.style.color = Ink; c.style.backgroundColor = new Color(1, 1, 1, 0.05f);
                Radius(c, 4); c.style.marginRight = 8; chips.Add(c);
            }
            dock.Add(chips);
            root.Add(dock);
            // attached record: always visible above the input, so a record MENTIONED in a question is never confused with one actually PRESENTED
            attachBar = new VisualElement(); Abs(attachBar, float.NaN, Length.Percent(19), 112, Length.Percent(19)); attachBar.style.flexDirection = FlexDirection.Row; attachBar.style.alignItems = Align.Center;
            attachBar.style.backgroundColor = new Color(0.16f, 0.12f, 0.08f, 1f); Radius(attachBar, 6); Pad(attachBar, 8); attachBar.style.display = DisplayStyle.None;
            attachBar.style.borderLeftWidth = 4; attachBar.style.borderLeftColor = new Color(0.86f, 0.68f, 0.40f);
            attachLabel = L("", 16, new Color(1f, 0.93f, 0.80f)); attachLabel.style.flexGrow = 1; attachLabel.style.whiteSpace = WhiteSpace.Normal; attachBar.Add(attachLabel);
            var viewBtn = new Button(() => OpenEvidence()) { text = "원본 보기" }; viewBtn.style.height = 32; viewBtn.style.marginRight = 6; attachBar.Add(viewBtn);
            var clrBtn = new Button(() => ClearAttachment()) { text = "첨부 해제" }; clrBtn.style.height = 32; attachBar.Add(clrBtn);
            root.Add(attachBar);
            attachHint = L("※ 질문에 기록 이름을 적은 것만으로는 자료를 제시한 것이 아닙니다. E 키로 기록을 첨부하세요", 13, new Color(0.95f, 0.78f, 0.5f)); Abs(attachHint, float.NaN, Length.Percent(19), 112, Length.Percent(19)); attachHint.style.display = DisplayStyle.None; attachHint.pickingMode = PickingMode.Ignore; root.Add(attachHint);
        }

        void ToolBtn(VisualElement parent, string text, string key, Action act)
        {
            var b = new Button(act); b.style.flexDirection = FlexDirection.Row; b.style.alignItems = Align.Center; b.style.height = 30;
            b.style.backgroundColor = Color.clear; b.style.borderTopWidth = b.style.borderBottomWidth = b.style.borderLeftWidth = b.style.borderRightWidth = 0;
            b.style.marginRight = 6; b.style.paddingLeft = 8; b.style.paddingRight = 8;
            b.Add(L(text, 14, Dim));
            var k = L(key, 11, Dim); k.style.marginLeft = 6; k.style.paddingLeft = 5; k.style.paddingRight = 5;
            k.style.borderTopWidth = k.style.borderBottomWidth = k.style.borderLeftWidth = k.style.borderRightWidth = 1;
            k.style.borderTopColor = k.style.borderBottomColor = k.style.borderLeftColor = k.style.borderRightColor = new Color(1, 1, 1, 0.18f); Radius(k, 3); b.Add(k);
            b.RegisterCallback<MouseEnterEvent>(_ => b.style.backgroundColor = new Color(1, 1, 1, 0.06f));
            b.RegisterCallback<MouseLeaveEvent>(_ => b.style.backgroundColor = Color.clear);
            parent.Add(b);
        }

        /// <summary>Side panels are closed during questioning; they open on demand and never stay over the suspect.</summary>
        void TogglePanel(VisualElement e)
        {
            if (e == null) return;
            bool show = e.style.display == DisplayStyle.None;
            e.style.display = show ? DisplayStyle.Flex : DisplayStyle.None; e.style.opacity = 1;
        }

        void BuildPicker()
        {
            picker = new VisualElement(); Abs(picker, 0, 0, 0, 0); picker.style.backgroundColor = new Color(0, 0, 0, 0.86f);
            picker.style.alignItems = Align.Center; picker.style.justifyContent = Justify.Center;
            var t = L("진술녹화실", 34, Ink); t.style.unityFontStyleAndWeight = FontStyle.Bold; picker.Add(t);
            var st = L("누구를 부르시겠습니까? 면담마다 사건 시간이 흐릅니다.", 17, Dim); st.style.marginBottom = 30; picker.Add(st);
            var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row;
            foreach (var s in suspects ?? new Suspect[0])
            {
                var sus = s;
                var c = new Button(() => Begin(sus)); c.style.width = 330; c.style.height = 420; c.style.marginLeft = c.style.marginRight = 14;
                c.style.backgroundColor = new Color(0.08f, 0.08f, 0.09f); Radius(c, 6); c.style.paddingTop = c.style.paddingBottom = c.style.paddingLeft = c.style.paddingRight = 0;
                c.style.flexDirection = FlexDirection.Column; c.style.overflow = Overflow.Hidden;
                var img = new VisualElement(); img.style.height = 290; img.style.backgroundImage = s.portrait; img.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Cover);
                c.Add(img);
                var n = L($"{s.name} ({s.age})", 24, Ink); n.style.marginTop = 14; n.style.marginLeft = 18; n.style.unityTextAlign = TextAnchor.MiddleLeft; c.Add(n);
                var j = L(s.job, 14, Dim); j.style.marginLeft = 18; j.style.unityTextAlign = TextAnchor.MiddleLeft; j.style.whiteSpace = WhiteSpace.Normal; c.Add(j);
                var r = L(s.relation, 14, Dim); r.style.marginLeft = 18; r.style.unityTextAlign = TextAnchor.MiddleLeft; c.Add(r);
                row.Add(c);
            }
            picker.Add(row);
            root.Add(picker);
        }

        void BuildEvidencePanel()
        {
            evidencePanel = new VisualElement(); Abs(evidencePanel, 88, 380, 252, 380); evidencePanel.style.backgroundColor = new Color(0.075f, 0.08f, 0.09f, 1f);   // fully opaque: nothing shows through from the room behind
            Radius(evidencePanel, 8); Pad(evidencePanel, 20); evidencePanel.style.display = DisplayStyle.None;
            root.Add(evidencePanel);
        }

        // ---------------------------------------------------------------- flow
        void ShowPicker(bool on) { picker.style.display = on ? DisplayStyle.Flex : DisplayStyle.None; }

        void Begin(Suspect s)
        {
            if (busy) return;
            if (TZServer.I == null || !TZServer.I.Online) { Toast("로컬 수사 서버에 연결 중입니다. 잠시 후 다시 시도하세요"); return; }
            busy = true;
            StartCoroutine(BeginCo(s));
        }

        IEnumerator BeginCo(Suspect s)
        {
            // scene chain on the server: whatever we are in -> desk -> interview (illegal hops are rejected and ignored)
            string scene = "";
            yield return Call("GET", "/v1/state", null, (ok, t) => { var r = JsonUtility.FromJson<StateResp>(t); scene = r?.state?.scene ?? ""; });
            if (scene != "interview")
            {
                if (scene != "desk") yield return Call("POST", "/v1/scene", JsonUtility.ToJson(new SceneReq { scene = "desk" }), null);
                yield return Call("POST", "/v1/scene", JsonUtility.ToJson(new SceneReq { scene = "interview" }), null);
            }
            bool ok = false; string err = "";
            yield return Call("POST", "/v1/interview/start", JsonUtility.ToJson(new StartReq { suspect_id = s.id }), (o, t) =>
            {
                var r = JsonUtility.FromJson<StartResp>(t); ok = o && r != null && r.ok; err = r?.error ?? t;
                if (ok && r.data != null && !string.IsNullOrEmpty(r.data.clock)) clockLbl.text = r.data.clock;
            });
            busy = false;
            if (!ok) { Toast("면담을 시작하지 못했습니다: " + err); yield break; }
            cur = s; asked = 0; presented = 0; secondsLeft = interviewSeconds; started = true; recStart = Time.unscaledTime;
            bg.style.backgroundImage = s.feed ? s.feed : s.background; portrait.style.backgroundImage = s.portrait;
            { var a3 = TZInterrogationRoom3D.Instance ? TZInterrogationRoom3D.Instance.ActiveActor : null; bool is3D = a3 != null; var tex = s.feed ? s.feed : s.background; rig2d.SetImage(is3D ? null : tex); }
            roomLbl.text = $"{s.room}  ·  {s.name} ({s.age})";
            nameLbl.text = $"{s.name} ({s.age})"; metaJob.text = s.job; metaRel.text = s.relation; metaStatus.text = "면담 진행 중";
            memoList.Clear(); memoList.Add(L("심문 중 관찰된 행동이 여기에 기록됩니다", 13, Dim));
            RefreshState(); ShowPicker(false);
            Say("", "");
            yield return EnterRoom(s);
            SetChrome(true, false);
            input.Focus();
        }

        void Send()
        {
            if (busy || cur == null) return;
            var q = (input.value ?? "").Trim();
            if (q.Length < 2 && pendingEvidence == null) return;
            busy = true; input.value = "";
            ShowDock(false);
            StartCoroutine(AskCo(q.Length < 2 ? "이걸 보세요. 설명해 보시겠습니까?" : q, pendingEvidence));
            ClearAttachment();
        }

        IEnumerator AskCo(string q, string evidence)
        {
            var actor = TZInterrogationRoom3D.Instance ? TZInterrogationRoom3D.Instance.ActiveActor : null;
            Say("형사", q); RecordTurn(cur.id, "형사", q);
            if (actor) actor.SetState(TZSuspectActor.State.Listen);
            rig2d.SetBeat(TZLivingPortrait2D.Beat.Listening, 0.4f);
            // The request leaves IMMEDIATELY; listening is acting that runs in parallel with generation (never a delay in front of it).
            float tSubmit = Time.realtimeSinceStartup;
            float listenFor = Mathf.Clamp(q.Length * 0.02f, 0.4f, 1.0f);
            Say(cur.name, ""); thinking.style.display = DisplayStyle.Flex;
            var body = JsonUtility.ToJson(new AskReq { question = q, action_id = TZServer.NewActionId(), input_mode = "typed", evidence_id = evidence });
            // Streamed turn: the server generates in the background; we poll the growing line and type it as it arrives.
            // While nothing has arrived the suspect is visibly thinking (gaze away, breath) - the wait is part of the acting.
            string jobId = null, raw = "";
            yield return Call("POST", "/v1/interview/ask_start", body, (o, t) => { raw = t; try { jobId = JsonUtility.FromJson<JobResp>(t)?.data?.job_id; } catch { } }, 15);
            float tAccepted = Time.realtimeSinceStartup - tSubmit;   // input accepted by the server
            bool thinkSet = false; float tFirst = -1f, tReact = -1f, tSubDone = -1f;
            string target = ""; PollData fin = null; bool pollBusy = false; int pollFail = 0; int shown = 0; bool began = false;
            float t0 = Time.realtimeSinceStartup, nextPoll = 0, nextChar = 0;
            if (typeCo != null) { StopCoroutine(typeCo); typeCo = null; }
            TZFramePacing.AIBusy(true);   // give the GPU to the model while the suspect thinks
            while (!string.IsNullOrEmpty(jobId))
            {
                float now = Time.realtimeSinceStartup;
                if (!pollBusy && fin == null && now >= nextPoll)
                {
                    pollBusy = true;
                    StartCoroutine(Call("POST", "/v1/interview/ask_poll", JsonUtility.ToJson(new JobReq { job_id = jobId }), (o, t) =>
                    {
                        pollBusy = false; nextPoll = Time.realtimeSinceStartup + 0.12f;
                        PollResp p = null; try { p = JsonUtility.FromJson<PollResp>(t); } catch { }
                        if (p == null || !p.ok || p.data == null) { pollFail++; raw = t; return; }
                        pollFail = 0;
                        if (p.data.done) fin = p.data;
                        target = p.data.done && p.data.ok && p.data.receipt != null ? p.data.receipt.suspect_text ?? "" : p.data.partial ?? "";
                    }, 10));
                }
                if (pollFail > 25 || now - t0 > 240f) break;
                if (fin != null && !fin.ok) break;
                // the server restarted a rejected attempt: what we typed is no longer the start of the line
                if (shown > 0 && (target.Length < shown || string.CompareOrdinal(target, 0, subText.text, 0, shown) != 0)) { shown = 0; subText.text = ""; }
                if (!thinkSet && now - tSubmit >= listenFor) { thinkSet = true; tReact = now - tSubmit; if (actor) actor.SetState(TZSuspectActor.State.Think); rig2d.SetBeat(TZLivingPortrait2D.Beat.Considering, 0.4f); }
                if (!began && target.Length > 0 && now - tSubmit >= listenFor)
                {
                    began = true; tFirst = now - tSubmit; thinking.style.display = DisplayStyle.None; Say(cur.name, ""); typing = true;
                    if (actor) actor.Speak(target, "answer", null);
                    rig2d.SetBeat(TZLivingPortrait2D.Beat.Answering, 0.3f); rig2d.SetSpeaking(true);
                    nextChar = now + 0.45f;   // breath before the first syllable
                }
                if (began)
                {
                    if (!typing) { shown = target.Length; subText.text = target; }   // player skipped the typing
                    else if (shown < target.Length && now >= nextChar)
                    {
                        shown++; subText.text = target.Substring(0, shown);
                        char c = target[shown - 1]; if (c == ' ' || c == ',') rig2d.Pulse();
                        float per = Mathf.Min(0.06f, 2.0f / Mathf.Max(8, target.Length));   // whole line types in <= ~2 s: subtitles never add seconds on top of the answer
                        nextChar = now + (c == ' ' ? per * 0.5f : (c == ',' || c == '…' || c == '.' || c == '?' || c == '!') ? per * 3f : per);
                    }
                }
                if (fin != null && shown >= target.Length && began) { tSubDone = now - tSubmit; break; }
                yield return null;
            }
            TZFramePacing.AIBusy(false);
            thinking.style.display = DisplayStyle.None; busy = false; typing = false;
            if (fin == null || !fin.ok || fin.receipt == null)
            {
                Say(cur.name, "……"); if (actor) actor.SetState(TZSuspectActor.State.Silence);
                string err = fin?.error ?? raw ?? "";
                Toast(err.Contains("ai_unavailable") || err.Contains("503") ? "로컬 AI가 응답하지 않습니다 (Ollama 실행 확인)" : "답변을 받지 못했습니다: " + err);
                awaitingContinue = true; continueHint.style.opacity = 1;
                yield break;
            }
            var rc = fin.receipt;
            rig2d.SetSpeaking(false); rig2d.SetBeat(string.IsNullOrEmpty(rc.beat) ? "Idle" : rc.beat, rc.beat_intensity, rc.beat_seq);
            TZLatencyLog.Write(cur.id, q.Length, tAccepted, tFirst, Time.realtimeSinceStartup - tSubmit, rc, tReact, tSubDone);
            if (Application.isEditor || Debug.isDebugBuild) Toast(rc.performer == "LLM" ? $"[개발] 로컬 모델 · 첫 글자 {tFirst:0.0}s · 완료 {Time.realtimeSinceStartup - tSubmit:0.0}s" : $"[개발] {rc.performer} (모델 답변 아님) · {Time.realtimeSinceStartup - tSubmit:0.0}s");
            asked++; if (evidence != null) presented++;
            secondsLeft = rc.seconds_left; RefreshState();
            subText.text = rc.suspect_text;
            if (actor) actor.UpdateLine(rc.suspect_text, rc.reply_mode, rc.motion_proposal);
            RecordTurn(cur.id, cur.name, rc.suspect_text);
            awaitingContinue = true; continueHint.style.opacity = 1;
            var resp = new AskResp { ok = true, data = rc };
            if (!string.IsNullOrEmpty(resp.data.motion_proposal) && MotionKo.TryGetValue(resp.data.motion_proposal, out var m)) AddMemo(m);
            if (secondsLeft <= 0) { metaStatus.text = "면담 시간 종료"; Toast("면담 시간이 끝났습니다"); }
        }

        void EndInterview()
        {
            if (busy || cur == null) { SetChrome(false, false); OnInterviewEnded(null); return; }
            busy = true;
            StartCoroutine(Call("POST", "/v1/interview/end", "{}", (o, t) =>
            {
                busy = false; started = false; var ended = cur; cur = null; Say("", ""); SetChrome(false, false); OnInterviewEnded(ended);
                StartCoroutine(Call("POST", "/v1/scene", JsonUtility.ToJson(new SceneReq { scene = "desk" }), null));
            }));
        }

        void SetAttachment(EvidenceCard ev, string fragment)
        {
            pendingEvidence = ev.id; pendingName = ev.name; pendingFragment = fragment;
            attachLabel.text = "첨부한 기록: " + ev.name + (string.IsNullOrEmpty(fragment) ? "" : "  ·  짚은 부분: “" + fragment + "”") + "\n질문을 보내면 이 기록을 상대에게 정식으로 제시합니다";
            attachBar.style.display = DisplayStyle.Flex; attachHint.style.display = DisplayStyle.None;
        }

        void ClearAttachment() { pendingEvidence = null; pendingName = null; pendingFragment = null; if (attachBar != null) attachBar.style.display = DisplayStyle.None; }

        /// <summary>Mentioned but not attached: tell the player (the suspect only reacts to attached records).</summary>
        void UpdateAttachHint()
        {
            if (attachHint == null || input == null) return;
            bool mention = pendingEvidence == null && !string.IsNullOrEmpty(input.value) && System.Array.Exists(evCache, e => e != null && !string.IsNullOrEmpty(e.name) && input.value.Contains(ShortName(e.name)));
            attachHint.style.display = mention ? DisplayStyle.Flex : DisplayStyle.None;
        }
        static string ShortName(string n) { int i = n.IndexOfAny(new[] { ' ', '·', '(' }); return (i > 2 ? n.Substring(0, i) : n); }

        void OpenEvidence()
        {
            if (cur == null) return;
            StartCoroutine(Call("POST", "/v1/evidence/list", "{}", (o, t) =>
            {
                evidencePanel.Clear();
                // bounded modal: title + scrolling list + a close bar that can never leave the panel (7+ records no longer spill over the dialogue)
                evidencePanel.style.flexDirection = FlexDirection.Column;
                var head = new VisualElement(); head.style.flexDirection = FlexDirection.Row; head.style.alignItems = Align.Center; head.style.flexShrink = 0;
                var h = L("증거 제시", 24, new Color(1f, 0.96f, 0.88f)); h.style.flexGrow = 1; head.Add(h);
                var x = new Button(() => evidencePanel.style.display = DisplayStyle.None) { text = "닫기 (Esc)" }; x.style.height = 34; x.style.fontSize = 15; head.Add(x);
                evidencePanel.Add(head);
                var hint = L("기록을 고르면 질문에 첨부됩니다. 아래 조각을 고르면 그 부분을 짚어 묻습니다", 14, new Color(0.85f, 0.86f, 0.88f)); hint.style.marginTop = 4; hint.style.marginBottom = 8; hint.style.flexShrink = 0; evidencePanel.Add(hint);
                var sv = new ScrollView(); sv.style.flexGrow = 1; sv.style.flexShrink = 1; sv.style.minHeight = 0; evidencePanel.Add(sv);
                var r = JsonUtility.FromJson<EvidenceResp>(t);
                var list = r?.data?.evidence ?? new EvidenceCard[0]; evCache = list;
                if (list.Length == 0) sv.Add(L("아직 확보한 증거가 없습니다. 현장에서 채취·봉인하거나 데스크에서 기록을 요청하세요.", 15, Dim));
                foreach (var e in list)
                {
                    var ev = e;
                    var card = new VisualElement(); card.style.backgroundColor = new Color(0.14f, 0.15f, 0.17f, 1f); card.style.marginBottom = 8; Pad(card, 12); Radius(card, 4); card.style.borderLeftWidth = 3; card.style.borderLeftColor = new Color(0.86f, 0.68f, 0.40f);
                    var b2 = new Button(() => { SetAttachment(ev, null); evidencePanel.style.display = DisplayStyle.None; input.value = $"이 {ev.name}, 설명해 보시겠습니까?"; input.Focus(); });
                    b2.style.flexDirection = FlexDirection.Column; b2.style.alignItems = Align.FlexStart; b2.style.backgroundColor = new Color(0, 0, 0, 0); b2.style.borderTopWidth = b2.style.borderBottomWidth = b2.style.borderLeftWidth = b2.style.borderRightWidth = 0; b2.style.paddingLeft = 0;
                    b2.Add(L(ev.name, 18, new Color(1f, 0.96f, 0.88f)));
                    var d = L($"출처: {ev.source}\n한계: {ev.limitation}", 14, new Color(0.82f, 0.84f, 0.86f)); d.style.whiteSpace = WhiteSpace.Normal; b2.Add(d);
                    card.Add(b2);
                    if (!string.IsNullOrEmpty(ev.detail))
                    {
                        var chips = new VisualElement(); chips.style.flexDirection = FlexDirection.Row; chips.style.flexWrap = Wrap.Wrap; chips.style.marginTop = 4;
                        foreach (var seg in ev.detail.Split(new[] { ',', '·', ';', '/' }, StringSplitOptions.RemoveEmptyEntries))
                        {
                            var sg = seg.Trim(); if (sg.Length < 3 || sg.Length > 40) continue;
                            var c = new Button(() => { SetAttachment(ev, sg); evidencePanel.style.display = DisplayStyle.None; input.value = $"이 {ev.name}에서 '{sg}' 부분은 어떻게 설명하시겠습니까?"; input.Focus(); }) { text = sg };
                            c.style.fontSize = 14; c.style.marginRight = 6; c.style.marginTop = 4; c.style.height = 30; c.style.backgroundColor = new Color(0.30f, 0.23f, 0.14f, 1f); c.style.color = new Color(1f, 0.95f, 0.85f); chips.Add(c);
                        }
                        card.Add(chips);
                    }
                    sv.Add(card);
                }
                evidencePanel.style.display = DisplayStyle.Flex;
            }));
        }

        // ---------------------------------------------------------------- helpers
        IEnumerator Call(string method, string path, string body, Action<bool, string> done, int timeout = 30)
        {
            bool fin = false; bool ok = false; string text = "";
            if (method == "GET") TZServer.I.Get(path, (o, t) => { ok = o; text = t; fin = true; });
            else TZServer.I.Post(path, body ?? "{}", (o, t) => { ok = o; text = t; fin = true; }, timeout);
            while (!fin) yield return null;
            done?.Invoke(ok, text);
        }

        void RefreshState()
        {
            int s = Mathf.Max(0, (int)secondsLeft);
            timeVal.text = $"{s / 60:00}:{s % 60:00}";
            timeBar.style.width = Length.Percent(100f * s / Mathf.Max(1, interviewSeconds));
            qVal.text = asked.ToString(); eVal.text = presented.ToString();
        }

        void AddMemo(string m)
        {
            if (memoList.childCount == 1 && memoList[0] is Label l0 && l0.text.StartsWith("심문 중")) memoList.Clear();
            var l = L("•  " + m, 15, Ink); l.style.marginBottom = 6; l.style.whiteSpace = WhiteSpace.Normal; memoList.Add(l);
            while (memoList.childCount > 6) memoList.RemoveAt(0);
        }

        void Say(string who, string text)
        {
            if (typeCo != null) StopCoroutine(typeCo);
            subName.text = who; subText.text = text;
            subName.style.color = who == "형사" ? new Color(0.70f, 0.78f, 0.92f) : new Color(1f, 0.35f, 0.38f);
            subtitleBox.style.opacity = string.IsNullOrEmpty(who) && string.IsNullOrEmpty(text) ? 0 : 1;
            subtitleBox.style.bottom = 64; subText.style.color = Ink; continueHint.style.opacity = 0;
        }

        /// <summary>Input bar is only on screen while the player is composing; it never covers a reply.</summary>
        void ShowDock(bool show)
        {
            if (dock == null) return;
            dock.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
            if (show)
            {   // last reply stays readable, dimmed, just above the bar
                if (subtitleBox.style.opacity.value > 0) { subtitleBox.style.bottom = 178; subText.style.color = new Color(0.86f, 0.86f, 0.84f); }
                input.Focus();
            }
            else input.Blur();
        }

        void Continue()
        {
            awaitingContinue = false; continueHint.style.opacity = 0;
            if (cur != null && started) ShowDock(true);
        }

        void TypeLine(string who, string text)
        {
            if (typeCo != null) StopCoroutine(typeCo);
            typeCo = StartCoroutine(TypeCo(who, text ?? ""));
        }

        IEnumerator TypeCo(string who, string text)
        {
            Say(who, ""); typing = true; typingFull = text;
            for (int i = 1; i <= text.Length && typing; i++)
            {
                subText.text = text.Substring(0, i);
                char c = text[i - 1];
                float d = c == ' ' ? 0.035f : (c == ',' || c == '…' || c == '.' || c == '?' || c == '!') ? 0.32f : 0.085f;
                yield return new WaitForSecondsRealtime(d);
            }
            subText.text = text; typing = false;
        }

        void Toast(string m)
        {
            if (toastCo != null) StopCoroutine(toastCo);
            toastCo = StartCoroutine(ToastCo(m));
        }

        IEnumerator ToastCo(string m) { toast.text = m; toast.style.opacity = 1; yield return new WaitForSecondsRealtime(3.2f); toast.style.opacity = 0; }

        static Label L(string t, int size, Color c) { var l = new Label(t); l.style.fontSize = size; l.style.color = c; return l; }
        static void Abs(VisualElement e, float top, float right, float bottom, float left)
        {
            e.style.position = Position.Absolute;
            if (!float.IsNaN(top)) e.style.top = top; if (!float.IsNaN(right)) e.style.right = right;
            if (!float.IsNaN(bottom)) e.style.bottom = bottom; if (!float.IsNaN(left)) e.style.left = left;
        }
        static void Abs(VisualElement e, float top, Length right, float bottom, Length left)
        {
            e.style.position = Position.Absolute; if (!float.IsNaN(top)) e.style.top = top; e.style.right = right; e.style.bottom = bottom; e.style.left = left;
        }
        static void Radius(VisualElement e, float r) { e.style.borderTopLeftRadius = e.style.borderTopRightRadius = e.style.borderBottomLeftRadius = e.style.borderBottomRightRadius = r; }
        static void Pad(VisualElement e, float p) { e.style.paddingTop = e.style.paddingBottom = e.style.paddingLeft = e.style.paddingRight = p; }
        VisualElement Box()
        {
            var b = new VisualElement(); b.style.backgroundColor = Panel; Radius(b, 8); Pad(b, 16);
            b.style.borderTopWidth = b.style.borderBottomWidth = b.style.borderLeftWidth = b.style.borderRightWidth = 1;
            b.style.borderTopColor = b.style.borderBottomColor = b.style.borderLeftColor = b.style.borderRightColor = Line;
            return b;
        }
        static Label Header(string t) { var h = L(t, 17, Ink); h.style.marginBottom = 12; h.style.unityFontStyleAndWeight = FontStyle.Bold; return h; }
        static Label Meta(VisualElement parent, string key)
        {
            var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.marginBottom = 4;
            var k = L(key, 14, Dim); k.style.width = 40; r.Add(k);
            var v = L("", 13, Ink); v.style.whiteSpace = WhiteSpace.Normal; v.style.flexShrink = 1; r.Add(v);
            parent.Add(r); return v;
        }
        static (Label, Label) Row(VisualElement parent, string key)
        {
            var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.justifyContent = Justify.SpaceBetween; r.style.marginBottom = 6;
            var k = L(key, 15, Ink); var v = L("—", 15, Ink); r.Add(k); r.Add(v); parent.Add(r); return (k, v);
        }
        void ActionBtn(VisualElement col, string title, string sub, bool enabled, Action click)
        {
            var b = new Button(click); b.style.flexDirection = FlexDirection.Column; b.style.alignItems = Align.FlexStart; b.style.marginBottom = 10;
            b.style.height = 70; b.style.justifyContent = Justify.Center; b.style.paddingLeft = 20; Radius(b, 6);
            b.style.backgroundColor = new Color(0.07f, 0.075f, 0.085f, enabled ? 0.86f : 0.6f);
            b.style.borderTopWidth = b.style.borderBottomWidth = b.style.borderLeftWidth = b.style.borderRightWidth = 1;
            b.style.borderTopColor = b.style.borderBottomColor = b.style.borderLeftColor = b.style.borderRightColor = new Color(1, 1, 1, enabled ? 0.16f : 0.06f);
            var t = L(title, 19, enabled ? Ink : Dim); var s = L(sub, 13, Dim); s.style.whiteSpace = WhiteSpace.Normal;
            b.Add(t); b.Add(s); col.Add(b);
        }
    }
}
