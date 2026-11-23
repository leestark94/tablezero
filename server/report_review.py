"""Structure/ownership/provenance checks for the final report (CASE001).
Adapted from the reviewed reference contract (Codex handoff). It never judges whether an accusation is TRUE and never scores
prose: the claim text must exist and belong to this session, the evidence attached to each axis must have been acquired in THIS
session, must not be duplicated, and source families come from the server's own catalog (the client's grouping is not trusted).
Proof sufficiency itself stays in World.evaluate_report (axis-by-axis, no union across axes)."""
from __future__ import annotations
from .runtime import GuardError

AXES = ('presence_or_timing', 'motive', 'physical_link', 'exclude_alternative')
SCHEMA_VERSION = 1
KO = {
    'unsupported_schema': '보고서 형식이 맞지 않습니다', 'stale_session': '이전 수사의 보고서입니다. 새 수사에서 다시 작성해야 합니다',
    'confirmation_required': '정식 제출 확인이 필요합니다', 'axis_map_required': '네 축별 주장과 근거가 필요합니다',
    'axis_required': '비어 있는 축이 있습니다', 'claim_required': '주장 문장이 비어 있는 축이 있습니다',
    'claim_too_long': '주장이 너무 깁니다', 'evidence_required': '근거가 붙지 않은 축이 있습니다',
    'invalid_evidence_ids': '근거 목록이 올바르지 않습니다', 'duplicate_evidence': '같은 근거가 한 축에 중복돼 있습니다',
    'evidence_not_acquired': '확보하지 않은 자료가 첨부돼 있습니다', 'unknown_axis': '알 수 없는 축입니다',
}


def validate(payload, *, session_id: str, acquired: set, require_all_axes: bool = True) -> dict:
    """Returns {'axes': {axis: [evidence ids]}, 'claims': {axis: text}}. Raises GuardError with a player-readable reason."""
    issues = []
    if not isinstance(payload, dict):
        raise GuardError('보고서 형식이 맞지 않습니다')
    if payload.get('schema_version') != SCHEMA_VERSION:
        issues.append('unsupported_schema')
    if payload.get('session_id') != session_id:
        issues.append('stale_session')
    axes = payload.get('axes')
    if not isinstance(axes, dict):
        issues.append('axis_map_required')
        raise GuardError(KO[issues[0]])
    for unk in axes.keys() - set(AXES):
        issues.append('unknown_axis')
    out_ev, out_cl, out_lim, out_against = {}, {}, {}, {}
    for axis in AXES:
        item = axes.get(axis)
        if not isinstance(item, dict):
            if require_all_axes:
                issues.append('axis_required')
            continue
        claim = item.get('claim')
        if not isinstance(claim, str) or not claim.strip():
            issues.append('claim_required')
        elif len(claim) > 4000:
            issues.append('claim_too_long')
        refs = item.get('evidence_ids')
        if not isinstance(refs, list) or not refs:
            issues.append('evidence_required'); continue
        if len(refs) > 64 or any(not isinstance(r, str) for r in refs):
            issues.append('invalid_evidence_ids'); continue
        if len(set(refs)) != len(refs):
            issues.append('duplicate_evidence')
        if any(r not in acquired for r in set(refs)):
            issues.append('evidence_not_acquired')
        out_ev[axis] = sorted(set(refs)); out_cl[axis] = (claim or '').strip()
        lim = item.get('limit_note'); ag = item.get('against_ids') or []
        if isinstance(lim, str): out_lim[axis] = lim.strip()[:1500]
        if isinstance(ag, list): out_against[axis] = [a for a in ag if isinstance(a, str) and a in acquired][:16]
    if issues:
        first = list(dict.fromkeys(issues))
        raise GuardError(' · '.join(KO.get(i, i) for i in first))
    return {'axes': out_ev, 'claims': out_cl, 'limits': out_lim, 'against': out_against}


AXIS_KO = {'presence_or_timing': '접근 및 시간', 'motive': '갈등과 동기', 'physical_link': '치명상과 행위의 연결', 'exclude_alternative': '다른 두 사람의 대안 검토'}


def axis_feedback(world, axis_evidence: dict, missing: list) -> list:
    """Why an axis did not hold — described from what was attached, never by naming the missing record or the culprit."""
    fam = {e['id']: e.get('source_family', '') for e in world._canon['evidence']}
    out = []
    for axis in missing:
        ids = axis_evidence.get(axis, [])
        fams = {fam.get(i) for i in ids if fam.get(i)}
        if not ids:
            why = '붙인 근거가 없다'
        elif axis == 'physical_link' and len(fams) < 2:
            why = '서로 다른 출처의 근거가 두 가지 이상 필요한데, 붙인 근거는 한 출처에 치우쳐 있다'
        else:
            why = '붙인 근거가 이 주장을 뒷받침하기에 부족하거나, 이 축과 직접 이어지지 않는다. 다른 축에 붙인 근거는 이 축에서 대신 쓰이지 않는다'
        out.append({'axis': axis, 'axis_ko': AXIS_KO.get(axis, axis), 'why': why, 'attached': len(ids), 'source_groups': len(fams)})
    return out
