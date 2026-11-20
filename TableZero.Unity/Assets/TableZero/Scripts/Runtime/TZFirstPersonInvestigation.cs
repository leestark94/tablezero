using System;
using UnityEngine;

namespace TableZero
{
    // Require properly rigged 1P arms. Hand animations and objects must be authored in Blender/Unity.
    // Camera aim uses player control; no forced cinematic camera cuts during inspection.
    public sealed class TZFirstPersonInvestigation : MonoBehaviour
    {
        public Camera playerCamera;
        public CharacterController characterController;
        public FirstPersonHands hands;
        public FirstPersonEvidenceInteractor evidenceInteractor;
        public Animator bodyAnimator;
        public AudioSource foley;
        public AudioClip shoeCoverStep;
        public AudioClip clothShift;
        public LayerMask obstacleMask;
        public float walkSpeed = 1.85f;
        public float lookSensitivity = 0.09f;
        public float inspectedWalkSpeed = 0f;
        public float gravity = -9.81f;
        public float maxHeadBobMeters = .003f;
        public bool reduceMotion = false;
        public bool gameplayInputEnabled = true;
        public Action<string> OnInspectEvidence;
        private float verticalVelocity;
        private float pitch;
        private Vector3 cameraRest;
        private bool evidenceInHands;
        private float stepDistance;

        private void Awake()
        {
            if (playerCamera) cameraRest = playerCamera.transform.localPosition;
            if (evidenceInteractor != null)
                evidenceInteractor.OnEvidenceInspected += EvidenceInspected;
        }
        private void OnDestroy()
        {
            if (evidenceInteractor != null)
                evidenceInteractor.OnEvidenceInspected -= EvidenceInspected;
        }
        private void EvidenceInspected(string id)
        {
            evidenceInHands = true;
            if (hands) hands.PlayInspect();
            OnInspectEvidence?.Invoke(id);
        }
        public void Move(Vector2 axes)
        {
            if (!gameplayInputEnabled || !characterController || evidenceInHands) return;
            Vector3 wish = transform.right * axes.x + transform.forward * axes.y;
            wish = Vector3.ClampMagnitude(wish, 1);
            Vector3 motion = wish * walkSpeed;
            if (characterController.isGrounded && verticalVelocity < 0f) verticalVelocity = -1f;
            verticalVelocity += gravity * Time.deltaTime;
            motion.y = verticalVelocity;
            characterController.Move(motion * Time.deltaTime);
            if (axes.sqrMagnitude > .2f && characterController.isGrounded)
            {
                stepDistance += walkSpeed * Time.deltaTime;
                if (stepDistance > 1.3f)
                {
                    stepDistance = 0;
                    if (foley && shoeCoverStep) foley.PlayOneShot(shoeCoverStep, .45f);
                }
            }
        }
        public void Look(Vector2 delta)
        {
            if (!gameplayInputEnabled || !playerCamera || evidenceInHands) return;
            transform.Rotate(0f, delta.x * lookSensitivity, 0f);
            pitch = Mathf.Clamp(pitch - delta.y * lookSensitivity, -77f, 77f);
            playerCamera.transform.localEulerAngles = new Vector3(pitch, 0, 0);
        }
        public bool Inspect()
        {
            if (!gameplayInputEnabled || !evidenceInteractor) return false;
            return evidenceInteractor.TryInspect();
        }
        public void RotateEvidence(Vector2 delta)
        {
            if (evidenceInHands && evidenceInteractor) evidenceInteractor.RotateHeld(delta);
        }
        public void CloseEvidence()
        {
            if (!evidenceInHands) return;
            if (evidenceInteractor) evidenceInteractor.Release();
            evidenceInHands = false;
        }
        public void SetFocusUI(bool focused)
        {
            gameplayInputEnabled = !focused;
            if (focused) CloseEvidence();
        }
        private void LateUpdate()
        {
            if (!playerCamera || reduceMotion) return;
            // No procedural body/character movement replacement; tiny visual settling only
            // Rotational camera is never overridden because that would fight player input
            if (characterController && characterController.isGrounded && !evidenceInHands && gameplayInputEnabled)
            {
                Vector3 p=playerCamera.transform.localPosition;
                float bob=Mathf.Sin(Time.time * 7.5f) * maxHeadBobMeters;
                p.y = Mathf.Lerp(p.y, cameraRest.y + bob, Time.deltaTime * 8f);
                playerCamera.transform.localPosition=p;
            }
        }
    }
}
