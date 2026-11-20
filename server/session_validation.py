"""Release-blocking quality gate for a manually reviewed Unity playthrough.
Never infer visual fidelity from Python tests.
"""
from dataclasses import dataclass
@dataclass(frozen=True)
class ShotReview:
    scene: str
    video_path: str
    reviewer: str
    viewed: bool
    korean_space_authentic: bool
    character_realism: bool
    lighting_pass: bool
    physical_contacts_pass: bool
    audio_pass: bool
    ui_legible: bool
    immersion_pass: bool
    verified_assets_only: bool
    notes: str=''

def evaluate_shot(review:ShotReview):
    fields=('viewed','korean_space_authentic','character_realism','lighting_pass',
            'physical_contacts_pass','audio_pass','ui_legible','immersion_pass','verified_assets_only')
    failed=[f for f in fields if not getattr(review,f)]
    if not review.video_path or not review.reviewer.strip():failed.append('missing_review_evidence')
    return {'ship_approved':not failed,'failed_criteria':failed,
            'note':'Self-reported checklist is not proof; reviewer must actually open frames and video'}
