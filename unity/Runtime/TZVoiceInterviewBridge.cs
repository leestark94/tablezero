using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace TableZero
{
    /// <summary>
    /// Attach with TZVoiceQuestionCapture and call SubmitConfirmedTranscript()
    /// only after the player reads/edits recognized Korean text in a real UI TextField.
    /// Pure localhost integration test. Production requires authenticated gateway.
    /// </summary>
    public sealed class TZVoiceInterviewBridge : MonoBehaviour
    {
        public TZVoiceQuestionCapture microphone;
        public string localServerUrl = "http://127.0.0.1:8765";
        public string localDevToken = "";
        public event Action<string> OnDraftTranscript;
        public event Action<string> OnConfirmedQuestionResult;
        public event Action<string> OnError;
        private string draft;
        private bool isBusy;
        [Serializable] private sealed class AskRequest
        {public string action_id;public string input_mode;public string question;public string evidence_id;public bool transcript_confirmed;}
        void Awake(){if(microphone)microphone.OnWavReady += CaptureReady;}
        void OnDestroy(){if(microphone)microphone.OnWavReady -= CaptureReady;}
        bool SafeEndpoint()=>localDevToken.Length >= 24 &&
            (localServerUrl.StartsWith("http://127.0.0.1:") || localServerUrl.StartsWith("http://localhost:"));
        void CaptureReady(byte[] bytes)
        {
            if(isBusy){OnError?.Invoke("이미 변환 중입니다");return;}
            StartCoroutine(Transcribe(bytes));
        }
        IEnumerator Transcribe(byte[] bytes)
        {
            if(!SafeEndpoint()){OnError?.Invoke("로컬 개발 서버 인증 필요");yield break;}
            isBusy=true;
            using(var req=new UnityWebRequest(localServerUrl+"/v1/speech/transcribe","POST"))
            {
                req.uploadHandler = new UploadHandlerRaw(bytes);
                req.downloadHandler=new DownloadHandlerBuffer();req.timeout=40;
                req.SetRequestHeader("Content-Type","audio/wav");
                req.SetRequestHeader("X-TableZero-Dev-Token",localDevToken);
                yield return req.SendWebRequest();
                if(req.result!=UnityWebRequest.Result.Success || req.responseCode>=400)
                    OnError?.Invoke("음성 인식 실패: "+req.responseCode);
                else
                {
                    // This server-only preview returns {"ok":true,"data":{"text":"..."}}
                    // This narrow JsonUtility wrapper avoids exposing raw audio to gameplay logic.
                    try
                    {
                        TZSpeechResult r=JsonUtility.FromJson<TZSpeechResult>(req.downloadHandler.text);
                        draft=r?.data?.text ?? "";
                        if (string.IsNullOrWhiteSpace(draft)) OnError?.Invoke("음성 내용이 인식되지 않았습니다");
                        else OnDraftTranscript?.Invoke(draft);
                    }
                    catch {OnError?.Invoke("음성 응답 형식 오류");}
                }
            }
            isBusy=false;
        }
        [Serializable] private sealed class TZSpeechResult { public bool ok; public TZSpeechData data; }
        [Serializable] private sealed class TZSpeechData { public string text; public bool needs_confirmation; }
        /// <summary>Invoke only after player accepts the editable transcript, not automatically.</summary>
        public void SubmitConfirmedTranscript(string correctedText,string evidenceId="")
        {
            if(isBusy || string.IsNullOrWhiteSpace(correctedText)){OnError?.Invoke("질문을 확인해야 합니다");return;}
            StartCoroutine(Submit(correctedText,evidenceId));
        }
        IEnumerator Submit(string correctedText,string evidenceId)
        {
            if (!SafeEndpoint()) {OnError?.Invoke("인증 확인 필요");yield break;}
            isBusy=true;
            AskRequest request=new AskRequest{
                action_id=Guid.NewGuid().ToString("N"),input_mode="voice",question=correctedText,
                evidence_id=string.IsNullOrWhiteSpace(evidenceId)?null:evidenceId,
                transcript_confirmed=true};
            byte[] payload=Encoding.UTF8.GetBytes(JsonUtility.ToJson(request));
            using(var req=new UnityWebRequest(localServerUrl+"/v1/interview/ask-v11","POST"))
            {
                req.uploadHandler=new UploadHandlerRaw(payload);req.downloadHandler=new DownloadHandlerBuffer();req.timeout=45;
                req.SetRequestHeader("Content-Type","application/json; charset=utf-8");
                req.SetRequestHeader("X-TableZero-Dev-Token",localDevToken);
                yield return req.SendWebRequest();
                if(req.result!=UnityWebRequest.Result.Success || req.responseCode>=400)OnError?.Invoke("심문 응답 오류: "+req.responseCode);
                else OnConfirmedQuestionResult?.Invoke(req.downloadHandler.text);
            }
            isBusy=false;
        }
    }
}
