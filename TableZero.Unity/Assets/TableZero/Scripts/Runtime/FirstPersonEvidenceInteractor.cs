using UnityEngine;

namespace TableZero
{
    // Binds to authored, physically modelled evidence prefabs. No generated geometry.
    public class EvidenceObject : MonoBehaviour
    {
        public string evidenceId;
        public bool availableToInspect = true;
        public Rigidbody body;
    }
    public class FirstPersonEvidenceInteractor : MonoBehaviour
    {
        public Camera eye;
        public Transform inspectionAnchor;
        public LayerMask evidenceLayers = ~0;
        public float reachMeters = 2.1f;
        public float rotationDegreesPerSecond = 70f;
        EvidenceObject held;
        Transform oldParent;
        Vector3 oldPosition;
        Quaternion oldRotation;
        bool oldKinematic;
        public System.Action<string> OnEvidenceInspected;

        public bool TryInspect()
        {
            if (held != null || !eye || !inspectionAnchor) return false;
            if (!Physics.Raycast(eye.transform.position,eye.transform.forward,out var hit,reachMeters,evidenceLayers,QueryTriggerInteraction.Ignore)) return false;
            var item = hit.collider.GetComponentInParent<EvidenceObject>();
            if (!item || !item.availableToInspect || string.IsNullOrEmpty(item.evidenceId)) return false;
            held=item; oldParent=item.transform.parent; oldPosition=item.transform.position; oldRotation=item.transform.rotation;
            if (item.body) { oldKinematic=item.body.isKinematic; item.body.isKinematic=true; item.body.linearVelocity=Vector3.zero; }
            item.transform.SetParent(inspectionAnchor,false);
            item.transform.localPosition=Vector3.zero;item.transform.localRotation=Quaternion.identity;
            OnEvidenceInspected?.Invoke(item.evidenceId);return true;
        }
        public void RotateHeld(Vector2 direction)
        {
            if (!held) return;
            held.transform.Rotate(Vector3.up,direction.x * rotationDegreesPerSecond * Time.deltaTime,Space.Self);
            held.transform.Rotate(Vector3.right,-direction.y * rotationDegreesPerSecond * Time.deltaTime,Space.Self);
        }
        public void Release()
        {
            if (!held) return;
            held.transform.SetParent(oldParent,true);
            held.transform.SetPositionAndRotation(oldPosition,oldRotation);
            if (held.body) held.body.isKinematic=oldKinematic;
            held=null;
        }
        void OnDisable() => Release();
    }
}
