"""Local-dev-only HTTP bridge for Unity.
NO production auth, persistence, rate limits, user-account system or licensed AI included.
Never bind to public network, never embed any provider API key in Unity build.
"""
from __future__ import annotations
import json,os,urllib.parse,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .episode_controller import EpisodeController
from .runtime import GuardError
from .providers import choose_provider_from_env,ProviderError
from .interview_service import InterviewService
from .speech_adapter import choose_speech_provider,SpeechNotReady,validate_wav

class LocalBridgeHandler(BaseHTTPRequestHandler):
    controller:EpisodeController=EpisodeController()
    local_token:str=''
    max_body:int=16384
    interview_service:InterviewService|None=None
    server_version='TableZeroPreview/0.8'
    def _send(self,code,obj):
        b=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(b)
    def _auth(self):
        if self.client_address[0] not in ('127.0.0.1','::1'):
            self._send(403,{'error':'localhost_only'});return False
        if not self.local_token or self.headers.get('X-TableZero-Dev-Token')!=self.local_token:
            self._send(401,{'error':'local_token_missing_or_wrong'});return False
        return True
    def do_GET(self):
        if not self._auth():return
        if self.path=='/v1/state':
            self._send(200,{'mode':'LOCAL_PREVIEW_NOT_SHIPPABLE','state':self.controller.public_state()})
        elif self.path.startswith('/v1/page?'):
            query=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            tab=query.get('tab',[''])[0]
            self._send(200,{'ok':True,'page':page_projection(self.controller,tab)})
        else:self._send(404,{'error':'not_found'})
    def do_POST(self):
        if not self._auth():return
        try:
            if self.path=='/v1/speech/transcribe':
                # Dev localhost route only; confirm the transcript in UI before asking
                size=int(self.headers.get('Content-Length','0'))
                if size<44 or size>3_000_000 or self.headers.get('Content-Type')!='audio/wav':
                    raise ValueError('Invalid voice request')
                blob=self.rfile.read(size)
                validate_wav(blob)
                provider=choose_speech_provider()
                transcript=provider.transcribe(blob)
                if not transcript:raise SpeechNotReady('No Korean speech recognized')
                self._send(200,{'ok':True,'data':{'text':transcript,'needs_confirmation':True,
                                               'provider':provider.label}})
                return
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>self.max_body:raise ValueError('invalid_body_length')
            value=json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(value,dict):raise ValueError('expected_json_object')
            path=self.path
            if path=='/v1/scene':
                result=self.controller.transition(value.get('scene'))
            elif path=='/v1/interview/start':
                if self.interview_service is None: self.interview_service=InterviewService(self.controller)
                actor=value.get('suspect_id')
                if self.controller.state.interviewed:self.controller.desk.charge_interview()
                session=self.interview_service.begin(actor)
                result={'actor_id':actor,'opened':True,'interview':session,
                        'clock':self.controller.clock_text(),'budget_left':self.controller.desk.budget-self.controller.desk.spent}
            elif path=='/v1/prop/interact':
                result=self.controller.props.interact(value.get('prop_id'),value.get('verb'),
                    action_id=value.get('action_id',''),player_pos=value.get('player_pos'))
            elif path=='/v1/prop/procedure':
                result=self.controller.props.procedure(value.get('prop_id'),value.get('action'),
                    player_pos=value.get('player_pos'))
            elif path=='/v1/player/gloves':
                result=self.controller.props.set_gloves(value.get('on') is True)
            elif path=='/v1/desk/options':
                result=self.controller.desk.options()
            elif path=='/v1/desk/request':
                result=self.controller.desk.request(value.get('request_id'))
            elif path=='/v1/evidence/list':
                result={'evidence':evidence_cards(self.controller)}
            elif path in ('/v1/interview/ask','/v1/interview/ask-v11'):
                if self.interview_service is None:raise GuardError('Interview service unavailable')
                # Legacy endpoint mapped to new time-contract; keys should be client-issued in production
                action_id=value.get('action_id') or uuid.uuid4().hex
                mode=value.get('input_mode','typed')
                receipt=self.interview_service.ask(value.get('question',''),
                    input_mode=mode,action_id=action_id,
                    presented_evidence=value.get('evidence_id') or None,   # Unity JsonUtility sends "" for an unset string
                    transcript_confirmed=value.get('transcript_confirmed',True) is True)
                result={k:getattr(receipt,k) for k in receipt.__dataclass_fields__}

            elif path=='/v1/interview/end':
                if self.interview_service:self.interview_service.close()
                else:self.controller.finish_interview()
                # The detective does NOT learn about autonomous contacts here; only via later records/testimony
                result={'ended':True,'clock':self.controller.clock_text()}
            elif path=='/v1/report':
                # Local preview test route, not a production final-submission service
                result=self.controller.file_report(value.get('accused_id'),value.get('evidence_ids',[]),
                                                   chain_defects=value.get('chain_defects',[]),
                                                   final=value.get('confirm') is True)
            elif path=='/v1/evidence/preview-grant':
                if os.environ.get('TABLEZERO_DEV_ALLOW_EVIDENCE_GRANT')!='1':
                    raise GuardError('Preview grant disabled; production needs server-side authorization')
                result=self.controller.acquire(value.get('evidence_id'),authorized=True,
                                               photo_logged=value.get('photo_logged') is True,
                                               sealed=value.get('sealed') is True)
            else:
                self._send(404,{'error':'not_found'});return
            self._send(200,{'ok':True,'data':result})
        except (GuardError,SpeechNotReady,ValueError,KeyError,TypeError) as e:
            self._send(422,{'ok':False,'error':str(e)})
        except ProviderError as e:
            # Model unavailable: explicit error, no world mutation, no time charged
            self._send(503,{'ok':False,'error':'ai_unavailable','detail':str(e)})
        except Exception as e:
            # No leakage of internals or secret world state in HTTP errors
            self.log_error('Unhandled exception %s',type(e).__name__)
            self._send(500,{'ok':False,'error':'internal_error'})
    def log_message(self,format,*args):pass

