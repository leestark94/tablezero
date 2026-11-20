using System;
using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    // Local integration glue between playable case desk and server-authorized records.
    // No fabricated evidence: every visible list item comes from the server page projection.
    public sealed class TZCaseDeskBridge : MonoBehaviour
    {
        [Serializable]public class PageEnvelope {public bool ok;public TZCaseDeskUI.PageData page;}
        [Serializable]public class ReplyData {public string line;public string provider;public string reply_mode;}
        [Serializable]public class ReplyEnvelope {public bool ok;public ReplyData data;}
        [Serializable]public class Identity {public string id;public string name;}
        [Serializable]public class StateData
        { public string[] evidence_ids;public Identity[] known_people;public string scene;public string act; }
        [Serializable]public class StateEnvelope {public StateData state;public string mode;}
        public TZCaseDeskUI ui;
        public TZLocalBridgeClient bridge;
        private readonly Dictionary<string,string> nameToId=new Dictionary<string,string>();
        private readonly Dictionary<string,string> evidenceLabels=new Dictionary<string,string>();
        private void OnEnable()
        {
            if(ui==null || bridge==null){Debug.LogError("TABLE ZERO UI bridge missing");return;}
            bridge.OnResponse+=ReadResponse;
            bridge.OnFailure+=ReadFailure;
            ui.NavigationRequested+=bridge.GetPage;
            ui.QuestionRequested+=Ask;
            ui.FinalReportRequested+=Report;
            ui.SetConnection("연결 대기");
            bridge.Refresh();
            bridge.GetPage("case");
        }
        private void OnDisable()
        {
            if(ui==null || bridge==null)return;
            bridge.OnResponse-=ReadResponse;
            bridge.OnFailure-=ReadFailure;
            ui.NavigationRequested-=bridge.GetPage;
            ui.QuestionRequested-=Ask;
            ui.FinalReportRequested-=Report;
        }
        private void ReadResponse(string json)
        {
            if(json.IndexOf("\"state\"")>=0)
            {
                StateEnvelope envelope=JsonUtility.FromJson<StateEnvelope>(json);
                if(envelope==null || envelope.state==null)return;
                var names=new List<string>{"지목 보류"};
                nameToId.Clear();
                foreach(var person in envelope.state.known_people ?? new Identity[0])
                {
                    names.Add(person.name);nameToId[person.name]=person.id;
                }
                ui.SetAccusedChoices(names);
                // Until names for acquired evidence are received, label by authoritative ID only
                evidenceLabels.Clear();
                foreach(var id in envelope.state.evidence_ids ?? new string[0])
                    evidenceLabels[id]="확보 자료  "+id;
                ui.SetReportEvidenceChoices(evidenceLabels);
                ui.SetConnection(envelope.mode);
            }
            else if(json.IndexOf("\"page\"")>=0)
            {
                // PageData must match server's PageData schema (records, context, connection)
                PageEnvelope envelope=JsonUtility.FromJson<PageEnvelope>(json);
                if(envelope?.page==null)return;
                // V10 uses an explicit server-supplied tab; do not sniff JSON text
                string tab = envelope.page.tab;
                if (string.IsNullOrWhiteSpace(tab)) return;
                ui.UpdatePage(tab,envelope.page);
                if(tab=="evidence")
                {
                    // The backend must return an id field for full binding, else keep ID labels
                    // Placeholder names are not guessed in release scenes
                }
            }
            else if(json.IndexOf("\"line\"")>=0)
            {
                ReplyEnvelope envelope=JsonUtility.FromJson<ReplyEnvelope>(json);
                if(envelope?.data!=null)
                    ui.SetSubtitle(envelope.data.line);
                bridge.GetPage("interview");
            }
            // Refresh after response mutations only; never refresh a state response recursively
            if(json.IndexOf("\"state\"")<0)bridge.Refresh();
        }
        private void ReadFailure(string error)
        {
            ui.SetConnection("연결 오류 / 확인 필요");
            Debug.LogWarning("TABLE ZERO SERVER: " + error);
        }
        private void Ask(string question)=>bridge.Ask(question);
        private void Report(string suspectName,string[] evidence)
        {
            string id=null;
            if(suspectName!="지목 보류" && !nameToId.TryGetValue(suspectName,out id))
            {ui.SetConnection("지목할 인물 확인 필요");return;}
            bridge.SubmitReport(id,evidence);
        }
    }
}
