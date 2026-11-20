using System.Collections;
using UnityEngine;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>
    /// Scene-first HUD (V11 §7 state A/B): almost nothing on screen. A faint dot appears only when an
    /// object is reachable; the object's name and the verbs appear low and small; observations read like
    /// subtitles. No percentages, no red answer highlight, no lightning-skill cards.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class TZHud : MonoBehaviour
    {
        public FontAsset koreanFont;
        public FontAsset documentFont;
        public bool showDevBadge = true;
        public string devBadgeText = "DEV BUILD · 절차적 1차 에셋 · 최종 아트 아님";

        VisualElement root, dot, promptBox, subtitleBox, toastBox;
        Label promptName, promptVerbs, subtitle, toast, badge, clock;
        Coroutine subCo, toastCo;

        public static TZHud I { get; private set; }

        void OnEnable()
        {
            I = this;
            var doc = GetComponent<UIDocument>();
            root = doc.rootVisualElement;
            root.Clear();
            root.style.flexGrow = 1;
            if (koreanFont) root.style.unityFontDefinition = FontDefinition.FromSDFFont(koreanFont);
            root.pickingMode = PickingMode.Ignore;

            dot = new VisualElement { pickingMode = PickingMode.Ignore };
            dot.style.position = Position.Absolute; dot.style.left = Length.Percent(50); dot.style.top = Length.Percent(50);
            dot.style.width = 4; dot.style.height = 4; dot.style.marginLeft = -2; dot.style.marginTop = -2;
            SetRadius(dot, 2); dot.style.backgroundColor = new Color(1, 1, 1, 0.0f);
            root.Add(dot);

            promptBox = new VisualElement { pickingMode = PickingMode.Ignore };
            promptBox.style.position = Position.Absolute; promptBox.style.left = 0; promptBox.style.right = 0;
            promptBox.style.top = Length.Percent(60); promptBox.style.alignItems = Align.Center; promptBox.style.opacity = 0;
            promptName = MkLabel(21, new Color(0.95f, 0.94f, 0.90f, 0.96f));
            promptVerbs = MkLabel(15, new Color(0.86f, 0.86f, 0.83f, 0.85f));
            promptVerbs.style.marginTop = 4; promptVerbs.style.letterSpacing = 1;
            promptBox.Add(promptName); promptBox.Add(promptVerbs);
            root.Add(promptBox);

            subtitleBox = new VisualElement { pickingMode = PickingMode.Ignore };
            subtitleBox.style.position = Position.Absolute; subtitleBox.style.left = Length.Percent(18); subtitleBox.style.right = Length.Percent(18);
            subtitleBox.style.bottom = Length.Percent(9); subtitleBox.style.alignItems = Align.Center; subtitleBox.style.opacity = 0;
            subtitle = MkLabel(21, new Color(0.96f, 0.95f, 0.92f, 1));
            subtitle.style.whiteSpace = WhiteSpace.Normal; subtitle.style.unityTextAlign = TextAnchor.MiddleCenter;
            subtitleBox.Add(subtitle);
            root.Add(subtitleBox);

            toastBox = new VisualElement { pickingMode = PickingMode.Ignore };
            toastBox.style.position = Position.Absolute; toastBox.style.right = 36; toastBox.style.top = 30; toastBox.style.opacity = 0;
            toast = MkLabel(14, new Color(0.85f, 0.84f, 0.80f, 0.85f));
            toastBox.Add(toast); root.Add(toastBox);

            clock = MkLabel(13, new Color(0.8f, 0.8f, 0.78f, 0.55f));
            clock.style.position = Position.Absolute; clock.style.left = 36; clock.style.top = 30; clock.style.opacity = 0;
            root.Add(clock);

            if (showDevBadge)
            {
                badge = MkLabel(13, new Color(1f, 0.85f, 0.4f, 0.55f));
                badge.text = devBadgeText;
                badge.style.position = Position.Absolute; badge.style.left = 18; badge.style.bottom = 12;
                root.Add(badge);
            }
        }

        static void SetRadius(VisualElement e, float r)
        {
            e.style.borderTopLeftRadius = r; e.style.borderTopRightRadius = r;
            e.style.borderBottomLeftRadius = r; e.style.borderBottomRightRadius = r;
        }

        Label MkLabel(int size, Color c)
        {
            var l = new Label { pickingMode = PickingMode.Ignore };
            l.style.fontSize = size; l.style.color = c;
            l.style.textShadow = new TextShadow { offset = new Vector2(0, 1), blurRadius = 3, color = new Color(0, 0, 0, 0.85f) };
            return l;
        }

        public void SetFocus(string name, string verbs)
        {
            bool on = !string.IsNullOrEmpty(name);
            dot.style.backgroundColor = new Color(1, 1, 1, on ? 0.55f : 0.0f);
            promptBox.style.opacity = on ? 1 : 0;
            promptName.text = name ?? "";
            promptVerbs.text = verbs ?? "";
        }

        public void ShowSubtitle(string text, float seconds = 4.5f)
        {
            if (subCo != null) StopCoroutine(subCo);
            subCo = StartCoroutine(Fade(subtitleBox, subtitle, text, seconds));
        }
        public void Toast(string text, float seconds = 3f)
        {
            if (toastCo != null) StopCoroutine(toastCo);
            toastCo = StartCoroutine(Fade(toastBox, toast, text, seconds));
        }
        public void SetClock(string text, bool visible) { clock.text = text; clock.style.opacity = visible ? 1 : 0; }

        IEnumerator Fade(VisualElement box, Label l, string text, float seconds)
        {
            l.text = text;
            for (float t = 0; t < 1; t += Time.unscaledDeltaTime * 5f) { box.style.opacity = t; yield return null; }
            box.style.opacity = 1;
            yield return new WaitForSecondsRealtime(seconds);
            for (float t = 1; t > 0; t -= Time.unscaledDeltaTime * 2.5f) { box.style.opacity = t; yield return null; }
            box.style.opacity = 0;
        }
    }
}
