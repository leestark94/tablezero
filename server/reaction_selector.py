"""Deterministic, evidence-neutral acting variants, never used to infer guilt."""
from __future__ import annotations
import hashlib

REACTIONS={
 ('wrong_accusation','s1'):[
  ('s1_furious',[('interview','강도현이 의자에서 반쯤 일어나다가 멈춘다','제가 그 시간에 어디 있었는지 기록 보셨잖아요'),('interview','컵에 닿을 듯한 손이 제자리로 돌아온다','제가 한 거하고 안 한 거는 구분하셔야죠')]),
  ('s1_numb',[('interview','강도현이 한참 동안 바닥만 본다','…됐습니다'),('interview','조용히 물컵을 책상 끝으로 민다','말해 봐야 안 믿으실 거잖아요')]),
  ('s1_cold',[('interview','강도현이 입술을 다물고 서류를 밀어놓는다','변호인하고 얘기하겠습니다'),('interview','의자 다리만 짧게 울린다','더 하실 말 없으면 가보겠습니다')]),
 ],
 ('wrong_accusation','s2'):[
  ('s2_still',[('interview','이서연이 손을 무릎 위에 포갠 채 움직이지 않는다','제가 나올 때 수연이는 괜찮았어요'),('interview','시선을 서류 모서리에 둔다','그걸로 제가 했다는 게 되나요')]),
  ('s2_boundaries',[('interview','이서연이 약간 몸을 뒤로 물린다','더 말씀드릴 게 없어요'),('interview','서류를 넘기지 않고 그대로 둔다','변호인하고 먼저 얘기하겠습니다')]),
 ],
 ('substantiated','s3'):[
  ('s3_paper',[('interview','박현수가 책상 위 서류 조각을 오래 내려다본다','그 뒷장을… 저는 못 봤어요'),('interview','손가락이 종이 끝을 만지다 멈춘다','이제 어떻게 되는 겁니까')]),
  ('s3_quiet',[('interview','박현수가 등받이에 기대지 못하고 앉아 있다','신고는 제가 했습니다'),('interview','한참 동안 말이 없다','…변호인 부르겠습니다')]),
  ('s3_incongruous',[('interview','박현수가 짧게 웃었다가 곧 그친다','웃겨서 웃는 거 아닙니다'),('interview','표정을 지운다','뭐라고 해야 할지 모르겠어서요')]),
 ],
 ('underproved_true_person','s3'):[
  ('s3_boundaries',[('interview','박현수가 팔짱을 끼고 형사를 본다','제가 신고한 사람이에요. 그걸로 뭘 하셨다는 거죠'),('interview','서류를 밀어 둔다','증거 있으면 가져오세요')]),
  ('s3_question',[('interview','박현수가 질문을 되돌린다','그 시간에 제가 거기 있었다는 걸 뭐로 보셨습니까?'),('interview','의자를 조금 뒤로 뺀다','확인할 거 있으면 확인하세요')]),
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
