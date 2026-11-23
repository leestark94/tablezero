using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace TableZero
{
    /// <summary>Shared look for the flow screens (menu, HQ desk, report, ending): dark night tones, paper for documents,
    /// one accent. Keeps every screen in the same TABLE INDEX language instead of each scene inventing its own.</summary>
    public static class TZUIKit
    {
        public static readonly Color Bg = new Color(0.035f, 0.045f, 0.055f), Panel = new Color(0.08f, 0.10f, 0.12f, 0.94f),
            Line = new Color(1, 1, 1, 0.10f), Ink = new Color(0.93f, 0.89f, 0.83f), Dim = new Color(0.64f, 0.66f, 0.68f),
            Accent = new Color(0.73f, 0.60f, 0.45f), Paper = new Color(0.90f, 0.86f, 0.78f), PaperInk = new Color(0.13f, 0.16f, 0.17f),
            Warn = new Color(0.78f, 0.64f, 0.48f);

        /// <summary>Active/primary buttons: bright text on a deep amber ground with an amber frame. (Dark text on a light amber fill read as thin grey with this font.)</summary>
        public static readonly Color PrimaryBg = new Color(0.34f, 0.24f, 0.11f), PrimaryInk = new Color(1f, 0.95f, 0.84f);

        public static Label L(string t, int size, Color c, bool bold = false)
        {
            var l = new Label(t); l.style.fontSize = size; l.style.color = c; l.style.whiteSpace = WhiteSpace.Normal;
            if (bold) l.style.unityFontStyleAndWeight = FontStyle.Bold;
            return l;
        }

        public static void Pad(VisualElement e, float v) { e.style.paddingLeft = e.style.paddingRight = e.style.paddingTop = e.style.paddingBottom = v; }
        public static void Radius(VisualElement e, float r) { e.style.borderTopLeftRadius = e.style.borderTopRightRadius = e.style.borderBottomLeftRadius = e.style.borderBottomRightRadius = r; }
        public static void Border(VisualElement e, Color c, float w = 1)
        {
            e.style.borderTopWidth = e.style.borderBottomWidth = e.style.borderLeftWidth = e.style.borderRightWidth = w;
            e.style.borderTopColor = e.style.borderBottomColor = e.style.borderLeftColor = e.style.borderRightColor = c;
        }
        public static void Full(VisualElement e) { e.style.position = Position.Absolute; e.style.left = e.style.right = e.style.top = e.style.bottom = 0; }

        public static VisualElement Box(Color bg)
        {
            var b = new VisualElement(); b.style.backgroundColor = bg; Pad(b, 20); Radius(b, 6); Border(b, Line); return b;
        }

        /// <summary>Button with real states: primary / normal / disabled (disabled shows why, and does nothing).</summary>
        public static Button Btn(string text, Action act, bool primary = false, bool enabled = true, string whyDisabled = null)
        {
            var b = new Button(() => { if (enabled) act?.Invoke(); }) { text = text };
            b.style.fontSize = 17; b.style.height = 46; b.style.marginTop = 6; b.style.marginBottom = 6; b.style.unityTextAlign = TextAnchor.MiddleLeft;
            b.style.paddingLeft = 16; b.style.paddingRight = 16; Radius(b, 5);
            b.style.backgroundColor = primary ? PrimaryBg : new Color(0.11f, 0.14f, 0.17f);
            b.style.color = primary ? PrimaryInk : Ink;
            if (primary) b.style.unityFontStyleAndWeight = FontStyle.Bold;   // active gold buttons must never read as the thin grey 'disabled' look
            Border(b, primary ? Accent : new Color(0.33f, 0.38f, 0.42f), primary ? 2 : 1);
            if (!enabled) { b.style.opacity = 0.42f; b.style.backgroundColor = new Color(0.08f, 0.09f, 0.10f); b.style.color = new Color(0.70f, 0.70f, 0.70f); b.style.unityFontStyleAndWeight = FontStyle.Normal; if (!string.IsNullOrEmpty(whyDisabled)) b.tooltip = whyDisabled; }
            b.RegisterCallback<MouseEnterEvent>(_ => { if (enabled && !primary) b.style.backgroundColor = new Color(0.17f, 0.20f, 0.23f); });
            b.RegisterCallback<MouseLeaveEvent>(_ => { if (enabled && !primary) b.style.backgroundColor = new Color(0.11f, 0.14f, 0.17f); });
            return b;
        }

        /// <summary>Dark input box (UI Toolkit default is a white field that breaks the night palette).</summary>
        public static T DarkInput<T>(T f) where T : TextField
        {
            f.RegisterCallback<AttachToPanelEvent>(_ =>
            {
                var inner = f.Q(className: TextField.inputUssClassName);
                if (inner == null) return;
                inner.style.backgroundColor = new Color(0.05f, 0.07f, 0.08f); inner.style.color = Ink; Border(inner, new Color(0.33f, 0.38f, 0.42f)); Radius(inner, 4);
                inner.style.paddingLeft = 10; inner.style.paddingTop = 6; inner.style.fontSize = 15;
            });
            return f;
        }

        public static VisualElement Divider() { var d = new VisualElement(); d.style.height = 1; d.style.backgroundColor = Line; d.style.marginTop = 14; d.style.marginBottom = 14; return d; }

        public static Label Toast(VisualElement root)
        {
            var t = L("", 15, Ink); t.style.position = Position.Absolute; t.style.right = 28; t.style.bottom = 28; t.style.maxWidth = 460;
            t.style.backgroundColor = new Color(0.12f, 0.16f, 0.19f, 0.96f); Pad(t, 12); Radius(t, 6); Border(t, new Color(0.55f, 0.66f, 0.69f));
            t.style.display = DisplayStyle.None; t.pickingMode = PickingMode.Ignore; root.Add(t); return t;
        }
    }
}
