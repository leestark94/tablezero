#!/bin/bash
# usage: tools/qa_suspect_shots.sh <tag>   — reimport 이서연, rebuild interrogation scene, play, call her in, render room+bust 1080p to qa/shots/v22/<tag>_*.png
cd "$(dirname "$0")/.."; TAG=${1:-shot}; R=$(pwd -W 2>/dev/null || pwd)
ev(){ unity command script eval --code "$1" 2>&1 | grep -v "claude-code-hint" | tail -1; }
unity command editor.playmode stop >/dev/null 2>&1; sleep 4
ev 'return TableZero.EditorTools.TZSuspectCharacterBuilder.Import();'
ev 'return TableZero.EditorTools.TZInterrogationBuilder.Build();'
unity command editor.playmode start >/dev/null 2>&1
until [ "$(ev 'return UnityEditor.EditorApplication.isPlaying && !UnityEditor.EditorApplication.isCompiling ? "ok":"wait";')" = "ok" ]; do sleep 3; done
ev 'var scr=UnityEngine.Object.FindAnyObjectByType<TableZero.TZInterrogationScreen>();var t=scr.GetType();var f=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Public;t.GetMethod("Select",f).Invoke(scr,new object[]{1,true});t.GetMethod("CallSelected",f).Invoke(scr,null);return "called";'
sleep 20
mkdir -p qa/shots/v22
for m in room bust; do ev "return TableZero.EditorTools.TZSuspectShot.Shoot(@\"$R\qa\shots\v22\${TAG}_$m.png\",\"$m\");"; done
