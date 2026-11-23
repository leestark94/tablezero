using System;
using System.Collections;
using System.Diagnostics;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using Debug = UnityEngine.Debug;

namespace TableZero
{
    /// <summary>
    /// Single localhost link to the authoritative case server (server/api.py).
    /// Dev/Editor: launches the Python server itself with a fresh random token (never stored in the build).
    /// The client never holds canon, persona data, or any LLM key; it only sends intents.
    /// </summary>
    public sealed class TZServer : MonoBehaviour
    {
        public static TZServer I { get; private set; }
        public string baseUrl = "http://127.0.0.1:8765";
        public bool autoLaunchInDev = true;
        [Tooltip("Ollama model used by the dev server (local, zero API cost)")]
        public string ollamaModel = "hf.co/DevQuasar/kakaocorp.kanana-1.5-8b-instruct-2505-GGUF:Q4_K_M";   // Korean-specialised; ~1s/answer on GPU with the strategy engine
        [Tooltip("0 = CPU inference (VRAM stays with the renderer; dev PC GPU resets under CUDA, see BUG-0001)")]
        public int ollamaNumGpu = -1;   // -1 = let Ollama place layers on the GPU (0 = CPU only, ~10x slower)
        public bool Online { get; private set; }
        public string LastError { get; private set; } = "";
        public event Action<bool> OnOnlineChanged;

        private string token;
        private Process proc;
        private bool busyLaunch;

        public static string RepoRoot
        {
            get
            {
                // Editor: .../TABLE_ZERO/TableZero.Unity/Assets. Standalone dev build: .../TABLE_ZERO/Builds/Full/TableZero_Data. Walk up to the folder holding server/api.py.
                for (var d = new DirectoryInfo(Application.dataPath); d != null; d = d.Parent)
                    if (File.Exists(Path.Combine(d.FullName, "server", "api.py"))) return d.FullName;
                var e = new DirectoryInfo(Application.dataPath); return e.Parent != null && e.Parent.Parent != null ? e.Parent.Parent.FullName : "";
            }
        }

        void Awake()
        {
            if (I != null && I != this) { Destroy(gameObject); return; }
            I = this;
            DontDestroyOnLoad(gameObject);
            token = Environment.GetEnvironmentVariable("TABLEZERO_LOCAL_DEV_TOKEN");
            if (string.IsNullOrEmpty(token) || token.Length < 24)
                token = Guid.NewGuid().ToString("N") + Guid.NewGuid().ToString("N");
        }

        IEnumerator Start()
        {
            if (autoLaunchInDev && (Application.isEditor || Debug.isDebugBuild)) yield return Launch();
            else yield return Ping();
        }

        IEnumerator Ping()
        {
            using (var r = UnityWebRequest.Get(baseUrl + "/v1/state"))
            {
                r.SetRequestHeader("X-TableZero-Dev-Token", token);
                r.timeout = 2;
                yield return r.SendWebRequest();
                SetOnline(r.result == UnityWebRequest.Result.Success && r.responseCode == 200);
                if (r.responseCode == 401) LastError = "다른 개발 서버가 이미 실행 중입니다(토큰 불일치)";
            }
        }

        static int FreePort()
        {
            var l = new System.Net.Sockets.TcpListener(System.Net.IPAddress.Loopback, 0);
            l.Start(); int p = ((System.Net.IPEndPoint)l.LocalEndpoint).Port; l.Stop();
            return p;
        }

        IEnumerator Launch()
        {
            if (busyLaunch) yield break;
            busyLaunch = true;
            // own port per session: a stale dev server elsewhere can never answer for this one
            int port = FreePort();
            baseUrl = "http://127.0.0.1:" + port;
            string py = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                                     "Programs", "Python", "Python312", "python.exe");
            if (!File.Exists(py)) py = "python";
            try
            {
                var psi = new ProcessStartInfo(py, "-m server.api")
                {
                    WorkingDirectory = RepoRoot, UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardOutput = true, RedirectStandardError = true
                };
                psi.EnvironmentVariables["TABLEZERO_LOCAL_DEV_TOKEN"] = token;
                psi.EnvironmentVariables["TABLEZERO_AI_PROVIDER"] = "ollama";
                psi.EnvironmentVariables["TABLEZERO_OLLAMA_MODEL"] = ollamaModel;
                if (ollamaNumGpu >= 0) psi.EnvironmentVariables["TABLEZERO_OLLAMA_NUM_GPU"] = ollamaNumGpu.ToString();
                psi.EnvironmentVariables["TABLEZERO_OLLAMA_THREADS"] = Mathf.Max(2, SystemInfo.processorCount / 2).ToString();
                psi.EnvironmentVariables["TABLEZERO_ALLOW_UNAPPROVED_ART"] = "1";
                psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                psi.EnvironmentVariables["TABLEZERO_PORT"] = port.ToString();
                proc = Process.Start(psi);
                proc.OutputDataReceived += (s, e) => { if (!string.IsNullOrEmpty(e.Data)) Debug.Log("[server] " + e.Data); };
                proc.ErrorDataReceived += (s, e) => { if (!string.IsNullOrEmpty(e.Data)) Debug.LogWarning("[server] " + e.Data); };
                proc.BeginOutputReadLine(); proc.BeginErrorReadLine();
            }
            catch (Exception e)
            {
                LastError = "로컬 수사 서버를 시작하지 못했습니다: " + e.Message;
                busyLaunch = false;
                yield break;
            }
            for (int i = 0; i < 40 && !Online; i++)
            {
                yield return new WaitForSecondsRealtime(0.25f);
                yield return Ping();
            }
            busyLaunch = false;
        }

        void SetOnline(bool v)
        {
            if (v == Online) return;
            Online = v;
            OnOnlineChanged?.Invoke(v);
        }

        public void Post(string path, string json, Action<bool, string> done, int timeoutSeconds = 30)
            => StartCoroutine(Send("POST", path, json, done, timeoutSeconds));
        public void Get(string path, Action<bool, string> done) => StartCoroutine(Send("GET", path, null, done, 10));

        IEnumerator Send(string method, string path, string body, Action<bool, string> done, int timeout)
        {
            if (!Online) yield return Ping();
            using (var req = new UnityWebRequest(baseUrl + path, method))
            {
                req.downloadHandler = new DownloadHandlerBuffer();
                req.SetRequestHeader("X-TableZero-Dev-Token", token);
                req.timeout = timeout;
                if (body != null)
                {
                    req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body));
                    req.SetRequestHeader("Content-Type", "application/json; charset=utf-8");
                }
                yield return req.SendWebRequest();
                string text = req.downloadHandler != null ? req.downloadHandler.text : "";
                bool ok = req.result == UnityWebRequest.Result.Success && req.responseCode < 400;
                if (req.result == UnityWebRequest.Result.ConnectionError) SetOnline(false);
                done?.Invoke(ok, string.IsNullOrEmpty(text) ? req.error : text);
            }
        }

        void OnApplicationQuit() => StopServer();
        void OnDestroy() => StopServer();

        /// <summary>Kill the whole tree (python may spawn children); never leave a dev server behind.</summary>
        void StopServer()
        {
            try
            {
                if (proc == null || proc.HasExited) return;
                var k = new ProcessStartInfo("taskkill", $"/PID {proc.Id} /T /F") { UseShellExecute = false, CreateNoWindow = true };
                Process.Start(k)?.WaitForExit(3000);
            }
            catch { }
            proc = null;
        }

        public static string NewActionId() => Guid.NewGuid().ToString("N");
    }

    [Serializable] public class TZError { public bool ok; public string error; public string detail; }
}
