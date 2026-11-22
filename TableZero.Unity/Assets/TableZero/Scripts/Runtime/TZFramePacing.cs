using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// The local suspect model shares one GPU with the renderer. Uncapped, Unity takes ~100% of the GPU and a single
    /// answer took 40-170 s (measured 2026-11-22). Cap the frame rate always, and lower it while a suspect is
    /// generating a line: the room is quiet then (suspect thinking), so 30 fps is not visible, and the model gets the GPU.
    /// Benchmark runs (-tzbench) keep their own uncapped setting.
    /// </summary>
    public static class TZFramePacing
    {
        public const int Normal = 60, WhileAIThinks = 30;
        static int busy;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Boot()
        {
            busy = 0;
            if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-tzbench") >= 0) return;
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = Normal;
        }

        /// <summary>Call with true when a model request starts and false when it ends (nested calls are counted).</summary>
        public static void AIBusy(bool on)
        {
            busy = Mathf.Max(0, busy + (on ? 1 : -1));
            if (Application.targetFrameRate > 0 || busy > 0) Application.targetFrameRate = busy > 0 ? WhileAIThinks : Normal;
        }
    }
}
