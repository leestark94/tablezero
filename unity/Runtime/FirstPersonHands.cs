using UnityEngine;

namespace TableZero
{
    // Existing authored first-person arm rig: never synthesizes capsule/sphere hands.
    public class FirstPersonHands : MonoBehaviour
    {
        public Animator handsAnimator;
        public Transform rightHandGrip;
        public Transform leftHandGrip;
        public AudioSource breathingSource;
        public float maxSwayDegrees = 0.6f;
        public string openDoorState = "Hands_OpenDoor";
        public string inspectState = "Hands_Inspect";
        public string flashlightState = "Hands_Flashlight";
        Quaternion rightRest;
        void Awake() { if (rightHandGrip) rightRest = rightHandGrip.localRotation; }
        void LateUpdate()
        {
            if (!rightHandGrip) return;
            float sway = Mathf.Sin(Time.time * 1.3f) * maxSwayDegrees;
            rightHandGrip.localRotation = rightRest * Quaternion.Euler(sway * .45f,0f,sway);
        }
        public bool PlayDoor() => Play(openDoorState);
        public bool PlayInspect() => Play(inspectState);
        public bool PlayFlashlight() => Play(flashlightState);
        bool Play(string state)
        {
            if (!handsAnimator) { Debug.LogWarning("First-person hand rig absent");return false; }
            if (!handsAnimator.HasState(0,Animator.StringToHash(state)))
            { Debug.LogWarning("Missing hand state: " + state);return false; }
            handsAnimator.CrossFadeInFixedTime(state,.12f);
            return true;
        }
    }
}
