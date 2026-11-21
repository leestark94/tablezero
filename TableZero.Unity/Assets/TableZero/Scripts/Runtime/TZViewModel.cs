using UnityEngine;
using UnityEngine.InputSystem;

namespace TableZero
{
    /// <summary>First-person view model (the detective's right hand + flashlight): lags the look a little,
    /// bobs with walking, and lowers slightly while examining. Purely presentational; no gameplay authority.</summary>
    public sealed class TZViewModel : MonoBehaviour
    {
        public Vector3 restPosition;
        public Vector3 restEuler;
        public float swayAmount = 0.012f, swaySmooth = 9f, bobAmount = 0.008f;
        Vector3 sway; float bobT;
        CharacterController cc;

        void Start() { cc = GetComponentInParent<CharacterController>(); transform.localPosition = restPosition; transform.localRotation = Quaternion.Euler(restEuler); }

        void LateUpdate()
        {
            var m = Mouse.current != null ? Mouse.current.delta.ReadValue() : Vector2.zero;
            var target = new Vector3(-m.x, -m.y, 0) * (swayAmount * 0.02f);
            target = Vector3.ClampMagnitude(target, 0.03f);
            sway = Vector3.Lerp(sway, target, Time.deltaTime * swaySmooth);
            float speed = cc ? new Vector2(cc.velocity.x, cc.velocity.z).magnitude : 0f;
            bobT += Time.deltaTime * (speed > 0.1f ? 7.5f : 1.2f);
            float amp = speed > 0.1f ? bobAmount : bobAmount * 0.25f;   // idle breathing when standing
            var bob = new Vector3(Mathf.Sin(bobT) * amp * 0.6f, Mathf.Abs(Mathf.Cos(bobT)) * amp, 0);
            transform.localPosition = restPosition + sway + bob;
            transform.localRotation = Quaternion.Euler(restEuler + new Vector3(sway.y, -sway.x, sway.x) * 120f);
        }
    }
}
