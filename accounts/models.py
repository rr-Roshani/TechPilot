from django.db import models
from django.contrib.auth.models import User


def normalize_career_goal(value):
    """Return the canonical profile value used across learning pages."""
    value = (value or "").strip()
    if value.casefold() in {
        "cybersecurity",
        "cybersecurity analyst",
        "penetration testing",
        "penetration testing / cybersecurity analyst",
        "penetration testing/cybersecurity analyst",
    }:
        return "Cybersecurity Analyst"
    return value


# ============================================================
# STUDENT PROFILE
# ============================================================

class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    EDUCATION_CHOICES = [
        ("MCA", "MCA"),
        ("BCA", "BCA"),
        ("BTECH", "B.Tech / B.E."),
        ("DIPLOMA", "Diploma"),
        ("OTHER", "Other"),
    ]

    education = models.CharField(
        max_length=20,
        choices=EDUCATION_CHOICES,
        blank=True
    )

    year = models.CharField(
        max_length=30,
        blank=True
    )

    specialization = models.CharField(
        max_length=150,
        blank=True
    )

    career_goal = models.CharField(
        max_length=100,
        blank=True
    )

    skills = models.JSONField(
        default=list,
        blank=True
    )

    skill_level = models.CharField(
        max_length=30,
        blank=True
    )

    study_time = models.PositiveIntegerField(
        default=60
    )

    preparation = models.CharField(
        max_length=50,
        blank=True
    )

    onboarding_completed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):
        self.career_goal = normalize_career_goal(self.career_goal)
        super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.user.email} - "
            f"{self.career_goal or 'No Goal'}"
        )


# ============================================================
# LEARNING PROGRESS
# ============================================================

class LearningProgress(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="learning_progress"
    )

    total_xp = models.PositiveIntegerField(
        default=0
    )

    missions_completed = models.PositiveIntegerField(
        default=0
    )

    projects_completed = models.PositiveIntegerField(
        default=0
    )

    practice_completed = models.PositiveIntegerField(
        default=0
    )

    interviews_completed = models.PositiveIntegerField(
        default=0
    )

    current_streak = models.PositiveIntegerField(
        default=0
    )

    longest_streak = models.PositiveIntegerField(
        default=0
    )

    career_progress = models.PositiveIntegerField(
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"{self.user.email} - "
            f"{self.total_xp} XP"
        )


class DashboardChecklistProgress(models.Model):
    """Saved state and one-time XP award for a dashboard checklist item."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="dashboard_checklist_progress",
    )
    career_goal = models.CharField(max_length=100, blank=True, default="")
    item_key = models.CharField(max_length=50)
    completed = models.BooleanField(default=False)
    xp_awarded = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "career_goal", "item_key"],
                name="unique_user_career_dashboard_checklist_item",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.career_goal} - {self.item_key}"


# ============================================================
# LEARNING ATTENDANCE
# ============================================================

class LearningAttendance(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="learning_attendance"
    )

    date = models.DateField()

    minutes_spent = models.PositiveIntegerField(
        default=0
    )

    missions_completed = models.PositiveIntegerField(
        default=0
    )

    attended = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"],
                name="unique_user_learning_date"
            )
        ]

        ordering = [
            "-date"
        ]

    def __str__(self):

        return (
            f"{self.user.email} - "
            f"{self.date}"
        )


# ============================================================
# MISSION PROGRESS
# ============================================================

class MissionProgress(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mission_progress"
    )
    career_goal = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
    )
    day_number = models.PositiveIntegerField(
        default=1,
        db_index=True
    )

    mission_date = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )

    title = models.CharField(
        max_length=200
    )

    category = models.CharField(
        max_length=100,
        blank=True
    )

    skill = models.CharField(
        max_length=100,
        blank=True
    )

    difficulty = models.CharField(
        max_length=50,
        blank=True
    )

    duration = models.PositiveIntegerField(
        default=15
    )

    xp = models.PositiveIntegerField(
        default=0
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed = models.BooleanField(
        default=False
    )

    class Meta:

        ordering = [
            "-started_at"
        ]

    def __str__(
        self):

        return (
            f"{self.user.email} - "
            f"{self.title}"
        )
        
# ============================================================
# MISSION QUIZ ATTEMPTS
# ============================================================

class MissionQuizAttempt(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mission_quiz_attempts"
    )

    mission = models.ForeignKey(
        MissionProgress,
        on_delete=models.CASCADE,
        related_name="quiz_attempts"
    )

    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=10)
    answers = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return (
            f"{self.user.email} - {self.mission.title} "
            f"- {self.score}/{self.total_questions}"
        )


class InterviewAnswer(models.Model):
    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
    ]
    QUESTION_TYPE_CHOICES = [
        ("technical", "Technical"),
        ("behavioral", "Behavioural"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interview_answers",
    )
    career_goal = models.CharField(max_length=100)
    question_key = models.CharField(max_length=160)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    answer = models.TextField(blank=True)
    self_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "career_goal", "question_key"],
                name="unique_user_career_interview_answer",
            ),
        ]
        ordering = ["-updated_at"]


class InterviewDayProgress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interview_day_progress",
    )
    career_goal = models.CharField(max_length=100)
    day_number = models.PositiveSmallIntegerField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "career_goal", "day_number"],
                name="unique_user_career_interview_day",
            ),
        ]
        ordering = ["day_number"]
