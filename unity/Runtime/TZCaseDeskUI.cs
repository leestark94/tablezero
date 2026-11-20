using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>
    /// CASE DESK 1.0 — UI Toolkit front end to SERVER-AUTHORITATIVE records.
    /// No fabricated evidence, guilt labels, fake unlocks, auto contradiction detection,
    /// or world-state changes from UI effects. Visual quality requires Unity review.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class TZCaseDeskUI : MonoBehaviour
    {
        [Serializable] public class Record
        {
            public string id;            // Optional; present for acquired evidence only
            public string kind;
            public string title;
            public string detail;
            public string provenance;
            public string status;
            public string display_status;
            public string limitation;
        }
        [Serializable] public class PageData
        {
            public string tab;
            public Record[] records;
            public string context;
            public string connection;
        }

        public StyleSheet designSheet;
        public TZFirstPersonInvestigation investigator;
        public event Action<string> NavigationRequested;
        public event Action<string> QuestionRequested;
        public event Action<string, string[]> FinalReportRequested;
        public event Action<bool> ReducedMotionChanged;
        public event Action<bool> SubtitlesChanged;
        private UIDocument document;
        private VisualElement root, desk, deskShell, reportCompose, questionCompose, settingsCompose;
        private ScrollView content, reportEvidenceList;
        private Label titleLabel, pageDescription, kicker, context, toast, connection, subtitle, recordCount;
        private Label inspectorStatus, inspectorTitle, inspectorObservation, inspectorProvenance, inspectorLimitation;
        private Label compareA, compareB, compareStatus;
        private TextField questionField;
        private DropdownField accusedField;
        private Button confirmReport, askButton, submitButton, compareButton;
        private Toggle reduceMotionToggle, subtitlesToggle;
        private Slider scaleSlider;
        private bool opened, reportAwaitingConfirmation;
        private readonly Dictionary<Button, Action> boundClickHandlers = new Dictionary<Button, Action>();
        private EventCallback<ChangeEvent<bool>> motionCallback, subtitlesCallback;
        private EventCallback<ChangeEvent<float>> scaleCallback;
        private string selectedTab = "case";
        private Record selectedRecord, firstRecord, secondRecord;
        private readonly Dictionary<string, Toggle> reportEvidenceToggles = new Dictionary<string, Toggle>();
        private readonly Dictionary<string, PageData> cache = new Dictionary<string, PageData>();
        private static readonly string[] Tabs = { "case", "evidence", "interview", "timeline", "report", "settings" };
        private static readonly Dictionary<string, string> TabNames = new Dictionary<string, string>
        {
            {"case", "사건 개요"}, {"evidence", "증거 보관함"}, {"interview", "진술 기록"},
            {"timeline", "시간 대조"}, {"report", "수사보고서"}, {"settings", "설정"}
        };

        private void OnEnable()
        {
            document = GetComponent<UIDocument>();
            root = document != null ? document.rootVisualElement : null;
            if (root == null) { Debug.LogError("TABLE ZERO UI: UIDocument missing root"); return; }
            if (designSheet != null && !root.styleSheets.Contains(designSheet)) root.styleSheets.Add(designSheet);
            desk = root.Q<VisualElement>("case-desk");
            deskShell = root.Q<VisualElement>("desk-shell");
            content = root.Q<ScrollView>("content-list");
            reportEvidenceList = root.Q<ScrollView>("report-evidence-list");
            titleLabel = root.Q<Label>("page-title");
            pageDescription = root.Q<Label>("page-description");
            kicker = root.Q<Label>("page-kicker");
            context = root.Q<Label>("context-text");
            toast = root.Q<Label>("toast-line");
            connection = root.Q<Label>("connection-status");
            subtitle = root.Q<Label>("hud-subtitle");
            recordCount = root.Q<Label>("record-count");
            inspectorStatus = root.Q<Label>("inspector-status");
            inspectorTitle = root.Q<Label>("inspector-title");
            inspectorObservation = root.Q<Label>("inspector-observation");
            inspectorProvenance = root.Q<Label>("inspector-provenance");
            inspectorLimitation = root.Q<Label>("inspector-limitation");
            compareA = root.Q<Label>("compare-a"); compareB = root.Q<Label>("compare-b");
            compareStatus = root.Q<Label>("compare-status");
            reportCompose = root.Q<VisualElement>("report-compose");
            questionCompose = root.Q<VisualElement>("interview-compose");
            settingsCompose = root.Q<VisualElement>("settings-compose");
            questionField = root.Q<TextField>("question-input");
            accusedField = root.Q<DropdownField>("accused-choice");
            confirmReport = root.Q<Button>("report-confirm");
            askButton = root.Q<Button>("question-submit");
            submitButton = root.Q<Button>("report-submit");
            compareButton = root.Q<Button>("inspector-compare");
            reduceMotionToggle = root.Q<Toggle>("reduce-motion");
            subtitlesToggle = root.Q<Toggle>("show-subtitles");
            scaleSlider = root.Q<Slider>("ui-scale");
            if (desk == null || content == null || titleLabel == null || reportEvidenceList == null ||
                compareButton == null || askButton == null || submitButton == null || confirmReport == null)
            {
                Debug.LogError("TABLE ZERO UI: expected UXML elements are missing; verify CaseDesk.uxml V10");
                return;
            }
            foreach (string tab in Tabs)
            {
                string captured = tab;
                Button button = root.Q<Button>("nav-" + tab);
                if (button != null) Bind(button, () => Navigate(captured));
            }
            Button close = root.Q<Button>("close-desk"); if (close != null) Bind(close, () => SetOpened(false));
            Button clear = root.Q<Button>("compare-clear"); if (clear != null) Bind(clear, ClearCompare);
            Bind(compareButton, AddSelectedToCompare);
            Bind(askButton, SubmitQuestion);
            Bind(submitButton, ReviewReport);
            Bind(confirmReport, ConfirmReport);
            motionCallback = e => ReducedMotionChanged?.Invoke(e.newValue);
            subtitlesCallback = e => SubtitlesChanged?.Invoke(e.newValue);
            scaleCallback = e => { if (deskShell != null) deskShell.transform.scale = new Vector3(e.newValue, e.newValue, 1f); };
            if (reduceMotionToggle != null) reduceMotionToggle.RegisterValueChangedCallback(motionCallback);
            if (subtitlesToggle != null) subtitlesToggle.RegisterValueChangedCallback(subtitlesCallback);
            if (scaleSlider != null) scaleSlider.RegisterValueChangedCallback(scaleCallback);
            SetOpened(false); Navigate("case");
            ClearCompare(); ClearInspector();
        }

        private void Bind(Button button, Action callback)
        {
            button.clicked += callback;
            boundClickHandlers[button] = callback;
        }
        private void OnDisable()
        {
            foreach (var binding in boundClickHandlers) binding.Key.clicked -= binding.Value;
            boundClickHandlers.Clear();
            if (reduceMotionToggle != null && motionCallback != null) reduceMotionToggle.UnregisterValueChangedCallback(motionCallback);
            if (subtitlesToggle != null && subtitlesCallback != null) subtitlesToggle.UnregisterValueChangedCallback(subtitlesCallback);
            if (scaleSlider != null && scaleCallback != null) scaleSlider.UnregisterValueChangedCallback(scaleCallback);
        }

        public void SetOpened(bool value)
        {
            opened = value;
            if (desk != null) desk.style.display = value ? DisplayStyle.Flex : DisplayStyle.None;
            if (investigator != null) investigator.SetFocusUI(value);
            if (!value && toast != null) toast.text = "";
        }
        public void Toggle() => SetOpened(!opened);
        public void HandleEscape() => SetOpened(false);
        public void SetConnection(string value) { if (connection != null) connection.text = value ?? ""; }
        public void SetContext(string value) { if (context != null) context.text = value ?? ""; }
        public void SetSubtitle(string value) { if (subtitle != null) subtitle.text = value ?? ""; }
        public void SetAccusedChoices(List<string> choices)
        {
            if (accusedField == null) return;
            accusedField.choices = choices ?? new List<string>();
            if (accusedField.choices.Count > 0) accusedField.index = 0;
        }
        public void SetReportEvidenceChoices(Dictionary<string, string> acquiredEvidence)
        {
            reportEvidenceToggles.Clear();
            if (reportEvidenceList == null) return;
            reportEvidenceList.Clear();
            if (acquiredEvidence == null) return;
            foreach (var pair in acquiredEvidence)
            {
                Toggle toggle = new Toggle(pair.Value);
                toggle.AddToClassList("report-evidence-checkbox");
                reportEvidenceList.Add(toggle);
                reportEvidenceToggles[pair.Key] = toggle;
            }
        }
        private string[] SelectedEvidence()
        {
            List<string> ids = new List<string>();
            foreach (var entry in reportEvidenceToggles) if (entry.Value.value) ids.Add(entry.Key);
            return ids.ToArray();
        }
        public void UpdatePage(string tab, PageData data)
        {
            if (!TabNames.ContainsKey(tab) || data == null) return;
            cache[tab] = data;
            if (selectedTab == tab) RenderPage(data);
        }
        private void Navigate(string tab)
        {
            if (!TabNames.ContainsKey(tab) || root == null) return;
            selectedTab = tab; reportAwaitingConfirmation = false;
            if (confirmReport != null) confirmReport.style.display = DisplayStyle.None;
            foreach (string name in Tabs)
            {
                Button button = root.Q<Button>("nav-" + name);
                if (button != null)
                {
                    button.RemoveFromClassList("selected");
                    if (name == tab) button.AddToClassList("selected");
                }
            }
            titleLabel.text = TabNames[tab];
            kicker.text = tab == "timeline" ? "TIME RECONSTRUCTION" : tab == "report" ? "REPORT REVIEW" : "CASE RECORD";
            pageDescription.text = tab == "report" ? "혐의 대상, 확보 자료, 입증 경로를 구분해 검토합니다" :
                tab == "timeline" ? "시간이 같아도 서로 다른 기록의 정확도는 다를 수 있습니다" :
                tab == "evidence" ? "자료를 열어 출처와 한계를 확인한 뒤 직접 대조하세요" :
                tab == "interview" ? "인물의 진술은 사실로 확인되기 전까지 주장으로 기록됩니다" :
                "확인된 사실과 추정을 구분해서 기록합니다";
            reportCompose.style.display = tab == "report" ? DisplayStyle.Flex : DisplayStyle.None;
            questionCompose.style.display = tab == "interview" ? DisplayStyle.Flex : DisplayStyle.None;
            settingsCompose.style.display = tab == "settings" ? DisplayStyle.Flex : DisplayStyle.None;
            ClearInspector(); ClearCompare();
            if (cache.TryGetValue(tab, out PageData data)) RenderPage(data);
            else
            {
                content.Clear(); AddInformationalRecord("연결 대기", "아직 자료가 전달되지 않았습니다");
            }
            NavigationRequested?.Invoke(tab);
        }
        private void RenderPage(PageData data)
        {
            content.Clear(); ClearInspector(); ClearCompare();
            int count = data.records == null ? 0 : data.records.Length;
            if (recordCount != null) recordCount.text = count.ToString() + "건";
            if (data.records != null)
            {
                foreach (Record record in data.records)
                {
                    Record captured = record;
                    Button button = new Button(() => SelectRecord(captured));
                    button.AddToClassList("record");
                    Label status = new Label(record.display_status ?? record.status ?? "확인 전");status.AddToClassList("record-header");
                    Label main = new Label(record.title ?? "자료명 없음");main.AddToClassList("record-main");
                    Label foot = new Label(record.provenance ?? "출처 미기록");foot.AddToClassList("record-foot");
                    button.Add(status);button.Add(main);button.Add(foot);
                    content.Add(button);
                }
            }
            if (data.context != null) SetContext(data.context);
            if (!string.IsNullOrEmpty(data.connection)) SetConnection(data.connection);
        }
        private void AddInformationalRecord(string header, string body)
        {
            VisualElement panel = new VisualElement();panel.AddToClassList("record");
            Label head = new Label(header); head.AddToClassList("record-header");
            Label detail = new Label(body); detail.AddToClassList("record-main");
            panel.Add(head);panel.Add(detail);content.Add(panel);
            if (recordCount != null) recordCount.text = "0건";
        }
        private void SelectRecord(Record record)
        {
            selectedRecord = record;
            if (inspectorStatus != null) inspectorStatus.text = record.display_status ?? record.status ?? "자료";
            if (inspectorTitle != null) inspectorTitle.text = record.title ?? "";
            if (inspectorObservation != null) inspectorObservation.text = record.detail ?? "기록된 내용 없음";
            if (inspectorProvenance != null) inspectorProvenance.text = record.provenance ?? "출처 기록 없음";
            if (inspectorLimitation != null) inspectorLimitation.text = record.limitation ?? "현재 표시 가능한 검증 한계 없음";
            // Client can compare a claim with an evidence record but cannot infer guilt
            if (compareButton != null) compareButton.SetEnabled(!string.IsNullOrEmpty(record.id));
        }
        private void ClearInspector()
        {
            selectedRecord = null;
            if (inspectorStatus != null) inspectorStatus.text = "자료를 선택하세요";
            if (inspectorTitle != null) inspectorTitle.text = "";
            if (inspectorObservation != null) inspectorObservation.text = "";
            if (inspectorProvenance != null) inspectorProvenance.text = "";
            if (inspectorLimitation != null) inspectorLimitation.text = "";
            if (compareButton != null) compareButton.SetEnabled(false);
        }
        private void AddSelectedToCompare()
        {
            if (selectedRecord == null || string.IsNullOrEmpty(selectedRecord.id))
            { if (toast != null) toast.text = "비교할 수 있는 자료가 선택되지 않았습니다"; return; }
            if (firstRecord == null || (secondRecord != null))
            {
                firstRecord = selectedRecord; secondRecord = null;
            }
            else if (firstRecord.id != selectedRecord.id)
            {
                secondRecord = selectedRecord;
            }
            else
            {
                if (toast != null) toast.text = "서로 다른 기록 두 건을 선택하세요";
            }
            PaintCompare();
        }
        private void ClearCompare()
        {
            firstRecord = null;secondRecord = null;PaintCompare();
        }
        private void PaintCompare()
        {
            if (compareA != null) compareA.text = firstRecord == null ? "첫 번째 자료를 선택하세요" : firstRecord.title;
            if (compareB != null) compareB.text = secondRecord == null ? "두 번째 자료를 선택하세요" : secondRecord.title;
            if (compareStatus != null) compareStatus.text = secondRecord == null ?
                "두 자료를 고른 뒤 출처와 한계를 직접 비교하세요" :
                "대조 준비됨  /  같은 시각이나 다른 표현만으로 거짓 진술이 확정되지 않습니다";
        }
        private void SubmitQuestion()
        {
            string question = questionField == null ? null : questionField.value?.Trim();
            if (string.IsNullOrWhiteSpace(question)) { if (toast != null) toast.text = "질문을 입력하세요"; return; }
            if (QuestionRequested == null) { if (toast != null) toast.text = "심문 연결을 확인하세요"; return; }
            QuestionRequested.Invoke(question);
            questionField.value = "";
        }
        private void ReviewReport()
        {
            if (FinalReportRequested == null || accusedField == null || accusedField.choices.Count == 0)
            { if (toast != null) toast.text = "지목 대상 또는 사건 연결을 확인하세요"; return; }
            reportAwaitingConfirmation = true;
            confirmReport.style.display = DisplayStyle.Flex;
            Label hint = root.Q<Label>("report-confirm-hint");
            if (hint != null) hint.text = "선택한 대상과 확보·제출 자료를 다시 확인한 뒤 제출하세요";
        }
        private void ConfirmReport()
        {
            if (!reportAwaitingConfirmation) return;
            reportAwaitingConfirmation = false;
            confirmReport.style.display = DisplayStyle.None;
            FinalReportRequested?.Invoke(accusedField.value, SelectedEvidence());
        }
    }
}
