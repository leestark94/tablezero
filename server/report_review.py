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
    out_ev, out_cl = {}, {}
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
    if issues:
        first = list(dict.fromkeys(issues))
        raise GuardError(' · '.join(KO.get(i, i) for i in first))
    return {'axes': out_ev, 'claims': out_cl}
