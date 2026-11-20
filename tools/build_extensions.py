from pathlib import Path
import copy,json
ROOT=Path(__file__).resolve().parents[1]; p=ROOT/'data/case001_deep_beats_61.json'; old=json.loads(p.read_text(encoding='utf-8'))['beats'];new=[]
# List: id,scene,trigger,act,category,cue,flag,gest,sound,prop,camera,dramaturgy,author example
ROWS=[
 ('x01_fire_stair','hall','ambient','arrival','ambient_surprise','ambience.hallfootsteps','', '어깨 조정','계단 발소리가 멀어짐','계단문','시선만', '누군가가 가까이 있어도 의도는 모름','누구 내려오시나'),
 ('x02_sensordelay','hall','ambient','arrival','ambient_surprise','entrance.flicker_door','', '손전등 손 멈춤','센서등 지연음','센서등','가벼운 노출 변경','복도 평범함 속 작은 긴장','센서등이 왜 이렇게 늦게 켜져요'),
 ('x03_slippers','hall','inspect','arrival','scene','entrance.shoe_cover','shoe_pairs_visible','발 위치 변경','슬리퍼 스침','슬리퍼','시점 고정','생활 소품 자체가 사람을 말함','신발 몇 켤레였죠'),
 ('x04_urgent_radio','hall','ambient','arrival','procedural_interrupt','ambience.police_radio','radio_received','무전기 살짝 듦','무전기 잡음','무전기','시점 고정','실제 현장업무와 긴장감 연결','네, 지금 확인하고 있습니다'),
 ('x05_sink_drop','room302','ambient','exploration','ambient_surprise','scene.sink_drip','sink_unrepaired','미세한 고개 돌림','싱크대 물방울','싱크대','강제 컷 금지','사건과 무관한 소리도 현장 불안','수도 잠겼어요?'),
 ('x06_cold_meal','room302','inspect','exploration','scene','scene.spilled_drink','food_visible','손 멈춤','냉장고 윙','배달음식','초점 조정','시간의 흔적이지만 사망시간 확정 아님','이게 아직 그대로 있네'),
 ('x07_coffee_stain','room302','inspect','exploration','scene','scene.spilled_drink','table_stain_visible','장갑 손가락 회수','장갑 마찰','탁자 얼룩','지점 살피기','자극 없는 사소한 사실','커피 자국은 언제 생긴 걸까요'),
 ('x08_empty_chair','room302','inspect','exploration','scene','scene.photo_pause','vacant_chair_visible','시선 잠깐 멈춤','진공 같은 방 소음','빈 의자','움직임 최소','사람이 부재하는 감정','평소엔 여기 앉았겠죠'),
 ('x09_doorbell','room302','ambient','exploration','ambient_surprise','entrance.door_chain','hall_perimeter_open','몸 방향 선택','도어벨 낮은 소리','현관 벨','플레이어 컨트롤 유지','현장 밖 존재의 침입','누구 왔습니까'),
 ('x10_clock_mismatch','room302','inspect','redirection','evidence','evidence.evidence_compare','clock_mismatch_verified','기록 대조','종이 넘김','시계·기록','UI 두 시각 오버랩','시각은 교차 검증해야 함','저 시계가 좀 빠르네요'),
 ('x11_window_motor','room302','ambient','exploration','scene','scene.window_wind','window_accessible','커튼을 살짝 보기','원거리 오토바이','커튼','초점만','평범한 주거단지의 소리','여기서 차 소리 꽤 들리겠네요'),
 ('x12_neighbor_pry','hall','witness_start','first_contact','witness','entrance.neighbor_step','neighbor_present','손으로 선 막음','철문 굴러가는 소리','현관 철문','시점 유지','주민 보호 및 소문 경계','안에 들어가시면 안 돼요'),
 ('x13_witness_correct','hall','question','pressure','witness','psychology.no_answer','witness_recalled','손 놓음','바지 비빔','손수건','고정','뒤늦은 진술정정도 인간적인 행동','제가 그때 시간을 잘못 봤을 수도 있어요'),
 ('x14_career_call','desk','ambient','pressure','ambient_surprise','ambience.police_radio','external_call_approved','수화기 손','유선전화','수화기','절제','기관 밖 연락은 정해진 관계를 통해','네, 자료 요청 접수됐습니다'),
 ('x15_paper_printer','desk','world_event','redirection','world_event_echo','evidence.paper_flip','record_received','서류 잡기','인쇄기','인쇄기','고정','AI 승인 이벤트 또는 기록 확보 뒤에만','출력물 나왔네요'),
 ('x16_reinterview','interview','start_interview','redirection','interview','interview.chair_shift','reinterview_authorized','등받이 조정','의자 마찰','의자','최소 변화','재조사 때도 처음처럼 드라마틱하게 하면 안 됨','지난번 말씀부터 다시 확인할게요'),
 ('x17_chair_mic','interview','reply','pressure','interview','interview.chair_shift','microphone_armed','팔 모서리 스침','의자 바닥 소리','의자','고정','마이크에 들어오는 소리는 마이크 거리 기반','잠시만요'),
 ('x18_cup_stop','interview','reply','pressure','interview','interview.cup_touch','cup_prop_ready','컵 접촉 정지','컵 바닥 스침','컵','포커스 1프레임','손이 멈춘 이유를 단정하지 않음','그건…'),
 ('x19_s1_tap','interview','question','pressure','interview','interview.finger_tap','repeat_pressure_approved','손가락 두 번','탁자 두드림','탁자','고정','신경질적 행동, 유죄 힌트 아님','몇 번 얘기했잖아요'),
 ('x20_s2_subjectchange','interview','question','redirection','interview','interview.question_repeat','interview_legal','손깍지','숨','종이','고정','AI가 수사관의 지식 범위를 역탐문','다른 분은 뭐라셨어요'),
 ('x21_s3_hesitate','interview','question','first_contact','witness','interview.long_silence','interview_legal','의자 팔걸이 잡음','시계','의자','고정','증언 확신도 유연','그건 딱 잘라 말은 못 하겠어요'),
 ('x22_outside_shout','interview','ambient','pressure','ambient_surprise','ambience.hallfootsteps','corridor_busy','짧은 고개 이동','복도 급히 지나가는 소리','문','시선 선택','조사실 밖 소리는 평범한 업무일 수 있음','밖에 무슨 일이에요'),
 ('x23_counsel_wait','interview','end_interview','pressure','procedural_interrupt','interview.request_lawyer','counsel_requested','의자에서 거리 두기','서류 닫힘','종이','조사 중단','변호인 요청이 게임 실패가 아님','절차 확인하고 다시 진행하죠'),
 ('x24_witness_tears','interview','reply','pressure','witness','psychology.suspect_relief','witness_distressed','손수건 꺼냄','코 훌쩍','손수건','클로즈업 금지','눈물은 신빙성 판단의 기준 아님','그냥 빨리 집에 가고 싶어요'),
 ('x25_paper_tear','interview','reply','pressure','procedural_interrupt','interview.evidence_slide','temper_loss_verified','손목 힘','종이 구김','서류','카메라 흔들림 0','행동 결과가 소품 상태를 바꿔야 함','이거 왜 자꾸 보여줘요'),
 ('x26_glass_distant','interview','ambient','first_contact','scene','ambience.fluorescent_buzz','ventilation_running','숨 고름','멀리서 유리문','유리문','고정','조사실은 대체로 조용해야 함',''),
 ('x27_long_pause','interview','reply','redirection','interview','interview.long_silence','pause_permitted','손 놓음','벽시계','컵','고정','거짓말과 무관한 길고 실재하는 침묵','…'),
 ('x28_body_recenter','interview','reply','pressure','interview','interview.chair_shift','camera_mark_approved','조용한 자세 바꿈','옷 마찰','의자','고정','몸 움직임의 합리적 관성',''),
 ('x29_false_end_look','interview','reply','aftershock','interview','interview.gaze_lower','outcome_wrong_accusation','하체를 미세히 뺌','의자 발','의자','강제 역광 없음','억울한 사람의 상처는 다음 사건에도 남음','제가 아니란 말, 그렇게 안 믿어지세요'),
 ('x30_true_end_hand','interview','reply','aftershock','interview','interview.hand_clench','outcome_substantiated','서류 잡은 손을 늦게 놓음','손 떼는 마찰','서류','고정','잡았다는 환호 대신 상대의 균열','여기까지 알아보신 거예요'),
 ('x31_underdone_end','desk','world_event','aftershock','procedural_interrupt','evidence.paper_flip','outcome_underproved','빈 보고서 보완란','종이 바스락','파일','시선 정적','심증만으로 확정 불가','아직 한 줄이 비네요'),
 ('x32_noaccuse','desk','world_event','aftershock','procedural_interrupt','evidence.paper_flip','outcome_no_accusation','서류 봉함','도장 소리','서류','고정','합리적 유보도 플레이어 선택','더 확인하겠습니다'),
 ('x33_after_hours','hall','ambient','aftershock','ambient_surprise','ambience.hallfootsteps','case_review_done','코트 정리','새벽 청소 발소리','복도','고정','큰 사건 직후에도 사람들은 출근하고 청소한다','벌써 아침이네'),
 ('x34_cup_contact','interview','reply','pressure','interview','interview.table_slam','table_slam_approved_animation','손-테이블 접촉','마이크 진동','테이블·컵','미세 반응','애니메이션 접촉 키프레임과 소품 충돌을 묶는다','아, 아니라고요!'),
]
# Override mapping for a few existing ids if needed but do not invent base catalog IDs
baseids={b['id'] for b in json.loads((ROOT/'data/cinematic_catalog_82.json').read_text(encoding='utf-8'))}
for id,scene,trigger,act,kind,cue,flag,gest,sound,prop,camera,meaning,line in ROWS:
 if cue not in baseids:
  print('MISSING',id,cue);continue
 b=copy.deepcopy(old[0]);b.update({'id':id,'scene':scene,'trigger':trigger,'act':act,'kind':kind,
  'description':meaning,'original_v06_cue':cue,'performance':{'gesture':gest,'sound':sound,
  'prop':prop,'camera':camera,'duration_s':2.1,'animation_contact_event':'physical_touch' if 'table_slam' in cue else ''},
  'dramatic_purpose':meaning,'dialogue_example':line.rstrip('.'), 'actor_id':'any',
  'requires_flags':[flag] if flag else [],'forbids_flags':[], 'requires_evidence_ids':[],
  'requires_visible_world_event':'','required_reply_modes':[], 'question_intent':'',
  'max_per_session':1,'cooldown_s':150.0,'priority':40,
  'world_mutation':'NEVER_FROM_CUE','guilt_hint':'NONE','evidence_creation':'NONE'})
 if kind=='world_event_echo':
  b['requires_visible_world_event']='prepare_statement'
 new.append(b)
# No server-authoritative outcome flags should ever be sent from UI
combined=old+new
(ROOT/'data/case001_director_beats.json').write_text(json.dumps({'schema':'tablezero.case001.beats.v1','beats':combined},ensure_ascii=False,indent=2),encoding='utf-8')
print('V07',len(old),'new',len(new),'total',len(combined))
