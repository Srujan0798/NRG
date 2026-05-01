"""Feedback/RLHF signal endpoint."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.api.logging_config import get_logger

router = APIRouter(prefix="/api", tags=["feedback"])
logger = get_logger(__name__)


class FeedbackRequest(BaseModel):
    query_id: str
    score: int
    feedback_text: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(
    request: Request,
    feedback: FeedbackRequest,
):
    """
    Submit user feedback on a query response.

    Updates the training pair with the researcher's 1-5 rating so the signal can
    feed future model fine-tuning.
    """
    if feedback.score < 1 or feedback.score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")

    try:
        from src.training.data_collector import get_training_collector

        collector = get_training_collector()
        success = collector.update_feedback(
            query_id=feedback.query_id,
            score=feedback.score,
            feedback_text=feedback.feedback_text,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Training pair not found")
        return {"status": "ok", "query_id": feedback.query_id, "score": feedback.score}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Feedback update failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to record feedback") from exc
