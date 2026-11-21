from pathlib import Path
import json,csv,collections,shutil
R=Path('/mnt/data/TABLE_ZERO_V21_FINAL_MASTER')
# evidence tuples: id, title, source family, props, finding, nonproven, acquisition, confrontation, contaminated_by
E=[
('V21-E01','20:47 배달 영수증 및 배달업체 기록','DELIVERY',['LV-001','LV-037'],'20:47 배달, 음식은 피해자 거주지 도착','식사 인원, 방문자, 범행시각','현장 봉투 확인→필요시 업체 기록 원본 대조','세 용의자의 식사/방문 설명은 별도 확인','소품 이동/음식 섞임'),
('V21-E02','공동현관·복도 CCTV 원본','CCTV',['CR-006'],'강 21:12 입·21:21 퇴, 이 21:39 접근·21:49 퇴장. 301→302 일부 시야 밖','내부 폭행, 301→302 경로, 미촬영 구간에 사람이 없었음','관리실 제공→원본 보존→카메라 광학 시야·시간오차 대조','강·이의 출입 자체를 확인하지만 죄/무죄 결론은 따로','시각 편차/압축/해상도'),
('V21-E03','박현수 22:07 신고 녹취','DISPATCH',['CR-003'],'박의 신고 내용·접수 시각·최초 진술','정말 22:07 처음 피해자를 봤는지','112 초기 접수 자료·정확한 녹취','박의 신고시각=최초 발견시각이라는 가정 교차','신고자가 놀라 시각을 부정확하게 말할 수 있음'),
('V21-E04','복도 환경음 녹음(선택·불확실)','HALL_AUDIO',['CR-002','CR-003'],'두 개의 충격 가능성/소음 시각의 참고, 신원 미확정','사람·가해자 자동 식별, 정확한 범행행위','박의 동의 또는 정당한 확보와 음원 원본검사. 미확보해도 보고 가능','추가 진술 대조용; 박 보유 녹음은 자동 제출하지 않음','녹음 시계·소리 원인·녹음 적법성'),
('V21-E05','피해자 왼팔 접촉 흔적','MEDICAL',['LV-027'],'팔을 강하게 붙잡거나 접촉한 정황이 의학 기록과 부합 가능','강이 그때 붙잡았다는 정확한 가해자·분 특정','의료 기록·증상 소견과 외부 진술 대조','강이 손댄 적 없다는 진술과 대조','부상 발생시점/개인차'),
('V21-E06','파손 휴대전화 외형과 현장 위치','SCENE_PHONE',['LV-027'],'휴대전화는 사망 전 파손되어 있었고 잠금 상태에서도 기능이 일부 유지','누가 직접 던졌는지/정확한 파손시각','현장 사진→원형·바닥 파편 위치→법적 디지털 분석','강 팔 접촉과 파손경위 질문','파손 이전 손상/이송 중 물품 이동'),
('V21-E07','피해자 휴대전화 통화기록·21:50 음성메모','PHONE_DIGITAL',['LV-027'],'21:34 이와 통화, 21:50~51 수연 목소리 업무메모 가능; 이후 살아 있었다는 근거','메모 원본 검증 없이는 작성자·시각 확정, 살인범 식별','권한 확인·압수 적법성→포렌식→파일 무결성·기기시각·음성 대조','서연 21:49 퇴장 뒤 수연 생존, 박 방문 목적 추론','메타데이터 조작 가능성, 앱 저장지연, 기기시계 편차'),
('V21-E08','깨진 네 사람 사진 액자·유리 파편','SCENE_GLASS',['LV-029','LV-012'],'사건 현장에서 사진 액자 유리 깨짐, 손 상처와 부합 가능','치명상 행위나 정확한 발생시각','현장 사진·안전 조치·필요시 파편 대조','서연의 21:42 다툼을 들춰냄','구급 구조/이동 때 추가 파손 가능'),
('V21-E09','두 부상군의 의학적 구별','MEDICAL',['LV-007','LV-040'],'오른손바닥 열상과 두부 치명상은 서로 다른 기전일 가능성','두 손상 각각 정확한 분·가해자 이름','의료진 소견·감정절차→현장 혈흔/탁자 대조','이 소매 혈액이 두부치명상을 뜻한다는 오판 검증','현장 출혈 혼합/후속 처치'),
('V21-E10','정정서 원본·구버전 배송자료·파편 대응','DOCUMENT',['LV-021','LV-022','LV-024','LV-038','LV-045'],'박 이름 허위 기재, 정수연이 뒤늦게 정정서 작성, 현장 서류와 별도 확보 조각이 같은 출처일 가능성','그 종이를 누가 언제 찢었는지 자동 확정','현장 원본 사진→발행/수정 기록→박 쪽 문서 적법 확인→파편 물리 대응','박의 서류 관련 진술, 도현이 보낸 건 구버전이었다는 사실','문서 보관경로/인쇄 시점/서류 겹침과 사후 오염'),
('V21-E11','공방 계좌·480만원 이체 원본','FINANCE',['LV-021','LV-038'],'이 무단 사용 480만원, 강이 수연에게 480만원 송금, 수연이 박에게 책임을 허위 전가한 동기적 맥락','누가 죽였는지','자발적 제출/정당한 금융자료 확보와 공방 문서 교차','3명 각자의 독립적 경제적 원한','금액 같다고 동일 거래 2건 자동 묶기 금지'),
('V21-E12','강도현→박현수 21:28 책임서 화면 메시지','MESSAGING',['LV-038','CR-003'],'박이 치명상 전에 구버전 문서 화면을 받았고 강은 바로 출근하지 않았음','강이 박에게 폭행을 지시했다는 증명 아님','수신자/발신자 원본 또는 동의·절차에 따른 확인','두 사람의 거짓말과 감정 자극을 각각 대조','스크린샷만으로 원본성 단정 금지'),
('V21-E13','강도현 21:51~22:00 근무 확인','WORKPLACE',['CR-006'],'근무지 출입·점검·동료 진술을 대조해 직접 치명상 가해 가능성을 낮춤','21:17 별도 폭력·21:28 서류 전송까지 무죄로 지움','사업장 출입 기록+점검로그+동료 확인 등 교차','강의 바로 출근 주장 일부 거짓과 21:57 현장 부재 분리','출입카드 대리 태깅 가능성 및 독립성 검증'),
('V21-E14','이서연 21:49 퇴장·21:55 편의점','MERCHANT',['CR-006'],'이서연이 21:55 편의점에서 결제했고 퇴장 기록과 연결','카드 결제만으로 이전 출입·치명상 가해/비가해 자동 확정','편의점 결제+원본 영상·진술 대조. CCTV와 별도 근원 확보','21:50 음성메모와 이 퇴장을 비교','카드 대리 사용 및 영상 인물 식별'),
('V21-E15','탁자 모서리·의자·혈흔 재구성','SCENE_IMPACT',['LV-007','LV-008','LV-040','LV-055'],'저상 탁자와 충돌하며 두부 손상이 발생할 수 있는 위치·흔적','정확한 밀친 사람·몇 분에 일어났는지','현장사진→예비소견→전문 혈흔/접촉 재구성→구급 흔적 제거','박과 이의 신체 접촉 주장과 구별','2회 사건 흔적·구급대 재배치'),
('V21-E16','박의 물증: 찢어진 원본 일부·의복 접촉 흔적','PARK_POSSESSION',['LV-022','LV-008'],'박이 정정 관련 서류 일부를 보유한 사실 및 실내 접촉 정황을 지원','언제 박이 현장에 있었는지 단독 확정, 살인 자동 증명','동의·영장 등 적법 경로→원본 사진·대응 조사→봉인/동일성 감정','처음엔 안 들어갔다는 주장·발견시각 설명과 교차','이전에 오갔던 관계, 수사 후 접촉, 자료 이전 전달 가능성'),
('V21-E17','119 구조 기록과 의료 사망 확인','EMS_HOSPITAL',['LV-041','LV-042'],'신고 뒤 처치/이송 과정, 현장 EMS 유래 흔적, 병원 사망 확인','치명상 가해자/분 자동 특정','구급일지·병원 기록을 적법 확인','현장의 끌린 흔적을 범행 은폐로 오인하지 않기','영상·기록 사후 정리 시각'),
('V21-E18','피해자와 박의 당일 방문 약속·연락','PHONE_DIGITAL',['LV-027','LV-022'],'사망 전부터 박이 방문하기로 한 사전 약속과 문서 전달 의도','실제 방문 완료 자동 확정','피해자/박 메시지 원본과 기기시각 교차, 타 출처 확인','박이 우연히 문 열려 신고했다는 주장 검증','E07과 같은 원본이면 독립증거 2개로 집계 금지'),
('V21-E19','과거 접촉 머그컵·주방 일반 흔적','OLD_CONTACT',['KI-016'],'과거 방문자 접촉 흔적이 남았을 수 있음','사건 당일 타살 가해/범행시각','사진·필요한 경우만 감식, 과거 방문 대안 고려','과잉감식 유혹을 플레이어가 판단','시간 특정 불가')]
records=[]
for id,title,fam,props,proves,doesnt,acquire,question,risks in E:
 records.append({'id':id,'title':title,'source_family':fam,'prop_ids':props,'could_support':proves,'does_not_prove':doesnt,'acquisition_and_integrity':acquire,'interrogation_bridge':question,'alternative_explanations_or_limits':risks,'mandatory':False})
