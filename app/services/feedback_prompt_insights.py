"""
rating=0 피드백을 모아 프롬프트 보조 문구를 만들고, 관리자용으로 문제 가이드를 집계한다.
"""

from tortoise.expressions import Q
from tortoise.functions import Count

# 제품 DTO 기준: 0 = 아쉬워요
LOW_RATING = 0


async def build_feedback_addon_for_llm(guide_id: str, prompt_version: str) -> str:
    """같은 가이드의 불만 코멘트 → 없으면 같은 prompt_version 다른 가이드 코멘트를 짧게 붙인다."""
    texts = await _recent_low_rating_comments_for_guide(guide_id, limit=8)
    if not texts:
        texts = await _recent_low_rating_comments_other_guides(prompt_version, exclude_guide_id=guide_id, limit=5)
    if not texts:
        return ""
    body = "\n".join(f"- {t}" for t in texts)
    return (
        "\n\n## 참고: 최근 이용자 불만 피드백 (품질 개선용)\n"
        "아래는 rating=0 피드백에서 가져온 코멘트입니다. "
        "빠진 설명·톤·난이도를 보완하는 데만 활용하고, 개인을 특정하지 마세요.\n"
        f"{body}"
    )


async def list_guides_with_many_low_ratings(*, min_count: int, limit: int) -> list[dict]:
    """rating=0 피드백이 많은 가이드와 그때의 prompt_version (관리자 대시보드용)."""
    from app.models.guides import Guide

    rows = (
        await Guide.annotate(
            low_rating_count=Count("feedbacks", _filter=Q(feedbacks__rating=LOW_RATING)),
        )
        .filter(low_rating_count__gte=min_count)
        .order_by("-low_rating_count")
        .limit(limit)
        .values("id", "prompt_version", "status", "low_rating_count")
    )
    return [
        {
            "guide_id": str(r["id"]),
            "prompt_version": r["prompt_version"],
            "guide_status": r["status"],
            "low_rating_count": r["low_rating_count"],
        }
        for r in rows
    ]


async def _recent_low_rating_comments_for_guide(guide_id: str, limit: int) -> list[str]:
    from app.models.feedbacks import Feedback

    rows = await Feedback.filter(guide_id=guide_id, rating=LOW_RATING).order_by("-created_at").limit(limit)
    out: list[str] = []
    for r in rows:
        if r.comment and (t := r.comment.strip()):
            out.append(t[:500])
    return out


async def _recent_low_rating_comments_other_guides(
    prompt_version: str, *, exclude_guide_id: str, limit: int
) -> list[str]:
    from app.models.feedbacks import Feedback

    rows = (
        await Feedback.filter(rating=LOW_RATING, guide__prompt_version=prompt_version)
        .exclude(guide_id=exclude_guide_id)
        .order_by("-created_at")
        .limit(limit)
    )
    out: list[str] = []
    for r in rows:
        if r.comment and (t := r.comment.strip()):
            out.append(t[:500])
    return out
