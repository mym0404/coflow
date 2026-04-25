from . import (
    ask_next,
    bundle_author,
    closure_auditor,
    contract_reviewer,
    score,
    seed_architect,
    seed_feedback,
    seed_reviser,
    verification_reviewer,
)

REQUIRED_REVIEWERS = (contract_reviewer.ROLE, verification_reviewer.ROLE)
