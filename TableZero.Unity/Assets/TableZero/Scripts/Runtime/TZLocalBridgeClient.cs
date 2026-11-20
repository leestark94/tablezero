using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace TableZero
{
    /// <summary>
    /// Development-only Unity localhost adapter; use production auth before public distribution.
    /// Does not contain LLM API keys or locked story canon. Never connect Unity directly to a paid LLM.
    /// </summary>
    public sealed class TZLocalBridgeClient : MonoBehaviour
    {
        public string serverUrl = "http://127.0.0.1:8765";
        [Tooltip("LOCAL DEV ONLY, never commit production secrets")]
        public string localDevToken = "";
        public bool refuseNonLocalhost = true;
        public event Action<string> OnResponse;
        public event Action<string> OnFailure;
        [Serializable] public sealed class SceneRequest {public string scene;}
        [Serializable] public sealed class InterviewRequest {public string suspect_id;}
        [Serializable] public sealed class QuestionRequest {public string question; public string evidence_id;}
        [Serializable] public sealed class ReportRequest
        {public string accused_id; public string[] evidence_ids; public bool confirm;}

        private bool SafeEndpoint()
        {
            if (string.IsNullOrEmpty(localDevToken) || localDevToken.Length < 24) return false;
            if (refuseNonLocalhost && !(serverUrl.StartsWith("http://127.0.0.1:") || serverUrl.StartsWith("http://localhost:"))) return false;
            return true;
        }
        public void Refresh() => StartCoroutine(Request("GET","/v1/state",null));
        public void GetPage(string tab) => StartCoroutine(Request("GET","/v1/page?tab="+UnityWebRequest.EscapeURL(tab),null));
        public void ChangeScene(string id) => StartCoroutine(Request("POST","/v1/scene",JsonUtility.ToJson(new SceneRequest{scene=id})));
        public void StartInterview(string suspectId) => StartCoroutine(Request("POST","/v1/interview/start",JsonUtility.ToJson(new InterviewRequest{suspect_id=suspectId})));
        public void Ask(string question,string evidenceId=null) => StartCoroutine(Request("POST","/v1/interview/ask",JsonUtility.ToJson(new QuestionRequest{question=question,evidence_id=evidenceId})));
        public void EndInterview() => StartCoroutine(Request("POST","/v1/interview/end","{}"));
        public void SubmitReport(string id,string[] evidence)
        {
            StartCoroutine(Request("POST","/v1/report",JsonUtility.ToJson(new ReportRequest{accused_id=id,evidence_ids=evidence,confirm=true})));
        }
        private IEnumerator Request(string method,string path,string body)
        {
            if(!SafeEndpoint()) {OnFailure?.Invoke("개발 서버 인증 또는 로컬 주소 설정 필요");yield break;}
            UnityWebRequest req = new UnityWebRequest(serverUrl + path,method);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("X-TableZero-Dev-Token",localDevToken);
            req.timeout=28;
            if(body!=null)
            {
                req.uploadHandler=new UploadHandlerRaw(Encoding.UTF8.GetBytes(body));
                req.SetRequestHeader("Content-Type","application/json; charset=utf-8");
            }
            yield return req.SendWebRequest();
            if(req.result!=UnityWebRequest.Result.Success || req.responseCode>=400)
                OnFailure?.Invoke(req.downloadHandler?.text ?? "네트워크 오류");
            else OnResponse?.Invoke(req.downloadHandler.text);
            req.Dispose();
        }
    }
}
