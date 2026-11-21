using System;
using System.Collections;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>
    /// CASE 001 play order in the 302 scene: briefing (controls + what to do) → free scene investigation with a live
    /// evidence count → Tab "수사 수첩" → return to the station (server scene → desk) → interrogation scene (call ledger).
    /// Attaches itself to Case001_Room302 at runtime, so the baked scene does not need rebuilding.
    /// The evidence list shown is whatever the authoritative server says was acquired (no client-side guessing).
    /// </summary>
    public sealed class TZCaseFlow : MonoBehaviour
    {
        const string RoomScene = "Case001_Room302", InterrogationScene = "Case001_Interrogation";

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (SceneManager.GetActiveScene().name != RoomScene) return;
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "-tzbench") >= 0) return;   // benchmark runs stay unattended
            if (FindAnyObjectByType<TZCaseFlow>()) return;
            new GameObject("TZCaseFlow").AddComponent<TZCaseFlow>();
        }

        [Serializable] class EvidenceCard { public string id, name, source; }
        [Serializable] class EvidenceList { public EvidenceCard[] evidence; }
        [Serializable] class EvidenceResp { public bool ok; public EvidenceList data; }
        [Serializable] class SceneReq { public string scene; }

        TZPlayerController player;
        VisualElement root, briefing, notebook, fade, objective;
        Label objLabel, nbList, fadeCaption;
        EvidenceCard[] evidence = new EvidenceCard[0];
        bool inBriefing = true, nbOpen, leaving;
        float nextPoll;

        static readonly Color Ink = new Color(0.93f, 0.92f, 0.89f), Dim = new Color(0.62f, 0.62f, 0.60f), Red = new Color(0.86f, 0.18f, 0.20f);

        IEnumerator Start()
        {
            player = FindAnyObjectByType<TZPlayerController>();
            var hudDoc = FindObjectsByType<UIDocument>(FindObjectsSortMode.None).FirstOrDefault();
            var doc = gameObject.AddComponent<UIDocument>();
            if (hudDoc) { doc.panelSettings = hudDoc.panelSettings; doc.sortingOrder = hudDoc.sortingOrder + 10; }
            yield return null;
            root = doc.rootVisualElement; root.style.flexGrow = 1; root.pickingMode = PickingMode.Ignore;
            var hud = FindAnyObjectByType<TZHud>();
            if (hud && hud.koreanFont) root.style.unityFontDefinition = FontDefinition.FromSDFFont(hud.koreanFont);
            BuildObjective(); BuildNotebook(); BuildFade(); BuildBriefing();
            Lock(true);
        }

        // ------------------------------------------------------------------ UI
        static Label L(string t, int size, Color c) { var l = new Label(t); l.style.fontSize = size; l.style.color = c; l.style.whiteSpace = WhiteSpace.Normal; return l; }
        static void Full(VisualElement e) { e.style.position = Position.Absolute; e.style.left = 0; e.style.right = 0; e.style.top = 0; e.style.bottom = 0; }

        void BuildBriefing()
        {
            briefing = new VisualElement(); Full(briefing); briefing.style.backgroundColor = new Color(0.012f, 0.012f, 0.016f, 0.99f);
            briefing.style.alignItems = Align.Center; briefing.style.justifyContent = Justify.Center;
            var col = new VisualElement(); col.style.width = 760;
            var head = L("CASE 001  ·  302호의 밤", 15, Dim); head.style.letterSpacing = 3; col.Add(head);
            var title = L("현장 조사 개시", 40, Ink); title.style.marginTop = 6; title.style.unityFontStyleAndWeight = FontStyle.Bold; col.Add(title);
            var line = new VisualElement(); line.style.height = 1; line.style.backgroundColor = new Color(1, 1, 1, 0.15f); line.style.marginTop = 18; line.style.marginBottom = 18; col.Add(line);
            var c1 = L("2026. 10. 15 (목) 22:07 301호 주민 신고. 302호 거주 여성 1명이 의식을 잃은 상태로 발견돼 응급처치 후 이송, 병원에서 사망이 확인됐다.\n부상 경위와 정확한 시각은 조사 중이다. 피해자는 현장에 없다. 지금은 10월 16일 00:10.", 19, Ink); col.Add(c1);
            var steps = new[] { ("1", "302호 현장을 조사한다", "사물을 살펴보고, 사진을 찍고, 장갑을 끼고 증거를 채취한다"),
                                ("2", "확보한 증거를 가지고 경찰서로 복귀한다", "Tab — 수사 수첩에서 복귀"),
                                ("3", "관련자를 호출해 심문한다", "증거를 제시하고 진술을 대조한다") };
            foreach (var (n, t, d) in steps)
            {
                var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.marginTop = 16;
                var num = L(n, 22, Red); num.style.width = 34; row.Add(num);
                var txt = new VisualElement(); txt.Add(L(t, 20, Ink)); var dd = L(d, 15, Dim); dd.style.marginTop = 2; txt.Add(dd); row.Add(txt);
                col.Add(row);
            }
            var keys = L("이동 WASD   ·   손전등 F   ·   살펴보기 Q   ·   상호작용 E   ·   촬영 C   ·   장갑 G   ·   채취 X(길게)   ·   앉기 Ctrl   ·   수사 수첩 Tab", 14, Dim);
            keys.style.marginTop = 30; col.Add(keys);
            var go = L("Enter   수사 시작", 20, Ink); go.style.marginTop = 26; go.style.alignSelf = Align.FlexEnd;
            go.style.paddingLeft = 18; go.style.paddingRight = 18; go.style.paddingTop = 10; go.style.paddingBottom = 10;
            go.style.borderBottomWidth = 2; go.style.borderBottomColor = Red; col.Add(go);
            briefing.Add(col); root.Add(briefing);
        }

        void BuildObjective()
        {
            objective = new VisualElement(); objective.style.position = Position.Absolute; objective.style.left = 36; objective.style.top = 52;
            objective.pickingMode = PickingMode.Ignore;
            objLabel = L("", 16, new Color(0.92f, 0.91f, 0.87f, 0.92f)); objLabel.style.unityFontStyleAndWeight = FontStyle.Bold; objective.Add(objLabel);
            objective.style.opacity = 0; root.Add(objective);
        }

        void BuildNotebook()
        {
            notebook = new VisualElement(); Full(notebook); notebook.style.backgroundColor = new Color(0, 0, 0, 0.72f);
            notebook.style.alignItems = Align.Center; notebook.style.justifyContent = Justify.Center; notebook.style.display = DisplayStyle.None;
            var paper = new VisualElement(); paper.style.width = 620; paper.style.backgroundColor = new Color(0.86f, 0.84f, 0.79f);
            paper.style.paddingLeft = 40; paper.style.paddingRight = 40; paper.style.paddingTop = 34; paper.style.paddingBottom = 30;
            var ink = new Color(0.12f, 0.11f, 0.10f);
            var nbt = L("수사 수첩", 34, ink); nbt.style.unityFontStyleAndWeight = FontStyle.Bold; paper.Add(nbt);
            var sub = L("CASE 001 · 302호 현장 · 확보 증거 (서버 기록 기준)", 16, new Color(0.30f, 0.28f, 0.25f)); sub.style.marginBottom = 16; paper.Add(sub);
            nbList = L("", 20, ink); nbList.style.unityFontStyleAndWeight = FontStyle.Bold; nbList.style.marginBottom = 22; paper.Add(nbList);
            var hint = L("Enter   경찰서로 복귀해 심문 시작\nTab   현장 조사 계속", 20, ink); hint.style.unityFontStyleAndWeight = FontStyle.Bold; paper.Add(hint);
            var warn = L("복귀하면 사건 시각이 흐른다 (이동·서류 처리 약 38분). 필요하면 나중에 현장으로 돌아올 수 있다.", 13, new Color(0.40f, 0.20f, 0.18f));
            warn.style.fontSize = 15; warn.style.color = new Color(0.45f, 0.16f, 0.14f); warn.style.marginTop = 12; paper.Add(warn);
            notebook.Add(paper); root.Add(notebook);
        }

        void BuildFade()
        {
            fade = new VisualElement(); Full(fade); fade.style.backgroundColor = Color.black; fade.style.opacity = 0; fade.pickingMode = PickingMode.Ignore;
            fade.style.alignItems = Align.Center; fade.style.justifyContent = Justify.Center;
            fadeCaption = L("", 24, Ink); fade.Add(fadeCaption); root.Add(fade);
        }

        // ------------------------------------------------------------------ flow
        void Lock(bool locked)
        {
            if (!player) return;
            player.inputLocked = locked; player.SetCursor(!locked);
        }

        void Update()
        {
            var kb = Keyboard.current; if (kb == null || root == null || leaving) return;
            if (inBriefing)
            {
                if (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame) BeginInvestigation();
                return;
            }
            if (kb.tabKey.wasPressedThisFrame) SetNotebook(!nbOpen);
            else if (nbOpen && (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame)) ReturnToStation();
            else if (nbOpen && kb.escapeKey.wasPressedThisFrame) SetNotebook(false);
            if (Time.unscaledTime > nextPoll) Poll();
        }

        public void BeginInvestigation()
        {
            if (!inBriefing || root == null) return;
            inBriefing = false; briefing.style.display = DisplayStyle.None; objective.style.opacity = 1; Lock(false); Poll();
        }

        public void SetNotebook(bool open)
        {
            if (inBriefing || leaving || root == null) return;
            nbOpen = open; notebook.style.display = open ? DisplayStyle.Flex : DisplayStyle.None; Lock(open); if (open) Poll();
        }

        public void ReturnToStation() { if (!leaving && !inBriefing) StartCoroutine(GoToStation()); }

        void Poll()
        {
            nextPoll = Time.unscaledTime + 4f;
            if (TZServer.I == null) { Render(); return; }
            TZServer.I.Post("/v1/evidence/list", "{}", (ok, t) =>
            {
                if (ok) { try { evidence = JsonUtility.FromJson<EvidenceResp>(t)?.data?.evidence ?? new EvidenceCard[0]; } catch { } }
                Render();
            });
        }

        void Render()
        {
            objLabel.text = $"현장 조사  ·  확보 증거 {evidence.Length}건  ·  Tab 수사 수첩";
            nbList.text = evidence.Length == 0 ? "아직 확보한 증거가 없다.\n촬영(C)·채취(X 길게)한 것만 증거로 남는다."
                                               : string.Join("\n", evidence.Select((e, i) => $"{i + 1:00}  {e.name}"));
        }

        IEnumerator GoToStation()
        {
            leaving = true; notebook.style.display = DisplayStyle.None;
            bool done = false;
            if (TZServer.I != null)
                TZServer.I.Post("/v1/scene", JsonUtility.ToJson(new SceneReq { scene = "desk" }), (ok, t) => { if (!ok) Debug.Log("[flow] scene→desk: " + t); done = true; });
            else done = true;
            float t0 = 0; fadeCaption.text = "";
            while (t0 < 0.8f) { t0 += Time.unscaledDeltaTime; fade.style.opacity = Mathf.SmoothStep(0, 1, t0 / 0.8f); yield return null; }
            fadeCaption.text = "○○경찰서 형사과 강력1팀";
            float wait = 0; while (!done && wait < 10f) { wait += Time.unscaledDeltaTime; yield return null; }
            yield return new WaitForSecondsRealtime(1.2f);
            UnityEngine.Cursor.lockState = CursorLockMode.None; UnityEngine.Cursor.visible = true;
            SceneManager.LoadScene(InterrogationScene);
        }
    }
}
