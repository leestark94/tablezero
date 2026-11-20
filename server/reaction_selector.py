"""Deterministic, evidence-neutral acting variants, never used to infer guilt."""
from __future__ import annotations
import hashlib

REACTIONS={
 ('wrong_accusation','s1'):[
  ('s1_furious',[('interview','강도현이 의자에서 반쯤 일어나다가 멈춘다','아니라고 했잖아요, 몇 번이나'),('interview','컵에 닿을 듯한 손이 제자리로 돌아온다','제가 그때 나가는 거, 찍혀 있었잖아요')]),
  ('s1_numb',[('interview','강도현이 한참 동안 바닥만 본다','…됐습니다'),('interview','조용히 물컵을 책상 끝으로 민다','말해 봐야 안 믿으실 거잖아요')]),
  ('s1_cold',[('interview','강도현이 입술을 다물고 서류를 밀어놓는다','변호인하고 얘기하겠습니다'),('interview','의자 다리만 짧게 울린다','더 하실 말 없으면 가보겠습니다')]),
 ],
 ('wrong_accusation','s3'):[
  ('s3_indignant',[('interview','박현수가 두 손을 무릎 위에서 세게 모은다','내가 신고한 사람이에요'),('interview','시선을 돌린다','하, 진짜 기가 막히네')]),
  ('s3_afraid',[('interview','박현수가 뻣뻣한 자세로 형사를 쳐다본다','제가 뭘 잘못했습니까'),('interview','잠깐 말문이 막힌다','집에는 언제 가요')]),
 ],
 ('substantiated','s2'):[
  ('s2_composed',[('interview','이서연이 종이에 고정된 시선을 들지 않는다','자료는 잘 모으셨네요'),('interview','손가락이 컵을 잡았다가 놓는다','그래서, 이제 어떻게 되는 거예요')]),
  ('s2_brittle',[('interview','이서연이 코로 짧게 숨을 들이쉰다','그날… 그냥 안 갔어야 했어요'),('interview','고개를 숙이지만 눈물은 보이지 않는다','수연이한테 미안해요')]),
  ('s2_incongruous',[('interview','이서연이 뜬금없이 짧게 웃었다가 곧 그친다','웃겨서 웃는 거 아니에요'),('interview','컵 옆에 손을 뉘고 표정은 지운다','뭐라고 해야 할지 모르겠어서 그래요')]),
 ],
 ('underproved_true_person','s2'):[
  ('s2_boundaries',[('interview','이서연이 약간 몸을 뒤로 물린다','더 말씀드릴 게 없어요'),('interview','서류를 넘기지 않고 그대로 둔다','변호인하고 먼저 얘기하겠습니다')]),
  ('s2_question',[('interview','이서연이 질문을 조심스럽게 되돌린다','그걸로 제가 뭘 했다는 게 되나요?'),('interview','모서리가 휘어진 종이를 본다','확인할 거 있으면 확인하세요')]),
 ],
 ('no_accusation','any'):[
  ('desk_responsible',[('desk','형사가 지목란을 비워 두고 저장한다','확인 안 된 건 빼겠습니다'),('desk','동료가 서류를 받아 든다','그게 낫겠네요')]),
  ('desk_tired',[('desk','모니터가 꺼지고 복도 걸음소리만 남는다','오늘은 여기까지죠'),('desk','형사가 보고서를 다시 펼친다','내일 기록부터 다시 보죠')]),
 ],
 ('procedural_defect','any'):[
  ('desk_chain',[('desk','동료가 봉인 번호를 손가락으로 짚는다','이 번호가 접수기록이랑 안 맞아요'),('desk','형사가 조용히 펜을 내려놓는다','그건 빼고 다시 봐야겠네요')]),
 ]
}

class ReactionSelector:
    def __init__(self,world):self.world=world
    def choose(self,ending_code,accused_id, *, salt='case001'):
        options=REACTIONS.get((ending_code,accused_id)) or REACTIONS.get((ending_code,'any'))
        if not options:return None
        # Previous actual dialogue affects color, not correct identity or evidence thresholds
        history='|'.join(f"{c['suspect_id']}:{c['mode']}" for c in self.world.claims[-8:])
        token=f'{salt}|{ending_code}|{accused_id}|{history}'
        idx=int(hashlib.sha256(token.encode('utf-8')).hexdigest()[:8],16)%len(options)
        name,beats=options[idx]
        return {'variant_id':name,'beats':[{'location':a,'staging':b,'subtitle':c}
                                          for a,b,c in beats]}
