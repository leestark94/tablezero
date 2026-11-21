using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Real 3D 진술녹화실 that replaces the waiting-room photo once the detective walks in.
    /// Holds the detective camera (seated eye height), the suspect seat anchor and the room's single reflection probe
    /// (rendered once after lights settle — per-frame probe refresh was the main frame-time cost measured in 302).
    /// A suspect is "present in 3D" only when a rigged character is registered for that id; otherwise the interrogation
    /// screen keeps the approved 2D shot and the gap stays recorded as incomplete (never an empty chair passed off as done).
    /// </summary>
    public sealed class TZInterrogationRoom3D : MonoBehaviour
    {
        public static TZInterrogationRoom3D Instance { get; private set; }

        public Camera detectiveCamera;
        public Transform suspectSeat;            // seat-surface centre of the suspect chair, +Z facing the detective
        public ReflectionProbe probe;
        [Tooltip("Dev only: show the 3D room even when the called suspect has no rigged character yet (empty chair).")]
        public bool previewWithoutCharacter;
        [System.Serializable] public class Cast { public string suspectId; public GameObject character; }
        public Cast[] cast = new Cast[0];

        Vector3 camBasePos; Quaternion camBaseRot; float shownAt = -1f; GameObject activeCharacter;

        void Awake()
        {
            Instance = this;
            if (detectiveCamera) { camBasePos = detectiveCamera.transform.localPosition; camBaseRot = detectiveCamera.transform.localRotation; }
            foreach (var c in cast) if (c.character) c.character.SetActive(false);
            if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-tzroompreview") >= 0) previewWithoutCharacter = true;
        }

        System.Collections.IEnumerator Start()
        {
            yield return null; yield return null;            // lights + materials uploaded
            if (probe) { probe.refreshMode = UnityEngine.Rendering.ReflectionProbeRefreshMode.ViaScripting; probe.RenderProbe(); }
        }

        public bool HasCharacter(string id)
        {
            foreach (var c in cast) if (c.suspectId == id && c.character) return true;
            return false;
        }

        /// <summary>True when the 3D room should be shown for this suspect (real character, or the explicit dev preview).</summary>
        public bool CanShow(string id) => HasCharacter(id) || previewWithoutCharacter;

        public void Show(string id)
        {
            foreach (var c in cast) if (c.character) c.character.SetActive(c.suspectId == id);
            activeCharacter = null;
            foreach (var c in cast) if (c.suspectId == id) activeCharacter = c.character;
            shownAt = Time.time;
        }

        public void Hide()
        {
            foreach (var c in cast) if (c.character) c.character.SetActive(false);
            activeCharacter = null; shownAt = -1f;
        }

        /// <summary>Seated detective's head: slow breathing rise + tiny postural drift (no shake, no bob while typing).</summary>
        void LateUpdate()
        {
            if (!detectiveCamera || shownAt < 0) return;
            float t = Time.time;
            float breathe = Mathf.Sin(t * 2f * Mathf.PI / 4.6f);
            var p = camBasePos + new Vector3((Mathf.PerlinNoise(t * 0.07f, 3f) - 0.5f) * 0.012f, breathe * 0.0035f, 0f);
            detectiveCamera.transform.localPosition = p;
            detectiveCamera.transform.localRotation = camBaseRot * Quaternion.Euler((Mathf.PerlinNoise(t * 0.05f, 9f) - 0.5f) * 0.5f,
                                                                                     (Mathf.PerlinNoise(t * 0.04f, 1f) - 0.5f) * 0.7f, 0f);
        }

        /// <summary>Entry move: camera starts standing at the door side and settles into the seated position.</summary>
        public System.Collections.IEnumerator SitDown(float seconds)
        {
            if (!detectiveCamera) yield break;
            var tr = detectiveCamera.transform;
            Vector3 from = camBasePos + new Vector3(-0.32f, 0.42f, 0.38f);
            Quaternion fromR = camBaseRot * Quaternion.Euler(9f, -14f, 0f);
            float t = 0; shownAt = -1f;
            while (t < seconds)
            {
                t += Time.unscaledDeltaTime; float k = Mathf.SmoothStep(0, 1, Mathf.Clamp01(t / seconds));
                float settle = Mathf.Sin(Mathf.Clamp01(t / seconds) * Mathf.PI) * 0.012f;   // weight going into the chair
                tr.localPosition = Vector3.Lerp(from, camBasePos, k) + Vector3.down * settle;
                tr.localRotation = Quaternion.Slerp(fromR, camBaseRot, k);
                yield return null;
            }
            shownAt = Time.time;
        }
    }
}
