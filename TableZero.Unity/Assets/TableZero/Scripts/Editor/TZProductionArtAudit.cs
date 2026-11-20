#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace TableZero.Editor
{
    // Art director's read-only quality gate. It never edits or creates replacement objects.
    public static class TZProductionArtAudit
    {
        static readonly HashSet<string> ForbiddenMeshNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {"Cube", "Sphere", "Capsule", "Cylinder", "Plane", "Quad"};
        [MenuItem("Tools/TABLE ZERO/Audit Active Scene Art")]
        public static void Audit()
        {
            int critical=0, warning=0;
            Scene scene=SceneManager.GetActiveScene();
            foreach(GameObject root in scene.GetRootGameObjects())
            {
                foreach(MeshFilter filter in root.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (!filter.sharedMesh) { Debug.LogError("Missing mesh on " + filter.name); critical++; continue; }
                    if (ForbiddenMeshNames.Contains(filter.sharedMesh.name))
                    {
                        Debug.LogError("PREVIEW PRIMITIVE IN PRODUCTION SCENE: " + filter.name,filter);critical++;
                    }
                    if (filter.name.ToUpperInvariant().Contains("TEMP") || filter.name.ToUpperInvariant().Contains("PLACEHOLDER"))
                    {
                        Debug.LogError("TEMP ASSET DETECTED: " + filter.name,filter);critical++;
                    }
                }
                foreach(Renderer renderer in root.GetComponentsInChildren<Renderer>(true))
                {
                    if (renderer.sharedMaterials.Length==0) {Debug.LogWarning("No material " + renderer.name);warning++;}
                    foreach(Material material in renderer.sharedMaterials)
                        if (material==null){Debug.LogError("MISSING MATERIAL " + renderer.name,renderer);critical++;}
                }
                foreach(Animator animator in root.GetComponentsInChildren<Animator>(true))
                {
                    if (!animator.runtimeAnimatorController)
                    { Debug.LogWarning("Unbound animator " + animator.name,animator); warning++; }
                }
                foreach(TZPerformanceManifest manifest in root.GetComponentsInChildren<TZPerformanceManifest>(true))
                {
                    manifest.LogMissing();
                    foreach(var entry in manifest.entries)
                        if(entry!=null && !manifest.IsReady(entry.id))critical++;
                }
            }
            Debug.Log($"TABLE ZERO ART GATE: critical={critical} warning={warning} scene={scene.name}\n"+
                "This is only a structural audit; photorealism and cultural authenticity still require screenshot review");
        }
    }
}
#endif
