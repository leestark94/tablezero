using System;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Threshold volume (302 front door). Crossing it asks the server to move the case scene
    /// (hall ⇄ room302). The server, not this trigger, decides whether the move is legal.
    /// Also swaps the ambience: hallway hum vs. the room's fridge/room tone.
    /// </summary>
    [RequireComponent(typeof(BoxCollider))]
    public sealed class TZSceneZoneTrigger : MonoBehaviour
    {
        public string insideScene = "room302";
        public string outsideScene = "hall";
        public Transform roomCenter;
        public AudioSource hallAmbience, roomAmbience;
        public static string ServerScene = "hall";
        [Serializable] class SceneReq { public string scene; }

        void Start() { TZSession.Sync(); }   // the zone cache follows the server's real scene (new Play / new case / reconnect)

        void OnTriggerEnter(Collider other) => Reconcile(other);
        void OnTriggerExit(Collider other) => Reconcile(other);

        void Reconcile(Collider other)
        {
            if (!other.GetComponent<CharacterController>() || !roomCenter) return;
            bool inside = Vector3.Distance(other.transform.position, roomCenter.position) <
                          Vector3.Distance(transform.position, roomCenter.position);
            string want = inside ? insideScene : outsideScene;
            if (want == ServerScene || TZServer.I == null) return;
            TZServer.I.Post("/v1/scene", JsonUtility.ToJson(new SceneReq { scene = want }), (ok, text) =>
            {
                if (ok) { ServerScene = want; TZEventLog.Record("scene", want); }
                else { Debug.Log("[scene] server refused: " + text); TZSession.Sync(); }   // refused => our cache was wrong: take the server's scene
            });
            if (hallAmbience) hallAmbience.volume = inside ? 0.12f : 0.5f;
            if (roomAmbience) roomAmbience.volume = inside ? 0.5f : 0.08f;
        }
    }
}
