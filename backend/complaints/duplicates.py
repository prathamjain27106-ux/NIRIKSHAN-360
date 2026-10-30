"""Non-destructive duplicate candidate detection for complaints."""

import re
from difflib import SequenceMatcher

from django.utils import timezone


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _similarity(left: str, right: str) -> float:
    """Return a percentage based on both character and meaningful-token overlap."""
    left_tokens = set(_TOKEN_RE.findall(left.lower()))
    right_tokens = set(_TOKEN_RE.findall(right.lower()))
    token_union = left_tokens | right_tokens
    token_score = (
        len(left_tokens & right_tokens) / len(token_union)
        if token_union
        else 0.0
    )
    character_score = SequenceMatcher(None, left.lower(), right.lower()).ratio()
    return (character_score * 0.65 + token_score * 0.35) * 100


def find_possible_duplicates(target_complaint, max_days_window=30) -> list:
    """Find explainable candidates without automatically merging any complaint."""
    complaint_model = target_complaint.__class__
    candidates = complaint_model.objects.filter(
        institution=target_complaint.institution,
        category=target_complaint.category,
    ).exclude(pk=target_complaint.pk)

    target_time = getattr(target_complaint, "created_at", None) or timezone.now()
    target_text = f"{target_complaint.title} {target_complaint.description}".strip()
    matches = []

    for candidate in candidates:
        candidate_time = getattr(candidate, "created_at", None) or timezone.now()
        days_diff = abs((target_time - candidate_time).total_seconds()) / 86400
        if days_diff > max_days_window:
            continue

        candidate_text = f"{candidate.title} {candidate.description}".strip()
        text_score = _similarity(target_text, candidate_text)
        score = min(100, round(text_score + 20))
        if score < 45:
            continue

        explanation = (
            f"Matching institution and category with {score}% text similarity "
            f"within a {round(days_diff, 1)}-day window; officer confirmation "
            "is required before linking and cases are never auto-merged."
        )
        matches.append({
            "candidate": candidate,
            "candidate_id": candidate.pk,
            "similarity_score": score,
            "explanation": explanation,
            "similarity_explanation": explanation,
        })

    return matches


def locate_possible_duplicates(target_complaint, max_days_window=30) -> list:
    """Backward-compatible alias for the duplicate candidate detector."""
    return find_possible_duplicates(target_complaint, max_days_window)
