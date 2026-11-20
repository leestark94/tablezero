using UnityEngine;

namespace TableZero
{
    // Collision-driven secondary prop response, not scripted teleportation.
    public class InterrogationTable : MonoBehaviour
    {
        public Rigidbody cupBody;
        public AudioSource impactAudio;
        public AudioClip tableThump;
        public float maxCupImpulse = .12f;
        public void OnApprovedTableSlam(Vector3 worldImpactDirection)
        {
            if (impactAudio && tableThump) impactAudio.PlayOneShot(tableThump);
            if (!cupBody) { Debug.LogWarning("TABLE//ZERO: physical cup not bound"); return; }
            if (cupBody.isKinematic) { Debug.LogWarning("Cup Rigidbody is kinematic; no physical reaction"); return; }
            Vector3 impulse = Vector3.ClampMagnitude(worldImpactDirection,maxCupImpulse);
            cupBody.AddForceAtPosition(impulse,cupBody.worldCenterOfMass + Vector3.up*.025f,ForceMode.Impulse);
        }
    }
}
