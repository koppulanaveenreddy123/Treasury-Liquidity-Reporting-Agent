from __future__ import annotations

import pytest

from app.exceptions import HumanApprovalRequired
from app.services.review_service import ReviewService


def test_review_service_requires_human_approval() -> None:
    with pytest.raises(HumanApprovalRequired):
        ReviewService().validate_human_approval(False)


def test_review_service_accepts_approval() -> None:
    ReviewService().validate_human_approval(True)
