using System;
using UnityEngine;

namespace TableZero
{
    public enum TZPropAction { Inspect, Open, Close, Move, Activate, Deactivate }
    public enum TZPropKind { Inspect, Move, EvidenceAnchor, Container, Door, Switch }

    public static class TZDev
    {
        /// <summary>Dev builds may interact with procedural (not art-approved) props. Shipping builds may not.</summary>
        public static bool AllowUnapprovedArt => Application.isEditor || Debug.isDebugBuild;
    }

    /// <summary>
    /// Authoring contract for 302ho. Every human-scale accessible set piece needs its own
    /// persistent propId. This component does NOT synthesize meshes, physical reactions,
    /// fingerprints or case truth. Motion runs only after the server approved the intent.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class TZInspectableProp : MonoBehaviour
    {
        [Header("Catalog contract")]
        public string propId;
        public string KoreanLabel;
        public TZPropKind kind;
        public float interactionDistanceMeters = 1.75f;
        public bool artApproved;
        public bool contactAnimationApproved;
        public bool gameplayAvailable = true;
        [Tooltip("Asset status mirrored from data/asset_verification.json")]
        public string artStatus = "UNASSIGNED_NEEDS_QUALITY_ASSET";
        [Header("Bindings must be authored, never generated from primitives")]
        public Collider interactionCollider;
        public Animator authoredAnimator;
        public TZPropMotion motion;
        public Transform handContactTarget;
        public string openTrigger = "Open";
        public string closeTrigger = "Close";
        public string switchOnTrigger = "SwitchOn";
        public string switchOffTrigger = "SwitchOff";
        [Header("Switch targets (lights/water) toggled after approval")]
        public Behaviour[] switchTargets;
        public GameObject[] switchObjects;
        [Header("Scene relationships")]
        public TZInspectableProp parentContainer;
        [Tooltip("Small enough to pick up and turn over in the hands")]
        public bool handheld;
        // Inspect callback to actual case backend
        public event Action<TZInspectableProp, TZPropAction> OnInteractionRequested;
        public bool isOpen { get; private set; }
        public bool isActive { get; private set; }
        [Tooltip("Initial switch state; must match server/case_flow.py INITIAL_ACTIVE")]
        public bool startActive;
        [Tooltip("Initial open state; must match server/case_flow.py INITIAL_OPEN")]
        public bool startOpen;

        void Start()
        {
            if (startActive) isActive = true;
            if (startOpen) { isOpen = true; if (motion) motion.SnapPartial(0.62f); }
            if (switchTargets != null) foreach (var b in switchTargets) if (b) b.enabled = isActive;
            if (switchObjects != null) foreach (var g in switchObjects) if (g) g.SetActive(isActive);
        }

        public bool CanTarget()
        {
            return gameplayAvailable && interactionCollider && (artApproved || TZDev.AllowUnapprovedArt) &&
                   (parentContainer == null || parentContainer.isOpen);
        }

        public TZPropAction PrimaryAction()
        {
            switch (kind)
            {
                case TZPropKind.Container:
                case TZPropKind.Door: return isOpen ? TZPropAction.Close : TZPropAction.Open;
                case TZPropKind.Switch: return isActive ? TZPropAction.Deactivate : TZPropAction.Activate;
                case TZPropKind.Move: return TZPropAction.Move;
                default: return TZPropAction.Inspect;
            }
        }

        public bool TryRequest(TZPropAction action)
        {
            if (!CanTarget()) return false;
            bool rigged = action == TZPropAction.Open || action == TZPropAction.Close;
            if (rigged && !authoredAnimator && !motion) return false;
            if ((action == TZPropAction.Open || action == TZPropAction.Close) &&
                kind != TZPropKind.Container && kind != TZPropKind.Door) return false;
            if ((action == TZPropAction.Activate || action == TZPropAction.Deactivate) && kind != TZPropKind.Switch) return false;
            if (action == TZPropAction.Move && kind != TZPropKind.Move) return false;
            if (action == TZPropAction.Open && isOpen) return false;
            if (action == TZPropAction.Close && !isOpen) return false;
            if (action == TZPropAction.Activate && isActive) return false;
            if (action == TZPropAction.Deactivate && !isActive) return false;
            if (motion && motion.Moving) return false;
            // Server must authorize actual mutation. No subscriber means no action.
            if (OnInteractionRequested == null) return false;
            OnInteractionRequested.Invoke(this, action);
            return true;
        }

        /// <summary>Call ONLY with a server-approved result.</summary>
        public void ApplyServerApproved(TZPropAction action)
        {
            if (authoredAnimator)
            {
                if (action == TZPropAction.Open) authoredAnimator.SetTrigger(openTrigger);
                if (action == TZPropAction.Close) authoredAnimator.SetTrigger(closeTrigger);
                if (action == TZPropAction.Activate) authoredAnimator.SetTrigger(switchOnTrigger);
                if (action == TZPropAction.Deactivate) authoredAnimator.SetTrigger(switchOffTrigger);
            }
            if (motion)
            {
                if (action == TZPropAction.Open || action == TZPropAction.Activate && motion.kind != TZMotionKind.None) motion.Play(true);
                if (action == TZPropAction.Close || action == TZPropAction.Deactivate && motion.kind != TZMotionKind.None) motion.Play(false);
            }
            if (action == TZPropAction.Open) isOpen = true;
            if (action == TZPropAction.Close) isOpen = false;
            if (action == TZPropAction.Activate) isActive = true;
            if (action == TZPropAction.Deactivate) isActive = false;
            if (action == TZPropAction.Activate || action == TZPropAction.Deactivate)
            {
                if (switchTargets != null) foreach (var b in switchTargets) if (b) b.enabled = isActive;
                if (switchObjects != null) foreach (var g in switchObjects) if (g) g.SetActive(isActive);
            }
        }

        private void OnValidate()
        {
            interactionDistanceMeters = Mathf.Clamp(interactionDistanceMeters, .6f, 2.8f);
            if (!interactionCollider) interactionCollider = GetComponent<Collider>();
            if (!motion) motion = GetComponent<TZPropMotion>();
        }
    }
}
