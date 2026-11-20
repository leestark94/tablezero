#if UNITY_EDITOR
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Manual run after every import: Tools/TableZero/Audit scene interactions.
    /// Materials and animations are NOT visually judged by this scanner.
    /// Scene review must also catch renderers that have no registered prop parent.
    /// </summary>
    public static class TZPropCoverageAudit
    {
        [MenuItem("Tools/TableZero/Audit scene interactions")]
        public static void Audit()
        {
            var props = Object.FindObjectsByType<TZInspectableProp>(FindObjectsSortMode.None);
            var ids = new HashSet<string>();
            int fail=0;
            foreach(var p in props)
            {
                if (string.IsNullOrWhiteSpace(p.propId) || !ids.Add(p.propId))
                {
                    Debug.LogError("[TABLEZERO] Missing or duplicate prop ID: "+p.name,p);
                    fail++;
                }
                if (!p.interactionCollider || !p.artApproved)
                {
                    Debug.LogError("[TABLEZERO] Prop lacks verified collider/art: "+p.propId,p);
                    fail++;
                }
                if (p.kind != TZPropKind.Inspect && p.kind != TZPropKind.EvidenceAnchor)
                {
                    if (!p.handContactTarget || !p.authoredAnimator || !p.contactAnimationApproved)
                    {
                        Debug.LogError("[TABLEZERO] No real hand/interaction motion: "+p.propId,p);
                        fail++;
                    }
                }
            }
            // This cannot know which surfaces are structural or intentional. It flags
            // unbound geometry for human review; exempt documented architecture only.
            var unbound = Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None)
                .Where(x => x.gameObject.activeInHierarchy && x.GetComponentInParent<TZInspectableProp>() == null).ToArray();
            foreach (var r in unbound)
                Debug.LogWarning("[TABLEZERO] Renderer needs prop binding or explicit architectural exemption: "+r.name,r);
            Debug.Log($"[TABLEZERO] {props.Length} registered props; errors={fail}; unbound meshes={unbound.Length}. Compare all IDs against room302_interaction_manifest.json", 
                      props.Length>0 ? props[0] : null);
        }
    }
}
#endif
