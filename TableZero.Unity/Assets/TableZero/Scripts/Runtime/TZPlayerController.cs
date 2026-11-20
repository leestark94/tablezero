using UnityEngine;
using UnityEngine.InputSystem;

namespace TableZero
{
    /// <summary>
    /// First-person investigator body. Walk pace is a detective at a scene, not a shooter.
    /// The camera always belongs to the player: no forced look, head bob is tiny and can be disabled.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public sealed class TZPlayerController : MonoBehaviour
    {
        public Camera cam;
        public Light flashlight;
        public float walkSpeed = 1.35f, slowSpeed = 0.7f, crouchSpeed = 0.55f;
        public float standEye = 1.62f, crouchEye = 1.05f;
        public float mouseSensitivity = 0.075f;
        public bool reduceMotion = false;
        public bool inputLocked;
        public AudioSource footsteps;
        public AudioClip[] stepClips;

        CharacterController cc;
        float pitch, yaw, vy, bobT, stepDist;
        float eye;
        public bool Crouching { get; private set; }

        void Awake()
        {
            cc = GetComponent<CharacterController>();
            eye = standEye;
            yaw = transform.eulerAngles.y;
            if (cam) pitch = cam.transform.localEulerAngles.x > 180 ? cam.transform.localEulerAngles.x - 360 : cam.transform.localEulerAngles.x;
        }

        void OnEnable() { SetCursor(true); }

        /// <summary>Place the investigator (save/load, QA capture rigs). Not used for cinematic camera theft.</summary>
        public void Place(Vector3 feet, float yawDeg, float pitchDeg)
        {
            cc = cc ? cc : GetComponent<CharacterController>();
            cc.enabled = false; transform.position = feet; cc.enabled = true;
            yaw = yawDeg; pitch = pitchDeg; vy = 0;
            transform.rotation = Quaternion.Euler(0, yaw, 0);
            if (cam) cam.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
        }
        public void SetCursor(bool locked)
        {
            Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !locked;
        }

        void Update()
        {
            var kb = Keyboard.current; var mouse = Mouse.current;
            if (kb == null || mouse == null) return;
            if (!inputLocked)
            {
                Vector2 d = mouse.delta.ReadValue() * mouseSensitivity;
                yaw += d.x; pitch = Mathf.Clamp(pitch - d.y, -82f, 82f);
                transform.rotation = Quaternion.Euler(0, yaw, 0);
                if (kb.fKey.wasPressedThisFrame && flashlight) flashlight.enabled = !flashlight.enabled;
                if (kb.leftCtrlKey.wasPressedThisFrame || kb.cKey.wasPressedThisFrame && kb.leftShiftKey.isPressed) Crouching = !Crouching;
            }
            Vector2 mv = Vector2.zero;
            if (!inputLocked)
            {
                if (kb.wKey.isPressed) mv.y += 1; if (kb.sKey.isPressed) mv.y -= 1;
                if (kb.dKey.isPressed) mv.x += 1; if (kb.aKey.isPressed) mv.x -= 1;
            }
            float speed = Crouching ? crouchSpeed : (kb.leftShiftKey.isPressed ? slowSpeed : walkSpeed);
            Vector3 wish = (transform.right * mv.x + transform.forward * mv.y);
            wish = Vector3.ClampMagnitude(wish, 1f) * speed;
            if (cc.isGrounded && vy < 0) vy = -1f;
            vy += -9.81f * Time.deltaTime;
            wish.y = vy;
            cc.Move(wish * Time.deltaTime);

            // crouch: lower eye + capsule smoothly
            float targetEye = Crouching ? crouchEye : standEye;
            eye = Mathf.MoveTowards(eye, targetEye, Time.deltaTime * 1.6f);
            cc.height = Mathf.Max(0.9f, eye + 0.13f);
            cc.center = new Vector3(0, cc.height / 2f, 0);

            // tiny bob only while walking
            float planar = new Vector2(wish.x, wish.z).magnitude;
            if (planar > 0.1f && cc.isGrounded) { bobT += Time.deltaTime * planar * 5.2f; stepDist += planar * Time.deltaTime; }
            float bob = reduceMotion ? 0f : Mathf.Sin(bobT * 2f) * 0.006f * Mathf.Clamp01(planar);
            if (cam)
            {
                cam.transform.localPosition = new Vector3(0, eye + bob, 0);
                cam.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
            }
            if (stepDist > 0.62f)
            {
                stepDist = 0;
                if (footsteps && stepClips != null && stepClips.Length > 0)
                    footsteps.PlayOneShot(stepClips[Random.Range(0, stepClips.Length)], Crouching ? 0.25f : 0.5f);
            }
        }
    }
}
