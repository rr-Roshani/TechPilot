"""Skill status derived from saved profile, mission, and assessment records."""

import re

from assessment.models import AssessmentAnswer
from .models import MissionProgress, normalize_career_goal


def _key(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def career_skill_status(user, profile, career, recommendations):
    """Return independent self-reported, learning, and evidence-backed states."""
    career = normalize_career_goal(career)
    known_skills = list(profile.skills or [])
    missions = MissionProgress.objects.filter(user=user, career_goal=career)
    labels = {_key(skill): skill for skill in recommendations}

    learning = set()
    completed = set()
    for mission in missions:
        key = _key(mission.skill)
        label = labels.get(key)
        if label:
            (completed if mission.completed else learning).add(label)
    learning.difference_update(completed)

    latest_attempt = user.assessment_attempts.filter(is_completed=True).order_by(
        "-completed_at", "-id"
    ).first()
    assessed = set()
    if latest_attempt:
        skill_counts = {}
        for answer in AssessmentAnswer.objects.filter(
            attempt=latest_attempt
        ).select_related("question"):
            key = _key(answer.question.skill)
            if key in labels:
                correct, total = skill_counts.get(key, (0, 0))
                skill_counts[key] = (correct + int(answer.is_correct), total + 1)
        assessed = {
            labels[key]
            for key, (correct, total) in skill_counts.items()
            if total and correct / total >= 0.8
        }

    return {
        "known_skills": known_skills,
        "recommended_skills": list(recommendations),
        "learning_skills": sorted(learning),
        "completed_skills": sorted(completed),
        "assessment_skills": sorted(assessed),
        "skills_to_build": [
            skill for skill in recommendations
            if skill not in completed and skill not in assessed
        ],
    }
