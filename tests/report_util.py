def rp(ctrl, accused, evidence):
    """Compat helper: put the same evidence list on every axis (the OLD union behaviour) in a v1 report."""
    ids = list(evidence)
    axes = {a: {'claim': '주장', 'evidence_ids': ids} for a in ('presence_or_timing', 'motive', 'physical_link', 'exclude_alternative')}
    return {'schema_version': 1, 'session_id': ctrl.session_id, 'accused_id': accused, 'axes': axes, 'confirm': True}