def serve(host='127.0.0.1',port=8765):
    if host!='127.0.0.1':raise RuntimeError('LOCAL DEV ONLY: external bind forbidden')
    port=int(os.environ.get('TABLEZERO_PORT',port))
    token=os.environ.get('TABLEZERO_LOCAL_DEV_TOKEN','')
    if len(token)<24:raise RuntimeError('Set TABLEZERO_LOCAL_DEV_TOKEN (min 24 chars)')
    LocalBridgeHandler.local_token=token
    LocalBridgeHandler.controller=EpisodeController(provider=choose_provider_from_env())
    LocalBridgeHandler.interview_service=InterviewService(LocalBridgeHandler.controller)
    print(f'TABLE//ZERO localhost bridge on {host}:{port}; NOT production; endpoints require dev token',flush=True)
    server=ThreadingHTTPServer((host,port),LocalBridgeHandler)
    server.serve_forever()



def page_projection(ctrl, tab):
    """Player-only source projection for CASE DESK V10.

    - Only already acquired evidence is readable
    - Never reveal raw truth_events or culprit_id
    - Testimony remains unverified irrespective of delivery emotion
    - UI comparisons are just side-by-side observations, never guilt inference
    """
    if tab not in ('case', 'evidence', 'interview', 'timeline', 'report', 'settings'):
        raise ValueError('Unknown page')
    world = ctrl.world
    records = []
    def add(title, detail='', provenance='', status='확인 전', *, id='', kind='', limitation=''):
        records.append({'id': id, 'kind': kind, 'title': title,
                        'detail': detail, 'provenance': provenance,
                        'status': status, 'display_status': ('확보됨' if kind == 'evidence' else status), 'limitation': limitation})
    # The canon file is NEVER transferred to clients as a whole
    acquired = {e['id']: e for e in world._canon['evidence'] if e['id'] in world.available_evidence}
    if tab == 'case':
        add('CASE 001 / 302호의 밤', '가상의 경기도 소도시 · 빌라 302호',
            '사건 기본기록', '사건 진행 중', kind='case',
            limitation='사건의 진실은 수사 기록과 별도로 검증해야 함')
        add('수사 기록의 상태', '현장에서 관찰한 사실과 인물의 진술을 구분하세요',
            '수사 안내', '절차 안내', kind='guidance',
            limitation='AI 발언은 검증 전까지 미확인 주장임')
    elif tab == 'evidence':
        for evidence_id in sorted(acquired):
            e = acquired[evidence_id]
            chain = ctrl.state.acquired_chain.get(evidence_id, [])
            source = e.get('found', '')
            if chain: source += '  /  취득기록 ' + ', '.join(chain)
            add(e.get('name','확보 기록'), e.get('detail',''),
                source, evidence_id, id=evidence_id, kind='evidence',
                limitation=e.get('limitations',''))
        if not records:
            add('확보 기록 없음', '현장에서 조사해 확보한 자료만 목록에 나타납니다',
                '사건 기록', '대기', kind='guidance')
    elif tab == 'interview':
        # Claim IDs here are UI-local display anchors, not new evidence IDs
        for idx, statement in enumerate(world.claims[-60:]):
            speaker = world.suspects.get(statement['suspect_id'], {})
            add(speaker.get('name', '조사 대상'), statement['utterance'],
                '해당 인물의 면담 기록', '미검증 진술',
                id='statement:'+str(idx), kind='statement',
                limitation='이 발언만으로 객관적인 사건 사실이 확정되지 않음')
        if not records:
            add('기록된 진술 없음', '조사가 시작되면 실제 발언이 기록됩니다',
                '수사 기록', '대기', kind='guidance')
    elif tab == 'timeline':
        add('시각 대조 원칙', 'CCTV·휴대전화·진술 시각은 오차와 출처를 따로 검토하세요',
            '시간 대조 안내', '확인 필요', kind='guidance',
            limitation='한 자료의 시각만으로 사건 시간이나 범인을 단정할 수 없음')
        for evidence_id in sorted(acquired):
            e = acquired[evidence_id]
            add(e['name'], e.get('detail',''), e.get('found',''),
                '확보 자료', id=evidence_id, kind='timeline_source',
                limitation=e.get('limitations',''))
    elif tab == 'report':
        add('4개 독립 입증 축', '접근·시간 / 동기 / 현장 연결 / 대안 배제',
            '사건 보고 기준', '검토 요건', kind='guidance',
            limitation='자료 개수만으로 승인되지 않으며 실제 재판 판단과 다름')
        add('최종 제출', '확보 자료와 신문 절차의 적합성은 서버에서 다시 검증합니다',
            '수사보고서', '검토 전', kind='guidance')
    elif tab == 'settings':
        add('접근성', '카메라 움직임과 자막 표시, 화면 크기를 조절할 수 있습니다',
            '로컬 환경설정', '설정', kind='guidance')
    return {'tab': tab, 'records': records, 'context': '', 'connection': 'LOCAL PREVIEW — 실제 게임 미검증'}

if __name__=='__main__':serve()


def evidence_cards(ctrl):
    """Player-side evidence cards: only acquired items, with provenance and limitations."""
    out=[]
    for e in ctrl.world._canon['evidence']:
        if e['id'] in ctrl.world.available_evidence:
            out.append({'id':e['id'],'name':e['name'],'detail':e['detail'],'source':e['found'],
                        'limitation':e['limitations'],'strength':e['strength'],
                        'chain':ctrl.state.acquired_chain.get(e['id'],[])})
    return out
