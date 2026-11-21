using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Yellow numbered evidence tents. The SERVER issues the number (order of first photograph); the client only
    /// places the matching template beside the photographed object, on the surface under it, facing the detective.
    /// Every photographed object gets one, so a marker never signals relevance.
    /// </summary>
    public sealed class TZEvidenceMarkers : MonoBehaviour
    {
        public static TZEvidenceMarkers I { get; private set; }
        public GameObject[] kit;                     // kit_marker_01 .. kit_marker_NN (inactive templates)
        readonly Dictionary<string, GameObject> placed = new Dictionary<string, GameObject>();
        Transform root;

        void Awake() { I = this; root = new GameObject("PlacedMarkers").transform; }

        public bool Has(string propId) => placed.ContainsKey(propId);

        public GameObject Place(int number, TZInspectableProp prop, Vector3 viewer)
        {
            if (prop == null || number < 1 || kit == null || number > kit.Length || placed.ContainsKey(prop.propId)) return null;
            var rs = prop.GetComponentsInChildren<Renderer>();
            if (rs.Length == 0) return null;
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
            Vector3 toViewer = viewer - b.center; toViewer.y = 0;
            if (toViewer.sqrMagnitude < 1e-4f) toViewer = Vector3.forward;
            toViewer.Normalize();
            float reach = Mathf.Min(Mathf.Max(b.extents.x, b.extents.z), 0.5f) + 0.07f;
            Vector3 side = Vector3.Cross(Vector3.up, toViewer);
            Vector3 c0 = b.center + toViewer * reach;
            // try in front of the object, then to either side; first surface that is roughly horizontal wins
            foreach (var cand in new[] { c0, c0 + side * 0.12f, c0 - side * 0.12f })
            {
                if (!Ground(cand, Mathf.Min(b.max.y + 0.25f, 2.0f), prop.transform, out var hit)) continue;
                var pos = hit.point;
                foreach (var m in placed.Values) if (m && (m.transform.position - pos).sqrMagnitude < 0.09f * 0.09f) pos += side * 0.09f;
                var go = Instantiate(kit[number - 1], pos, Quaternion.LookRotation(-toViewer, Vector3.up), root);
                go.name = $"EvidenceMarker_{number:00}_{prop.propId}";
                go.SetActive(true);
                placed[prop.propId] = go;
                return go;
            }
            return null;
        }

        static bool Ground(Vector3 at, float fromY, Transform ignore, out RaycastHit best)
        {
            best = default;
            var hits = Physics.RaycastAll(new Vector3(at.x, fromY, at.z), Vector3.down, fromY + 1f, ~0, QueryTriggerInteraction.Ignore);
            float bestD = float.MaxValue;
            foreach (var h in hits)
            {
                if (h.transform.IsChildOf(ignore) || h.normal.y < 0.75f) continue;
                if (h.distance < bestD) { bestD = h.distance; best = h; }
            }
            return bestD < float.MaxValue;
        }
    }
}
