using System;
using UnityEngine;

namespace TableZero
{
    public enum TZPropAction { Inspect, Open, Close, Move, Activate, Deactivate }
    public enum TZPropKind { Inspect, Move, EvidenceAnchor, Container, Door, Switch }

    /// <summary>
    /// Authoring contract for 302ho. Every human-scale accessible set piece needs its own
    /// persistent propId. This component does NOT synthesize meshes, physical reactions,
    /// fingerprints or case truth. Actual animations and contact require explicit assets.
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
        [Header("Bindings must be authored, never generated from primitives")]
        public Collider interactionCollider;
        public Animator authoredAnimator;
        public Transform handContactTarget;
        public string openTrigger = "Open";
        public string closeTrigger = "Close";
        public string switchOnTrigger = "SwitchOn";
        public string switchOffTrigger = "SwitchOff";
        [Header("Scene relationships")]
        public TZInspectableProp parentContainer;
        [Header("Inspect callback to actual case backend")]
        public event Action<TZInspectableProp,TZPropAction> OnInteractionRequested;
        public bool isOpen { get; private set; }
        public bool isActive { get; private set; }

        public bool CanTarget()
        {
            return gameplayAvailable && interactionCollider && artApproved &&
                   (parentContainer == null || parentContainer.isOpen);
        }
        public bool TryRequest(TZPropAction action)
        {
            if (!CanTarget()) return false;
            bool rigged = action == TZPropAction.Open || action == TZPropAction.Close ||
                          action == TZPropAction.Activate || action == TZPropAction.Deactivate ||
                          action == TZPropAction.Move;
            if (rigged && (!authoredAnimator || !contactAnimationApproved || !handContactTarget)) return false;
            if ((action == TZPropAction.Open || action == TZPropAction.Close) &&
                kind != TZPropKind.Container && kind != TZPropKind.Door) return false;
            if ((action == TZPropAction.Activate || action == TZPropAction.Deactivate) && kind != TZPropKind.Switch) return false;
            if (action == TZPropAction.Move && kind != TZPropKind.Move) return false;
            if (action == TZPropAction.Open && isOpen) return false;
            if (action == TZPropAction.Close && !isOpen) return false;
            if (action == TZPropAction.Activate && isActive) return false;
            if (action == TZPropAction.Deactivate && !isActive) return false;
            // Server must authorize actual mutation. No subscriber means no action.
            if (OnInteractionRequested == null) return false;
            OnInteractionRequested.Invoke(this,action);
            return true;
        }
        public void ApplyServerApproved(TZPropAction action)
        {
            if (!CanTarget()) return;
            if (authoredAnimator)
            {
                if (action == TZPropAction.Open) authoredAnimator.SetTrigger(openTrigger);
                if (action == TZPropAction.Close) authoredAnimator.SetTrigger(closeTrigger);
                if (action == TZPropAction.Activate) authoredAnimator.SetTrigger(switchOnTrigger);
                if (action == TZPropAction.Deactivate) authoredAnimator.SetTrigger(switchOffTrigger);
            }
            if (action == TZPropAction.Open) isOpen = true;
            if (action == TZPropAction.Close) isOpen = false;
            if (action == TZPropAction.Activate) isActive = true;
            if (action == TZPropAction.Deactivate) isActive = false;
        }
        private void OnValidate()
        {
            interactionDistanceMeters = Mathf.Clamp(interactionDistanceMeters,.6f,2.8f);
            if (!interactionCollider) interactionCollider = GetComponent<Collider>();
        }
    }
}
