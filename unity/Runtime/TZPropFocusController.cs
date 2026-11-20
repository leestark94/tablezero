using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Connect Interact() to Input System actions in the real project.
    /// Hover/outline is intentionally not automatic; live UI decides which subtle cue to show.
    /// Raycast remains local UX. The authoritative server must separately validate action.
    /// </summary>
    public sealed class TZPropFocusController : MonoBehaviour
    {
        public Camera firstPersonCamera;
        public LayerMask propLayers = ~0;
        public float rayLengthMeters = 2.1f;
        public bool inputEnabled = true;
        public System.Action<TZInspectableProp> OnTargetChanged;
        public TZInspectableProp Current { get; private set; }

        void Update()
        {
            TZInspectableProp next = null;
            if (inputEnabled && firstPersonCamera &&
                Physics.Raycast(firstPersonCamera.transform.position,
                                firstPersonCamera.transform.forward, out RaycastHit hit,
                                rayLengthMeters,propLayers,QueryTriggerInteraction.Ignore))
            {
                var candidate = hit.collider.GetComponentInParent<TZInspectableProp>();
                if (candidate && candidate.CanTarget() && hit.distance <= candidate.interactionDistanceMeters)
                    next = candidate;
            }
            if (Current == next) return;
            Current = next;
            OnTargetChanged?.Invoke(Current);
        }
        public bool Interact(TZPropAction action)
        {
            return inputEnabled && Current != null && Current.TryRequest(action);
        }
    }
}