rules={
'version':'21.0','case_id':'001','rule':'증거 ID는 게임 안에서 플레이어가 발견/확보한 사실까지만 열림. AI 발언만으로 감정 결과 생성 불가. 법적 증거능력 판단은 자문 전 게임용 논증 조건으로 취급.',
'evidence':records,
'forensic_queues':{'max_active_jobs_initial':2,'max_total_jobs':None,'note':'동시 2건 큐는 UI/대기 전략 테스트용. 총 의뢰 횟수 제한 없음. 고비용 의뢰만 시간을 지불. 예비견해와 정밀 회신 시프트를 구분.'},
'final_report':{
 'suspect_options':['s1','s2','s3','hold'],'true_culprit':'s3','dimensions':[
  {'id':'OPPORTUNITY','must_reconstruct':'수연 생존 21:49 이후~박 방문/치명상 약 21:57','possible_sources':['V21-E07','V21-E18','V21-E02','V21-E03']},
  {'id':'MOTIVE','must_reconstruct':'박 허위 배송 책임·21:28 구버전 메시지·당일 대면','possible_sources':['V21-E10','V21-E12','V21-E11']},
  {'id':'PHYSICAL_LINK','must_reconstruct':'박 실제 방문과 서류 접촉·두부 치명상·현장 물리 간 연결','possible_sources':['V21-E10','V21-E15','V21-E16','V21-E09']},
  {'id':'ALTERNATIVES','must_reconstruct':'강 21:57 근무지 교차확인, 서연 21:49 퇴장 후 수연 21:50 활동','possible_sources':['V21-E13','V21-E14','V21-E07','V21-E02']}
 ],
 'requirement':'각 축에 주장은 1개 이상, 확인된 원본에 연결된 근거, 대안설명 처리. PHYSICAL_LINK는 서로 다른 source_family 최소 2개 이상. 사건 진실을 맞히더라도 임의 대사/동기만으로 입증 불가.',
 'success':'s3 plus 4 dimensions plus source/integrity check',
 'failures':['CORRECT_UNPROVEN','WRONG_ACCUSATION','PROCEDURAL_HOLD','UNRESOLVED'],
 'no_confession_requirement':True},
'synthetic_evidence_forbidden':['CCTV 얼굴 AI 초해상도 확정','DNA로 접촉 날짜 맞히기','지문에서 21:57 시각 읽기','혈흔만으로 박 이름 표시','박이 자백하지 않으면 막다른 길','도현 메시지만으로 공범 입증'],
 'citation_reality_reference':[{'kind':'legal_rights','url':'https://www.law.go.kr/LSW/lsInfoP.do?lsId=001671','use':'형사소송법 진술거부·변호인 참여 확인'},{'kind':'forensic_procedure','url':'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000266474','use':'국과수 현장 혈흔형태·흔적 조사 일반 규정'}]
}
out=R/'04_EVIDENCE/EVIDENCE_CHAIN_AND_REPORT.json';out.write_text(json.dumps(rules,ensure_ascii=False,indent=2),encoding='utf-8')
# Exact 208 original manifest and V17 classification used as baseline
src=Path('/mnt/data/TABLE_ZERO_V16_FINAL_GAME_BIBLE/04_PROPS/ORIGINAL_208_MANIFEST.csv')
shutil.copy(src,R/'05_PROPS/ORIGINAL_208_MANIFEST.csv')
v17={row['prop_id']:row for row in csv.DictReader(open('/mnt/data/TABLE_ZERO_V17_RENEWAL/03_ALL_208_PROP_DECISIONS.csv',encoding='utf-8-sig'))}
orig=list(csv.DictReader(open(src,encoding='utf-8-sig')))
clusters={
'G01_출입통제':['CR-007','CR-008'],
'G02_복도카메라':['CR-006'],
'G03_301호동선':['CR-002','CR-003'],
'G04_현관인터폰':['CR-005','EN-001','EN-002','EN-021'],
'G05_전남친짐':['EN-016','BD-012'],
'G06_피해자폰':['LV-027'],
'G07_깨진액자':['LV-029','LV-012'],
'G08_좌식탁자충돌':['LV-007','LV-040','LV-055'],
'G09_뒤집힌의자':['LV-008'],
'G10_구급흔적':['LV-041','LV-042'],
'G11_배송영수증':['LV-001','LV-002','LV-003','LV-037','LV-053','LV-054'],
'G12_정산서':['LV-021','LV-038'],
'G13_봉투뒤쪽':['LV-022'],
'G14_노트북수정본':['LV-024'],
'G15_송장재고':['LV-045'],
'G16_머그컵':['KI-016'],
'G17_월패드녹화없음':['EN-018'],
'G18_현장시계':['LV-019']
}
clmap={pid:g for g,ids in clusters.items() for pid in ids}
core_ids=set(clmap)
collected=[]
for r in orig:
 v=v17.get(r['prop_id'],{});c=v.get('v17_class','AMBIENT');pid=r['prop_id']
 if pid in core_ids: status='CORE_HOTSPOT'
 elif c=='MERGE_INTO_PARENT':status='MERGE_INTERACTION'
 elif c=='REMOVE_FROM_SCENE_PROPOSAL':status='REMOVE_CANDIDATE'
 elif c in ('PRIMARY_IN_GROUP','OPTIONAL_SIMPLE'):status='CONTEXT_INTERACT'
 else:status='DECOR_STATIC'
 if status=='REMOVE_CANDIDATE':action='가정집 현실감·기존 모델 완성도를 실제 씬에서 확인한 후에만 제거'
 elif status=='MERGE_INTERACTION':action=f"부모 오브젝트 {v.get('merge_into') or '현장 메쉬'}의 상세 관찰로 묶고 별도 클릭 제거"
 elif status=='DECOR_STATIC':action='한국 원룸 생활소품 배치 유지, 필수 수사 클릭·증거점수 부여 금지'
 elif status=='CONTEXT_INTERACT':action='문·전등·서랍 등 자연스런 조작, 독립 핵심증거로 자동 처리 금지'
 else:action='실제 확대/읽기/사진/채취·선택적 감식/후속심문 연결'
 collected.append({
 'prop_id':pid,'zone':r['zone'],'name':r['name'],'original_index':r['original_index'],
 'v21_disposition':status,'investigation_cluster':clmap.get(pid,''),
 'revised_action_policy':action,'v17_disposition_reference':c,'merge_to':v.get('merge_into',''),
 'v21_story_link':','.join(e['id'] for e in records if pid in e['prop_ids']),
 'nonnegotiable':'기존 Unity 상태/자산 확인 전 실제 삭제 금지, 방문자 신원·살인 증명 자동 생성 금지'
 })
with (R/'05_PROPS/PROP_208_V21_CLASSIFICATION.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(collected[0]));w.writeheader();w.writerows(collected)
with (R/'05_PROPS/18_HOTSPOT_GROUPS.json').open('w',encoding='utf-8') as f:
 json.dump({'version':'21.0','note':'18개는 208개 물건을 의미있게 조사하기 위한 논리 그룹, 모든 그룹이 필수는 아님. 실제 클릭 개수는 씬 QA 후 확정','groups':[{'id':key,'prop_ids':ids,'primary_evidence_ids':sorted({e['id'] for e in records if any(p in e['prop_ids'] for p in ids)})} for key,ids in clusters.items()]},f,ensure_ascii=False,indent=2)
print('evidence',len(records),'props',len(collected),'counts',collections.Counter(r['v21_disposition'] for r in collected),'groups',len(clusters))
