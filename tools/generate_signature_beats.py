"""Cinematic beat candidates. Not executed in Unity until all animations/audio/physics are authored.
Focus on acting and causality, not raw effects count.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# scene|trigger|tag|visual/acting|sound|physics|camera|conditions|assets|priority
raw='''
room302|enter_once|FIRST_ROOM_AIR|문을 열고 형사가 걸음을 잠깐 늦추며 손전등 높이를 낮춘다|복도 소음이 닫히고 냉장고 모터가 들어온다|현관문 손잡이 실제 감쇠|걷는 시점 유지, 1회 0.04 강도 이하|door_opened|door_rig,fp_arms,ambience_room,door_audio|hero
room302|first_view|BLOOD_RECOGNITION|형사가 한 번 말을 삼키고 바닥과 생활용품을 번갈아 본다|짧은 호흡, 모터·실외기 소음은 유지|없음|시야 강제 회전 없음|blood_visible|fp_breath,blood_material|hero
room302|first_view|UNMADE_BED|난장판보다 흐트러진 이불과 취침 공간이 먼저 눈에 걸린다|침구 천 마찰음만|없음|사용자 시선 우선|bed_visible|bed_highpoly,cloth_audio|quiet
room302|approach|BLOOD_EDGE_DETAIL|바닥 흔적 근접 촬영에서 재질·마른 부분·젖은 부분의 차이를 관찰한다|실내음만|카메라/장비와 충돌 없음|부드러운 포커스 전환|look_at_trace|blood_material,focus_tool|hero
room302|drawer_open|BED_DRAWER_RESIST|협탁 서랍이 처음엔 약하게 걸렸다가 부드럽게 열린다|레일 마찰과 목재 접촉|실제 슬라이드/충돌|카메라 흔들림 없음|hand_contact|bed_drawer_rig,fp_hand_IK,drawer_sfx|micro
room302|cabinet_open|KITCHEN_CABINET_HINGE|한쪽 상부장 경첩이 뻑뻑하게 움직인다|경첩 고주파 마찰|실제 회전 제한|시점 고정|hand_contact|kitchen_cabinet_rig,cabinet_audio|micro
room302|fridge_open|FRIDGE_LIGHT|문이 열리고 냉장고 안쪽 작은 등이 켜진다|문 개스킷 흡착음과 팬 소음 변화|회전 도어|카메라 자동 줌 금지|fridge_door_open|fridge_rig,fridge_audio,light_proxy|micro
room302|fridge_close|FRIDGE_COMPRESSOR|냉장고 문을 닫자 잠깐 모터가 다시 우웅거린다|실내 공간감 반영|문 물리 접촉|자연시점|fridge_door_close|fridge_rig,fridge_audio|ambient
room302|bath_enter|BATH_REVERB|화장실 문을 밀자 환풍기와 타일 잔향이 가까워진다|팬 루프+현장 반향 전환|문 경첩|일반 시점|bath_door_open|bath_door_rig,bath_audio,bath_reverb|hero
room302|bath_sink|WATER_DRIP|수도 손잡이를 돌렸을 때 마지막 물방울이 떨어진다|배수구 낙수음|실제 물줄기 파티클|주인공 조준 유지|faucet_touched|bath_faucet_rig,water_fx,drip_sfx|micro
room302|bath_cabinet|MIRROR_CABINET|거울장을 열자 거울 반사가 움직임을 따라간다|작은 문 울림|실제 도어 회전|시선 강제 이동 없음|cabinet_open|mirror_cabinet_rig,reflection_probe,hinge_sfx|micro
room302|footstep|SHOE_SCuff|형사의 덧신이 현관턱에서 짧게 미끄러진다|고무·타일 마찰음|발접촉|카메라 흔들림 없음|on_entry_threshold|fp_walk,shoe_step_sfx|ambient
room302|item_rotate|CUP_BASE|머그컵 바닥 각인의 사용 흔적을 가까이 확인한다|도자기 작은 마찰|물건 회전 클램프|뷰 포커스만|cup_inspected|cup_mesh,fp_grip_IK,ceramic_sfx|micro
room302|item_rotate|DELIVERY_LABEL|배달 봉투를 빛에 가까이 놓으면 인쇄된 글씨가 읽힌다|종이 구김|봉투 손 접촉|과장 줌 없음|bag_inspected|bag_mesh,print_texture,bag_rustle|hero
room302|photo_capture|SHUTTER_SUBTLE|촬영하는 손이 폰/카메라를 안정적으로 들고 기록한다|실제 촬영 버튼 소리|가벼운 장비 물리|제어 중임을 표시|camera_used|fp_camera_rig,shutter_sfx|micro
room302|open_bed|LINEN_WEIGHT|이불을 젖히면 아래 매트리스가 드러나고 주름이 늦게 풀린다|면직물 흔들림|침구 저렴한 천공 파편 금지|플레이어 카메라 자유|blanket_held|cloth_rig,fp_grip_IK,linen_sfx|hero
room302|window_open|WINDOW_NIGHT|창을 열자 오토바이 소리와 실외기가 더 크게 들린다|실외음 자연 크로스페이드|창문 리그|카메라 자유|window_latch_released|window_rig,exterior_audio,window_sfx|quiet
room302|ambient_safe|NEIGHBOR_TV|벽 너머 TV의 작은 대사 소리가 잠깐 들린다|저역통과 필터|없음|카메라 무반응|player_idle|neighbor_tv_audio|quiet
room302|ambient_safe|UPSTAIRS_STEP|윗집의 발걸음 두 번이 실내 정적에 섞인다|잔향 있는 발소리|없음|카메라 무반응|player_idle|upstairs_steps|ambient
room302|ambient_safe|HALL_FOOTSTEPS|복도에서 발소리가 멈췄다가 다시 멀어진다|도어 너머 발소리|없음|카메라 무반응|player_idle|hall_step_audio|quiet
hall|enter_once|SENSOR_DELAY|복도 센서등이 한 박자 늦게 켜진다|형광등 스타트 소리|실제 광량 변화|플레이어 시선 유지|night_entry|hall_light,fluorescent_audio|hero
hall|neighbor|DOOR_QUIET|문고리가 아주 짧게 돌아갔다가 멈춘다|도어 래치|진짜 도어 리그|플레이어 자유|neighbor_door_visible|neighbor_door_rig,door_latch|micro
hall|intercom|INTERCOM_STATIC|인터폰 눌림 뒤 한 박자 무음이 흐른다|미세한 전기음|버튼 작동|카메라 정지|intercom_pressed|intercom_rig,intercom_sfx|micro
hall|stair|STAIRS_SHADOW|계단에 내려오는 그림자가 잠깐 비친다|계단 발소리|실제 인물/광원 필요|시점 유지|approved_npc_pass|npc_walk,stair_lighting,steps|quiet
interview|start|RECORDER_ON|녹음기 단추를 누른 형사의 손이 테이블에서 천천히 떨어진다|녹음 버튼 작은 클릭|레코더 버튼 실제 누름|1인칭 앉은 시점|interview_started|recorder_rig,fp_seated_hands,click_sfx|hero
interview|quiet|BREATH_IN|용의자가 답변 전 고개를 숙이고 숨을 들이쉰다|호흡 실감, 룸톤 유지|없음|정면 응시 강제 없음|suspect_answer_pending|npc_breath_motion,breath_sfx|micro
interview|question|MISHEARD_TIME|용의자가 특정 시각을 다시 물으며 얼굴보다 종이를 먼저 본다|목소리 뒤 종이 마찰음|종이 소품 작동|카메라 고정|time_question_heard|npc_look_paper,paper_rustle|dialogue
interview|question|HAND_TWITCH|방향을 바꾼 질문에 손등의 작은 근육 긴장이 보인다|룸톤만|없음|줌 금지|question_changed_topic|npc_hand_rig|micro
interview|question|FINGER_TAP|용의자가 대답을 정리하는 동안 손가락으로 두 번 두드린다|손가락 탁탁|실제 테이블 접촉|카메라 무반응|deliberation|finger_tap_motion,table_tap_sfx|micro
interview|question|CHAIR_SHIFT|용의자가 자세를 고쳐 앉아 의자가 미세하게 운다|의자 가죽/다리 소리|물리 연출과 접촉 동기|카메라 무반응|high_discomfort|npc_chair_motion,chair_sfx|micro
interview|question|REPEATED_WORD|용의자가 형사의 단어 하나를 반복하며 시간을 번다|짧은 말 반복|없음|원래 구도|suspect_strategy_counter|npc_delivery_audio|dialogue
interview|evidence_present|EVIDENCE_SLIDE|형사의 손이 서류 한 장을 천천히 밀자 용의자 손이 멈춘다|종이 마찰+멈추는 의자 소리|서류 실제 테이블 접촉|컷 없이 팔 따라 소폭 이동|presented_verified_evidence|paper_mesh,fp_present_IK,npc_hand_stop,paper_slide_audio|hero
interview|evidence_present|CUP_STOP|컵을 만지던 손가락이 제출한 서류를 보고 멈춘다|컵 도자기 접촉 중단|컵 흔들림 현실적|인물 손 포커스|evidence_seen|npc_cup_touch,cup_mesh,ceramic_audio|micro
interview|evidence_present|PAPER_PUSHBACK|용의자가 서류를 읽지 않고 조용히 밀어낸다|종이 소리|서류 물리 이동|평범한 구도|avoid_document|npc_paper_push,paper_mesh,paper_audio|hero
interview|answer|NO_INSTANT_CONFESSION|불리한 자료 앞에서 용의자가 숨 고르고 일부 사실만 인정한다|짧은 쉼 후 말|없음|강제 연기 금지|partial_admission|npc_pause_motion,voice_audio|dialogue
interview|answer|LONG_SILENCE|양쪽 모두 한동안 말을 하지 않는 동안 방의 작은 환풍기 소리가 들린다|팬+녹음기 잡음|없음|프레임 정지 없음|both_silent|roomtone,breath_sfx|hero
interview|answer|VOICE_THIN|용의자의 목소리가 낮아지지만 또박또박 반문한다|변화하는 톤|없음|카메라 흔들림 없음|suspect_counter|voice_audio|dialogue
interview|player_strike|PLAYER_TABLE_STRIKE|형사 손이 실제 테이블 접촉 프레임에 부딪히고 용의자가 움찔한다|녹음기 피크·테이블 충격음|컵·서류에 물리 충격|한 번만 0.12 이내 임펄스|pressure_tactic_approved|fp_slam_clip,table_rigidbody,glass_rigidbody,mic_overload|hero
interview|npc_strike|SUSPECT_TABLE_STRIKE|용의자가 갑자기 손바닥으로 테이블을 쳤다 바로 손을 거둔다|저역의 단발 충격|컵 물리·팔 리깅 접촉|한 번만 0.12 이내 임펄스|npc_action_approved|npc_slam_clip,table_rigidbody,glass_rigidbody,table_hit_sfx|hero
interview|player_wait|REMAIN_SILENT|형사가 질문을 반복하지 않자 용의자가 시선을 들었다 내린다|호흡/무음 유지|없음|시점 자유|player_waited|npc_eye_motion,breath_sfx|micro
interview|raise_voice|RAISED_VOICE_AFTER|형사가 목소리를 올리자 용의자가 곧바로 항의하지 않고 먼저 숨을 멈춘다|목소리/의자 소리|없음|소폭 포커스|player_raised_voice|npc_discomfort_motion,voice_audio|dialogue
interview|lawyer|REQUEST_COUNSEL|용의자가 변호인 참여를 요청하자 형사 손이 녹음기를 가리킨다|녹음기 버튼 눌림|레코더 실제 멈춤|카메라 정면|counsel_requested|npc_counsel_motion,recorder_rig,button_audio|hero
interview|exit|STAY_SEATED|조사가 끝났는데 용의자가 바로 일어서지 않고 종이를 본다|의자/정적|없음|플레이어가 직접 퇴장|interview_finished|npc_linger_motion,roomtone|quiet
interview|exit|CHAIR_PUSH|용의자가 의자를 밀고 천천히 일어선다|의자 바닥 긁힘|가구 실루엣 이동|시점 고정|interview_finished|npc_stand_motion,chair_rig,chair_sfx|hero
interview|unexpected|HALL_RING|정적 뒤 조사실 밖 전화가 두 번 울렸다 끊긴다|벽 건너 전화벨|없음|카메라 반응 없음|safe_window|hall_phone_ring|ambient
interview|unexpected|RECORDER_BATTERY|녹음기 표시등이 순간 낮아지고 다시 안정된다|작은 전기음|녹음 상태 로그와 일치|카메라 무반응|recorder_low_battery|recorder_mesh,recorder_sfx|quiet
interview|unexpected|PAPER_CORNER|용의자가 서류 모서리를 접었다 다시 편다|종이 마찰|진짜 종이 접힘 포즈|클로즈업 강제 금지|nervous_habit|npc_paper_corner,paper_audio|micro
interview|unexpected|CUP_CONDENSATION|컵을 살짝 밀자 테이블에 물자국이 남는다|유리/물 소리|응결 머티리얼과 소품 이동|카메라 무반응|cup_moved|glass_condensation,cup_slide_sfx|micro
desk|event_received|NEW_CONTACT_TRACE|참고인 연락 기록이 기존 자료 옆에 새 번호로 접수된다|짧은 업무용 벨|서류/기록 실제 갱신|평상 카메라|world_contact_logged|case_ui,phone_sfx|hero
desk|timeline_update|TIME_LINE_UNCERTAINTY|서로 다른 두 시계 표시가 근접하지만 완전히 일치하지 않는다|조용한 종이 넘김|없음|UI 포커스|compare_two_sources|timeline_ui,paper_sfx|micro
desk|final_report|PRINTER_SLOW|신고 자료와 감정 기록을 다시 한 장씩 확인하고 인쇄를 기다린다|프린터 기계음|실제 종이 이동|자연 화면|report_submitted|printer_rig,printer_sfx|hero
desk|wrong_accusation|INNOCENT_AFTERSHOCK|오인 지목된 사람이 창밖이 아니라 자신의 손을 한참 내려다본다|호흡/의자 작은 소리|없음|인물 연기 우선|wrong_accusation_resolved|npc_reaction_rig,roomtone|hero
desk|correct_but_weak|NOT_ENOUGH|보고서에 입증 미충족 항목이 남고 프린터가 그대로 멈춘다|컴퓨터 팬/복도 발소리|실제 문서 상태|카메라 고정|underproved_report|report_ui,roomtone|hero
desk|success|NO_TRIUMPH_MUSIC|정상 접수됐지만 형사는 몇 초 동안 보고서 서명을 바라본다|음악 대신 서류음/멀리 걸음|없음|관찰 시점|report_accepted|report_ui,paper_sfx|hero
desk|procedure|SEAL_NUMBER_ERROR|증거 봉인 번호가 맞지 않아 해당 자료 사용이 보류된다|펜 내려놓는 소리|실제 서류 소품|컷 없음|chain_mismatch|report_ui,pen_audio|hero
'''

def build():
    rows=[]
    for line in raw.strip().splitlines():
        if not line.strip():continue
        cols=line.split('|')
        if len(cols)!=10:raise ValueError('Expected 10 columns: '+line)
        scene,trigger,name,visual,audio,physics,camera,conditions,assets,priority=cols
        rows.append({'beat_id':'V11_'+name,'scene':scene,'trigger':trigger,'performance':visual,
                     'sound_direction':audio,'physical_result':physics,'camera_rule':camera,
                     'conditions':conditions.split(','),'required_assets':assets.split(','),
                     'priority':priority,'cooldown_s':180 if priority=='hero' else 90,
                     'per_session_limit':1 if priority=='hero' else 2,
                     'world_mutation':'NEVER_DIRECT_FROM_CUE',
                     'authored_unity_clip_status':'NOT_VERIFIED'})
    assert len({b['beat_id'] for b in rows})==len(rows)
    return {'version':'11','description':'Additional candidate beats; never report as playable until clips, audio, physical collisions and runtime are verified','beats':rows}
if __name__=='__main__':
    data=build(); dest=ROOT/'data'/'v11_signature_cinematic_beats.json'
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(len(data['beats']),'shots authored',dest)
