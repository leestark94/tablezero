using System;
using System.Collections.Generic;
using UnityEngine;

namespace TableZero
{
    // Single source of runtime asset truth. Missing assets block release, never silently spawn primitives.
    public sealed class TZPerformanceManifest : MonoBehaviour
    {
        [Serializable] public sealed class Entry
        {
            public string id;
            public GameObject authoredPrefab;
            public AnimationClip authoredMotion;
            public AudioClip recordedSound;
            public Material[] pbrMaterials;
            public bool commercialLicenseChecked;
            public bool koreanArtDirectionApproved;
            public string licenseSourceUrl;
        }
        public Entry[] entries;
        public bool IsReady(string cueId)
        {
            Entry e=Array.Find(entries, x=>x!=null && x.id==cueId);
            if (e==null || !e.authoredPrefab || !e.authoredMotion || !e.recordedSound) return false;
            if (!e.commercialLicenseChecked || !e.koreanArtDirectionApproved) return false;
            if (e.pbrMaterials==null || e.pbrMaterials.Length==0) return false;
            foreach (Material mat in e.pbrMaterials) if (!mat || !mat.shader) return false;
            return true;
        }
        public int CountReady()
        {
            int count=0;
            foreach(var e in entries) if(e!=null && IsReady(e.id))count++;
            return count;
        }
        [ContextMenu("Report Missing Production Assets")]
        public void LogMissing()
        {
            if(entries==null){Debug.LogError("TABLE//ZERO missing manifest");return;}
            foreach(var e in entries)
                if(e!=null && !IsReady(e.id))Debug.LogError("TABLE//ZERO RELEASE_BLOCKED " + e.id);
        }
    }
}
