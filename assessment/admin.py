from django.contrib import admin
from .models import OnboardingQuestion, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        "question_text",
        "skill",
        "difficulty",
        "correct_answer",
        "created_at",
    )

    list_filter = (
        "skill",
        "difficulty",
    )

    search_fields = (
        "question_text",
        "skill",
    )

    ordering = ("skill", "difficulty")


@admin.register(OnboardingQuestion)
class OnboardingQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "skill", "difficulty", "correct_answer", "created_at")
    list_filter = ("skill", "difficulty")
    search_fields = ("question_text", "skill")
    readonly_fields = (
        "question_text", "option_a", "option_b", "option_c",
        "option_d", "correct_answer", "skill", "difficulty",
        "explanation", "created_at",
    )