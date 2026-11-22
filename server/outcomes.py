"""Branching outcomes: never infer guilt from emotion; evidence proof is authoritative."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ENDING_SCRIPTS = {
 # V21: the formal report closes the case. Lines never name the accused (accused-specific acting comes from reaction_selector)
 'substantiated': [
   ('desk','수사보고서에 마지막 자료를 첨부한다','검토 요청'),
   ('desk','정정서 뒷장 사본이 보고서 맨 뒤에 철해진다','이게 그날 고치던 거였네요'),
   ('corridor','복도 끝에서 낮은 통화음이 들린다','자료는 다 정리됐습니다'),
   ('desk','사건 파일 상태가 바뀐다','입증 요건 충족 · 수사 의견 송치 검토'),
   ('stinger','인쇄기에서 다음 장이 천천히 밀려나온다','판결이 아니라 수사 의견이다'),
 ],
 'wrong_accusation': [
   ('desk','보고서에 반려 표시가 남는다','지목한 사람과 치명상이 이어지지 않습니다'),
   ('corridor','조사실 문이 닫히고 복도 생활 소음이 돌아온다','그날 밤 다른 잘못이 있었다고 다 같은 건 아니죠'),
   ('stinger','사건 파일이 다른 팀으로 넘어간다','이 보고서로는 끝낼 수 없다'),
 ],
 'underproved_true_person': [
   ('desk','현장 연결과 대안 배제 항목 중 비어 있는 축을 확인한다','심증은 있지만 입증은 부족합니다'),
   ('corridor','출입문이 닫히며 복도 생활 소음이 돌아온다','이대로는 송치 못 합니다'),
   ('stinger','사건 파일이 재수사 대기로 넘어간다','이름만으로는 사건이 닫히지 않는다'),
 ],
 'no_accusation': [
   ('desk','빈 지목란이 화면에 남는다','오늘은 지목하지 않겠습니다'),
   ('corridor','야간 근무자가 커피 자판기 버튼을 누른다','확인 안 된 걸로 밀어붙일 순 없죠'),
   ('stinger','사건이 미제로 분류된다','열린 채로 남는다'),
 ],
 'procedural_defect': [
   ('desk','증거 봉인 일련번호가 맞지 않는다','이거 접수 기록이랑 다릅니다'),
   ('desk','해당 증거가 입증 경로에서 보류 처리된다','자료 적격성 확인 필요'),
   ('stinger','사건이 재검증을 위해 보류된다','흔적도 절차가 없으면 증거가 되기 어렵다'),
 ],
}

# V21 result types (the case is closed when the report is filed, so the category may be shown)
V21_RESULT={'substantiated':'SOLVED_PROVEN','underproved_true_person':'CORRECT_UNPROVEN','wrong_accusation':'WRONG_ACCUSATION',
            'procedural_defect':'PROCEDURAL_HOLD','no_accusation':'UNRESOLVED'}

@dataclass(frozen=True)
class Outcome:
    code: str
    evidence_sufficient: bool
    correct_identity: bool
    report_accepted: bool
    can_continue: bool
    missing_axes: tuple[str,...]
    montage: tuple[tuple[str,str,str],...]

class OutcomeDirector:
    def __init__(self, world):self.world=world
    def submit(self, accused_id: str | None, evidence_ids, *, chain_defects=(), submit_final=True) -> Outcome:
        # Missing record cannot turn into valid evidence by raising emotion/suspicion
        if accused_id is None:
            return self._compose('no_accusation',False,False,True,())
        report=self.world.evaluate_report(accused_id,evidence_ids)
        missing=tuple(axis for axis,ok in report['axes'].items() if not ok)
        canon_identity=self.world._canon['case_result_logic']['identity']
        identity_correct=accused_id==canon_identity
        if chain_defects:
            return self._compose('procedural_defect',False,identity_correct,True,missing)
        if not identity_correct:
            return self._compose('wrong_accusation',False,False,True,missing)
        if missing:
            return self._compose('underproved_true_person',False,True,True,missing)
        return self._compose('substantiated',True,True,False,())
    @staticmethod
    def _compose(code, sufficient,correct,continue_case,missing):
        # V21: the formal report is submitted once; every final submission closes the case (no guess-and-retry)
        return Outcome(code,sufficient,correct,sufficient and correct,False,
                       tuple(missing),tuple(ENDING_SCRIPTS[code]))
    def reaction(self, outcome:Outcome,accused_id):
        from .reaction_selector import ReactionSelector
        return ReactionSelector(self.world).choose(outcome.code, accused_id)

    @staticmethod
    def public_projection(outcome:Outcome,reaction=None):
        # Deliberately omit correct_identity from public payload: would reveal culprit on failure
        result=V21_RESULT[outcome.code]
        return {'ending_code':result,'result':result,'report_accepted':outcome.report_accepted,
                'may_continue':outcome.can_continue,'missing_proof_axes':list(outcome.missing_axes),
                'beats':[{'location':a,'staging':b,'subtitle':c} for a,b,c in outcome.montage],
                'reaction':reaction or {'variant_id':'none','beats':[]}}
