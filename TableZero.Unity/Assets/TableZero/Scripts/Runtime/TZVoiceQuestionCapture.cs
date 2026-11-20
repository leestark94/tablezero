using System;
using System.IO;
using UnityEngine;

namespace TableZero
{
    /// <summary>
    /// Push to talk capture: audio->WAV, NOT automatic question submission.
    /// Consumer sends WAV to authenticated SERVER STT; renders corrected transcript,
    /// asks for explicit confirmation, then submits through InterviewService.
    /// Voice recognition/network latency must never cost interview time.
    /// </summary>
    public sealed class TZVoiceQuestionCapture : MonoBehaviour
    {
        public int sampleRate = 16000;
        public int maxDurationSeconds = 20;
        public event Action<byte[]> OnWavReady;
        public event Action<string> OnCaptureError;
        private string selectedDevice;
        private AudioClip recording;
        private bool captureActive;

        public bool Begin()
        {
            if (captureActive) return false;
            if (Microphone.devices.Length==0) {OnCaptureError?.Invoke("마이크를 사용할 수 없습니다");return false;}
            selectedDevice=Microphone.devices[0];
            recording=Microphone.Start(selectedDevice,false,maxDurationSeconds,sampleRate);
            captureActive=recording!=null;
            if (!captureActive) OnCaptureError?.Invoke("마이크 녹음을 시작하지 못했습니다");
            return captureActive;
        }
        public void End()
        {
            if (!captureActive) return;
            int frames = Mathf.Clamp(Microphone.GetPosition(selectedDevice),0,recording.samples);
            Microphone.End(selectedDevice);
            captureActive=false;
            if (frames<sampleRate/5) {OnCaptureError?.Invoke("녹음이 너무 짧습니다");return;}
            int channels=recording.channels;
            float[] samples=new float[frames*channels];
            recording.GetData(samples,0);
            using(var stream=new MemoryStream())
            using(var writer=new BinaryWriter(stream))
            {
                int monoLength=frames*2;
                writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF"));writer.Write(36+monoLength);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));writer.Write(16);
                writer.Write((short)1);writer.Write((short)1);writer.Write(sampleRate);writer.Write(sampleRate*2);
                writer.Write((short)2);writer.Write((short)16);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("data"));writer.Write(monoLength);
                for(int i=0;i<frames;i++)
                {
                    float mix=0f;for(int ch=0;ch<channels;ch++)mix+=samples[i*channels+ch];
                    short value=(short)Mathf.RoundToInt(Mathf.Clamp(mix/channels,-1f,1f)*32767f);
                    writer.Write(value);
                }
                writer.Flush();OnWavReady?.Invoke(stream.ToArray());
            }
            Destroy(recording);
            recording=null;
        }
        private void OnDisable() { if(captureActive) { Microphone.End(selectedDevice);captureActive=false;} }
    }
}
