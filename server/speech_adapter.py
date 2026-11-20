"""Optional server-side Korean speech recognition.
No voice transcription is simulated. Audio isn't persisted or used until the player
confirms transcript. Paid API requires explicit opt-in. No key is ever in Unity.
"""
from __future__ import annotations
import io, json, os, urllib.request, uuid, wave

class SpeechNotReady(RuntimeError): pass

def validate_wav(blob:bytes):
    if not isinstance(blob,bytes) or len(blob)<44 or len(blob)>3_000_000:
        raise SpeechNotReady('Unsupported or oversized voice capture')
    try:
        with wave.open(io.BytesIO(blob),'rb') as w:
            if w.getnchannels()!=1 or w.getsampwidth()!=2 or w.getframerate() not in (16000,24000,48000):
                raise SpeechNotReady('Capture must be 16-bit mono WAV 16/24/48kHz')
            duration=w.getnframes()/w.getframerate()
            if not .2<=duration<=20.5:raise SpeechNotReady('Voice length must be 0.2–20.5 seconds')
    except (wave.Error,EOFError) as e:
        raise SpeechNotReady('Invalid WAV') from e
    return True

class LocalWhisperSTT:
    """Optional `pip install faster-whisper`; no model is bundled or fetched automatically.
    Explicitly provide a LOCAL on-disk model directory to avoid unapproved downloads.
    """
    label='LOCAL_WHISPER'
    def __init__(self):
        folder=os.environ.get('TABLEZERO_WHISPER_MODEL_DIR','')
        if not folder or not os.path.isdir(folder):raise SpeechNotReady('Local ASR model path missing')
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:raise SpeechNotReady('faster-whisper not installed') from e
        self.model=WhisperModel(folder,device='cpu',compute_type='int8',local_files_only=True)
    def transcribe(self,blob:bytes):
        validate_wav(blob)
        segments,info=self.model.transcribe(io.BytesIO(blob),language='ko',beam_size=4,
                                            vad_filter=True)
        return ''.join(x.text for x in segments).strip()

class PaidOpenAISTT:
    label='PAID_REMOTE_STT_OPENAI'
    def __init__(self):
        if os.environ.get('TABLEZERO_ALLOW_PAID_API')!='I_APPROVE_PAID_API_CALLS':
            raise SpeechNotReady('Explicit paid API opt-in missing')
        self.key=os.environ.get('OPENAI_API_KEY','')
        self.model=os.environ.get('TABLEZERO_STT_MODEL','')
        if not self.key or not self.model:raise SpeechNotReady('Server key and STT model required')
    def transcribe(self,blob:bytes):
        validate_wav(blob)
        boundary='----TZ'+uuid.uuid4().hex
        fields=[('model',self.model),('language','ko')]
        body=b''
        for key,value in fields:
            body+=f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()
        body+=f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="mic.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+blob
        body+=f'\r\n--{boundary}--\r\n'.encode()
        req=urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',data=body,
            headers={'Authorization':'Bearer '+self.key,'Content-Type':'multipart/form-data; boundary='+boundary})
        try:
            with urllib.request.urlopen(req,timeout=35) as response:
                result=json.loads(response.read(100_000))
            return str(result['text']).strip()
        except Exception as e:raise SpeechNotReady('Remote speech recognition unavailable') from e

def choose_speech_provider():
    mode=os.environ.get('TABLEZERO_STT_PROVIDER','disabled').lower()
    if mode=='local':return LocalWhisperSTT()
    if mode=='openai':return PaidOpenAISTT()
    raise SpeechNotReady('Voice recognition disabled; configure a real STT provider')
