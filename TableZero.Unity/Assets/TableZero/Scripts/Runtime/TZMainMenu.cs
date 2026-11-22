using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;
using static TableZero.TZUIKit;

namespace TableZero
{
    /// <summary>
    /// MAIN_MENU → CASE_SELECT → DISPATCH/INCIDENT_BRIEF → 302호 출동 (V21.1 UX spec). The brief shows only what is
    /// confirmed at assignment time: report 22:07, found unconscious, taken to hospital, death confirmed, cause under
    /// investigation. No suspects, no injury time, no money figure. Buttons that have no implementation yet are shown
    /// disabled with the reason (never a decorative button pretending to work).
    /// </summary>
    public sealed class TZMainMenu : MonoBehaviour
    {
        public FontAsset koreanFont;
        public const string RoomScene = "Case001_Room302";
        VisualElement root, page;

        // build after every OnEnable has run: the UIDocument may attach its panel after this component on scene load
        IEnumerator Start()
        {
            yield return null;
            root = GetComponent<UIDocument>().rootVisualElement; root.Clear(); root.style.flexGrow = 1;
            if (koreanFont) root.style.unityFontDefinition = FontDefinition.FromSDFFont(koreanFont);
            root.style.backgroundColor = Bg;
            page = new VisualElement(); Full(page); root.Add(page);
            Menu();
        }

        void Show(VisualElement content) { page.Clear(); page.Add(content); }

        VisualElement Shell(string crumb)
        {
            var s = new VisualElement(); Full(s); s.style.paddingLeft = 90; s.style.paddingRight = 90; s.style.paddingTop = 60;
            var top = new VisualElement(); top.style.flexDirection = FlexDirection.Row; top.style.alignItems = Align.Center;
            var brand = L("TABLE//ZERO", 24, Ink, true); brand.style.letterSpacing = 5; top.Add(brand);
            var c = L(crumb, 13, Dim); c.style.marginLeft = 24; top.Add(c); s.Add(top); s.Add(Divider());
            return s;
        }

        void Menu()
        {
            var s = new VisualElement(); Full(s); s.style.flexDirection = FlexDirection.Row;
            var left = new VisualElement(); left.style.width = Length.Percent(42); left.style.paddingLeft = 110; left.style.justifyContent = Justify.Center;
            var brand = L("TABLE//ZERO", 30, Ink, true); brand.style.letterSpacing = 8; left.Add(brand);
            var tag = L("진술은 남는다. 진실은 숨는다", 40, Ink); tag.style.marginTop = 26; tag.style.marginBottom = 8; left.Add(tag);
            left.Add(L("세 사람의 진술이 서로 부딪칠 때, 수사 시간을 어디에 쓸 것인가", 16, Dim));
            var col = new VisualElement(); col.style.width = 280; col.style.marginTop = 38;
            col.Add(Btn("새 사건", CaseSelect, primary: true));
            col.Add(Btn("이어하기", null, enabled: false, whyDisabled: "저장/불러오기는 다음 단계(P2)에서 구현됩니다"));
            col.Add(Btn("사건 기록", null, enabled: false, whyDisabled: "종결된 사건이 아직 없습니다"));
            col.Add(Btn("설정", null, enabled: false, whyDisabled: "설정 화면은 아직 구현되지 않았습니다"));
            col.Add(Btn("종료", () => { Application.Quit();
#if UNITY_EDITOR
                UnityEditor.EditorApplication.isPlaying = false;
#endif
            }));
            left.Add(col);
            var note = L("이어하기·사건 기록·설정은 아직 동작하지 않습니다 (회색 표시)", 12, Dim); note.style.marginTop = 10; left.Add(note);
            s.Add(left);
            var right = new VisualElement(); right.style.flexGrow = 1; right.style.justifyContent = Justify.FlexEnd; right.style.alignItems = Align.FlexEnd;
            right.style.paddingRight = 70; right.style.paddingBottom = 60;
            right.Add(L("경기도 소도시 다세대주택 302호  ·  00:10", 13, Dim));
            s.Add(right);
            Show(s);
        }

