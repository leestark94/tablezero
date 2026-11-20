"""Branching outcomes: never infer guilt from emotion; evidence proof is authoritative."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ENDING_SCRIPTS = {
 'substantiated': [
   ('desk','수사보고서에 마지막 자료를 첨부한다','검토 요청'),
   ('corridor','복도 끝에서 낮은 통화음이 들린다','자료는 다 정리됐습니다'),
   ('interview','이서연이 보고서를 한 번 내려다본다','그게… 다 남아 있었네요'),
   ('interview','그는 아니에요, 라고 말하려다 멈춘다','그 사람은 아니에요'),
   ('desk','사건 파일 상태가 변경된다','입증 요건 충족 · 검토 단계'),
   ('stinger','인쇄기에서 다음 장이 천천히 밀려나온다','사건은 여기서 끝난 게 아니다'),
 ],
 'wrong_accusation': [
   ('interview','강도현의 의자 다리가 바닥을 긁는다','제가 뭘 더 해야 믿으실 건데요'),
   ('interview','그가 말을 고르다 결국 고개를 든다','사람 죽은 거, 저도 압니다 근데 왜 제 말은 안 들어요'),
   ('desk','보고서에 보완 요청 표시가 남는다','입증 불충분 · 혐의 재검토'),
   ('corridor','같은 빌라에서 온 새 제보가 묻힌 채 쌓인다','아까 그쪽이 아니라니까요'),
   ('stinger','사건 파일을 다시 열 수 있다','끝난 게 아니다'),
 ],
 'underproved_true_person': [
   ('interview','이서연이 잠시 말을 멈추고 의자에 기대 앉는다','더 하실 말씀 없으시면 가도 될까요'),
   ('desk','현장 연결과 대안 배제 항목 중 누락된 축을 확인한다','심증은 있지만 입증은 부족합니다'),
   ('corridor','출입문이 닫히며 복도 생활 소음이 돌아온다','그 사람을 그냥 보낼 겁니까'),
   ('stinger','수사 파일이 미종결 상태로 남는다','확인되지 않은 사실이 남아 있다'),
 ],
 'no_accusation': [
   ('desk','빈 지목란이 화면에 남는다','오늘은 지목하지 않겠습니다'),
   ('corridor','야간 근무자가 커피 자판기 버튼을 누른다','확인 안 된 걸로 밀어붙일 순 없죠'),
   ('stinger','자료 수집 동선이 다시 열린다','수사 계속'),
 ],
 'procedural_defect': [
   ('desk','증거 봉인 일련번호가 맞지 않는다','이거 접수 기록이랑 다릅니다'),
   ('desk','해당 증거가 입증 경로에서 보류 처리된다','자료 적격성 확인 필요'),
   ('stinger','다시 현장 기록으로 돌아간다','흔적도 기록이 없으면 증거가 되기 어렵다'),
 ],
}

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
        return Outcome(code,sufficient,correct,sufficient and correct,continue_case,
                       tuple(missing),tuple(ENDING_SCRIPTS[code]))
    def reaction(self, outcome:Outcome,accused_id):
        from .reaction_selector import ReactionSelector
        return ReactionSelector(self.world).choose(outcome.code, accused_id)

    @staticmethod
    def public_projection(outcome:Outcome,reaction=None):
        # Deliberately omit correct_identity from public payload: would reveal culprit on failure
        return {'ending_code':('substantiated' if outcome.report_accepted else ('ongoing' if outcome.code=='no_accusation' else 'recheck_required')),'report_accepted':outcome.report_accepted,
                'may_continue':outcome.can_continue,'missing_proof_axes':list(outcome.missing_axes),
                'beats':[{'location':a,'staging':b,'subtitle':c} for a,b,c in outcome.montage],
                'reaction':reaction or {'variant_id':'none','beats':[]}}
