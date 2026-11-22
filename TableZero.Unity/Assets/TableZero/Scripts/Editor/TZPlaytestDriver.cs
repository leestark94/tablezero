using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace TableZero.EditorTools
{
    /// <summary>
    /// Drives the REAL interrogation screen in Play Mode through its own methods (select suspect, call, type a question, Send, Continue),
    /// so the same code path, server, model, rendering and frame pacing the player gets are measured. Each turn is logged by
    /// TZLatencyLog (qa/logs/perf/latency_unity.csv); this driver also writes qa/logs/perf/playtest_driver.log. It grants no evidence,
    /// no budget and does not touch server state: it only asks questions.
    /// Usage (Play Mode):  TZPlaytestDriver.Run(1, "q1|q2|q3")   // suspect index 0..2 (강도현, 이서연, 박현수 order of the ledger)
    /// </summary>
    public static class TZPlaytestDriver
    {
        static readonly BindingFlags F = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
        static string log; static Queue<string> qs; static object screen; static Type T; static int stage; static double until; static string cur; static double tStart;

        static void W(string m)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(log));
            File.AppendAllText(log, DateTime.Now.ToString("HH:mm:ss.fff") + "  " + m + "\n");
        }
        static object Get(string n) => T.GetField(n, F).GetValue(screen);
        static void Call(string n, params object[] a) => T.GetMethod(n, F).Invoke(screen, a);

        public static string Run(int suspectIndex, string pipeQuestions)
        {
            if (!EditorApplication.isPlaying) return "not in play mode";
            screen = UnityEngine.Object.FindAnyObjectByType<TableZero.TZInterrogationScreen>(); if (screen == null) return "no interrogation screen";
            T = screen.GetType(); log = Path.Combine(TZServer.RepoRoot, "qa", "logs", "perf", "playtest_driver.log");
            qs = new Queue<string>(pipeQuestions.Split('|')); stage = 0; until = 0;
            W($"=== run suspect={suspectIndex} questions={qs.Count} fps_target={Application.targetFrameRate}");
            Call("Select", suspectIndex, true); Call("CallSelected");
            tStart = EditorApplication.timeSinceStartup; EditorApplication.update -= Tick; EditorApplication.update += Tick;
            return "started";
        }

        static void Tick()
        {
            if (!EditorApplication.isPlaying || screen == null) { EditorApplication.update -= Tick; return; }
            double now = EditorApplication.timeSinceStartup;
            if (now < until) return;
            bool started = (bool)Get("started"), busy = (bool)Get("busy"), awaiting = (bool)Get("awaitingContinue");
            switch (stage)
            {
                case 0:   // wait for the call/entry sequence to finish
                    if (started) { W($"seated after {now - tStart:0.0}s"); stage = 1; until = now + 2; }
                    else if (now - tStart > 90) { W("TIMEOUT waiting for entry"); EditorApplication.update -= Tick; }
                    break;
                case 1:   // send next question
                    if (qs.Count == 0) { W("=== done"); EditorApplication.update -= Tick; return; }
                    cur = qs.Dequeue();
                    var input = (TextField)Get("input"); input.value = cur; tStart = now;
                    W("Q: " + cur); Call("Send"); stage = 2;
                    break;
                case 2:   // wait for the line to be complete
                    if (!busy && awaiting) { W($"A done in {now - tStart:0.0}s"); Call("Continue"); stage = 1; until = now + 1.2; }
                    else if (now - tStart > 120) { W("TIMEOUT waiting for answer"); EditorApplication.update -= Tick; }
                    break;
            }
        }
    }
}
