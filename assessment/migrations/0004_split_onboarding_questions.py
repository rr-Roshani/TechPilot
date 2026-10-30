from django.db import migrations, models


def move_onboarding_questions(apps, schema_editor):
    Question = apps.get_model("assessment", "Question")
    OnboardingQuestion = apps.get_model("assessment", "OnboardingQuestion")
    fields = (
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "skill",
        "difficulty",
        "explanation",
        "created_at",
    )
    onboarding_questions = Question.objects.filter(is_admin_created=False)
    OnboardingQuestion.objects.bulk_create(
        OnboardingQuestion(**{field: getattr(question, field) for field in fields})
        for question in onboarding_questions
    )
    onboarding_questions.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("assessment", "0003_question_is_admin_created"),
    ]

    operations = [
        migrations.CreateModel(
            name="OnboardingQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_text", models.TextField()),
                ("option_a", models.CharField(max_length=255)),
                ("option_b", models.CharField(max_length=255)),
                ("option_c", models.CharField(max_length=255)),
                ("option_d", models.CharField(max_length=255)),
                ("correct_answer", models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])),
                ("skill", models.CharField(max_length=50, choices=[("python", "Python"), ("sql", "SQL"), ("java", "Java"), ("javascript", "JavaScript"), ("html_css", "HTML & CSS"), ("react", "React"), ("django", "Django"), ("nodejs", "Node.js"), ("git", "Git"), ("linux", "Linux"), ("aws", "AWS"), ("docker", "Docker"), ("networking", "Networking"), ("dsa", "DSA")])),
                ("difficulty", models.CharField(max_length=20, choices=[("beginner", "Beginner"), ("basic", "Basic"), ("intermediate", "Intermediate"), ("advanced", "Advanced")])),
                ("explanation", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RunPython(move_onboarding_questions, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="question",
            name="is_admin_created",
        ),
    ]
