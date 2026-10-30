from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


# =========================================================
# QUESTION BANK
# =========================================================

class Question(models.Model):

    CONTENT_STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    SKILL_CHOICES = [
        ("python", "Python"),
        ("sql", "SQL"),
        ("java", "Java"),
        ("javascript", "JavaScript"),
        ("html_css", "HTML & CSS"),
        ("react", "React"),
        ("django", "Django"),
        ("nodejs", "Node.js"),
        ("git", "Git"),
        ("linux", "Linux"),
        ("aws", "AWS"),
        ("docker", "Docker"),
        ("networking", "Networking"),
        ("dsa", "DSA"),
        ("kotlin", "Kotlin"),
        ("android", "Android"),
        ("azure", "Azure"),
        ("iam", "IAM"),
        ("web_security", "Web Security"),
        ("security_fundamentals", "Security Fundamentals"),
        ("statistics", "Statistics"),
        ("powerbi", "Power BI"),
    ]

    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("basic", "Basic"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    question_text = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
        ],
    )

    skill = models.CharField(
        max_length=50,
        choices=SKILL_CHOICES,
    )

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
    )

    explanation = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_assessment_questions",
    )
    status = models.CharField(
        max_length=20,
        choices=CONTENT_STATUS_CHOICES,
        default="published",
        db_index=True,
    )
    assessment_enabled = models.BooleanField(
        default=True,
        help_text="Include this question in baseline and retest assessments.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.skill} - {self.question_text[:50]}"

    def get_options(self):
        return (
            ("A", self.option_a),
            ("B", self.option_b),
            ("C", self.option_c),
            ("D", self.option_d),
        )


# =========================================================
# ONBOARDING QUESTIONS
# =========================================================

class OnboardingQuestion(models.Model):

    SKILL_CHOICES = Question.SKILL_CHOICES
    DIFFICULTY_CHOICES = Question.DIFFICULTY_CHOICES

    question_text = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_answer = models.CharField(
        max_length=1,
        choices=Question._meta.get_field("correct_answer").choices,
    )

    skill = models.CharField(
        max_length=50,
        choices=SKILL_CHOICES,
    )

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
    )

    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.skill} - {self.question_text[:50]}"


# =========================================================
# ASSESSMENT ATTEMPTS
# Baseline Assessment and Retests
# =========================================================

class AssessmentAttempt(models.Model):

    ATTEMPT_TYPE_CHOICES = [
        ("baseline", "Baseline Assessment"),
        ("retest", "Retest"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
    )

    attempt_type = models.CharField(
        max_length=20,
        choices=ATTEMPT_TYPE_CHOICES,
        null=True,
        blank=True,
        db_index=True,
    )

    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    question_ids = models.JSONField(default=list, blank=True)
    is_completed = models.BooleanField(default=False, db_index=True)
    is_draft = models.BooleanField(default=False, db_index=True)
    is_explicit_restart = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.score}%"


# =========================================================
# ASSESSMENT ANSWERS
# =========================================================

class AssessmentAnswer(models.Model):

    attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )

    selected_answer = models.CharField(
        max_length=1,
        blank=True,
    )

    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.attempt.user.username} - "
            f"Question {self.question.id}"
        )


# =========================================================
# PRACTICE LAB
# =========================================================

class PracticeLab(models.Model):

    CONTENT_STATUS_CHOICES = Question.CONTENT_STATUS_CHOICES
    CONTENT_TYPE_CHOICES = [
        ("lab", "Skill Lab"),
        ("challenge", "Practice Challenge"),
    ]

    ROADMAP_CHOICES = [
        ("Cloud Engineer", "Cloud Engineer"),
        ("Full Stack Developer", "Full Stack Developer"),
        ("Data Analyst", "Data Analyst"),
        ("AI/ML Engineer", "AI/ML Engineer"),
        ("Android Developer", "Android Developer"),
        ("Cybersecurity Analyst", "Cybersecurity Analyst"),
        ("Not Sure Yet", "Not Sure Yet"),
        ("Cybersecurity", "Cybersecurity"),
        ("DevOps Engineer", "DevOps Engineer"),
    ]

    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("basic", "Basic"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    title = models.CharField(max_length=200)

    roadmap = models.CharField(
        max_length=100,
        choices=ROADMAP_CHOICES,
    )

    skill = models.CharField(max_length=100)

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
    )

    description = models.TextField()
    task = models.TextField()

    expected_answer = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    xp = models.PositiveIntegerField(default=10)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="lab",
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_practice_labs",
    )
    status = models.CharField(
        max_length=20,
        choices=CONTENT_STATUS_CHOICES,
        default="published",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.skill}"


class PracticeLabAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="practice_lab_attempts",
    )
    lab = models.ForeignKey(
        PracticeLab,
        on_delete=models.CASCADE,
        related_name="practice_attempts",
    )
    response = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-submitted_at", "-id")


class PracticeQuestionAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="practice_question_attempts",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="practice_attempts",
    )
    career_goal = models.CharField(max_length=100, blank=True, db_index=True)
    selected_answer = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-answered_at", "-id")