        void CaseSelect()
        {
            var s = Shell("사건 선택");
            s.Add(L("사건을 선택하십시오", 34, Ink));
            var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.marginTop = 26;
            var c1 = Box(Panel); c1.style.width = 460; c1.style.marginRight = 24;
            c1.Add(L("CASE 001", 12, Dim)); c1.Add(L("302호의 밤", 28, Ink, true));
            var d1 = L("여성 사망 사건  ·  현장 조사와 세 사람 자유 심문", 15, Dim); d1.style.marginTop = 6; d1.style.marginBottom = 12; c1.Add(d1);
            c1.Add(Btn("사건 배정 받기", Dispatch, primary: true)); row.Add(c1);
            var c2 = Box(Panel); c2.style.width = 460; c2.style.opacity = 0.6f;
            c2.Add(L("CASE 002", 12, Dim)); c2.Add(L("다음 사건", 28, Ink, true));
            var d2 = L("사건 데이터가 아직 없습니다", 15, Dim); d2.style.marginTop = 6; d2.style.marginBottom = 12; c2.Add(d2);
            c2.Add(Btn("제작 준비 중", null, enabled: false, whyDisabled: "CASE 002 데이터 미구현")); row.Add(c2);
            s.Add(row);
            var back = Btn("뒤로", Menu); back.style.width = 140; back.style.marginTop = 26; s.Add(back);
            Show(s);
        }

        void Dispatch()
        {
            var s = Shell("CASE 001 · 사건 배정 — 확인된 정보만");
            s.Add(L("302호의 밤", 34, Ink));
            var paper = new VisualElement(); paper.style.backgroundColor = Paper; Pad(paper, 30); Radius(paper, 4); paper.style.marginTop = 20; paper.style.maxWidth = 900;
            paper.Add(L("사건 배정 기록  ·  CASE 001", 12, new Color(0.38f, 0.38f, 0.36f)));
            var name = L("정수연  ·  29세", 26, PaperInk, true); name.style.marginTop = 10; name.style.marginBottom = 12; paper.Add(name);
            void Row(string k, string v)
            {
                var r = new VisualElement(); r.style.flexDirection = FlexDirection.Row; r.style.marginBottom = 8;
                var kk = L(k, 16, new Color(0.32f, 0.33f, 0.32f), true); kk.style.width = 90; r.Add(kk);
                var vv = L(v, 16, PaperInk); vv.style.flexShrink = 1; r.Add(vv); paper.Add(r);
            }
            Row("주소", "경기도 소도시 다세대주택 302호");
            Row("신고", "2026년 10월 15일 22:07, 301호 거주자 신고");
            Row("조치", "의식 없는 상태로 발견 → 응급처치 후 이송 → 병원에서 사망 확인");
            Row("경위", "부상 발생 과정과 정확한 시각은 조사 중");
            Row("현재", "10월 16일 00:10. 피해자는 병원에 있고 현장은 통제 중");
            var order = L("수사 지시: 현장을 확인하고 사망에 이른 경위를 조사하라. 이 기록에는 현재 확인된 내용만 적는다", 15, PaperInk);
            order.style.marginTop = 14; paper.Add(order);
            s.Add(paper);
            var row = new VisualElement(); row.style.flexDirection = FlexDirection.Row; row.style.marginTop = 24;
            var go = Btn("302호 출동", () => StartCoroutine(GoToScene()), primary: true); go.style.width = 200; go.style.marginRight = 12; row.Add(go);
            var back = Btn("뒤로", CaseSelect); back.style.width = 140; row.Add(back);
            s.Add(row);
            Show(s);
        }

        IEnumerator GoToScene()
        {
            var fade = new VisualElement(); Full(fade); fade.style.backgroundColor = Color.black; fade.style.opacity = 0; root.Add(fade);
            var cap = L("빌라 302호 · 00:10", 22, Ink); cap.style.alignSelf = Align.Center; cap.style.marginTop = Length.Percent(24); fade.Add(cap);
            float t = 0; while (t < 0.8f) { t += Time.unscaledDeltaTime; fade.style.opacity = t / 0.8f; yield return null; }
            yield return new WaitForSecondsRealtime(0.8f);
            // a NEW case is a new investigation: the server issues a new session (evidence, budget, memory, report all fresh)
            bool started = false, okNew = false; float wait = 0;
            while (TZServer.I != null && !TZServer.I.Online && wait < 20f) { wait += Time.unscaledDeltaTime; yield return null; }
            TZSession.StartNewCase(g => { okNew = g; started = true; });
            while (!started) yield return null;
            if (!okNew && TZServer.I != null) Debug.LogWarning("[case] server did not start a new session; continuing with the current one");
            TZCaseFlow.SkipBriefing = true;   // the assignment brief was just read; the room shows only the short objective
            SceneManager.LoadScene(RoomScene);
        }
    }
}
