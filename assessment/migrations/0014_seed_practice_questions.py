from django.db import migrations


PRACTICE_QUESTIONS = (
    (
        "Which AWS practice best reduces accidental public access to a training bucket?",
        "Grant only the required scoped access and verify public access is blocked",
        "Attach administrator access to every learner",
        "Disable access logging",
        "Share account root credentials",
        "A", "aws", "beginner",
        "Start private, grant only the needed permission, and test the denied path.",
    ),
    (
        "Which SQL clause filters individual rows before grouping?",
        "HAVING", "WHERE", "ORDER BY", "LIMIT",
        "B", "sql", "beginner",
        "WHERE filters rows before aggregation; HAVING filters grouped results.",
    ),
    (
        "Which JavaScript method creates a new array containing items that pass a test?",
        "map", "filter", "reduce", "sort",
        "B", "javascript", "beginner",
        "filter returns a new array containing elements whose callback result is truthy.",
    ),
    (
        "Why should a machine-learning evaluation split be made before fitting preprocessing steps?",
        "To prevent information from the test data leaking into training",
        "To increase the number of labels",
        "To guarantee the model is accurate",
        "To avoid measuring a baseline",
        "A", "python", "beginner",
        "Fit preprocessing on training data only, then apply it to held-out data.",
    ),
    (
        "What does Kotlin's nullable type, such as String?, communicate?",
        "The value is always empty",
        "The value may be null and should be handled explicitly",
        "The value is immutable",
        "The value is stored in a database",
        "B", "kotlin", "beginner",
        "Nullable types make the possibility of null explicit in the type system.",
    ),
    (
        "During defensive web-security review, what should be confirmed before testing a live system?",
        "That the tester has written authorization and a defined scope",
        "That public exploit code is available",
        "That logs are disabled",
        "That the target has no owner",
        "A", "web_security", "beginner",
        "Testing must stay within written authorization and agreed scope.",
    ),
    (
        "Which Git command shows the current working-tree changes without changing files?",
        "git status", "git reset --hard", "git clean -fd", "git push --force",
        "A", "git", "beginner",
        "git status reports staged and unstaged changes without modifying the work tree.",
    ),
)


def add_practice_questions(apps, schema_editor):
    Question = apps.get_model("assessment", "Question")
    database = schema_editor.connection.alias
    for row in PRACTICE_QUESTIONS:
        text, option_a, option_b, option_c, option_d, answer, skill, difficulty, explanation = row
        if Question.objects.using(database).filter(question_text=text).exists():
            continue
        Question.objects.using(database).create(
            question_text=text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=answer,
            skill=skill,
            difficulty=difficulty,
            explanation=explanation,
            status="published",
            assessment_enabled=False,
            created_by=None,
        )


class Migration(migrations.Migration):
    dependencies = [("assessment", "0013_question_assessment_enabled")]

    operations = [migrations.RunPython(add_practice_questions, migrations.RunPython.noop)]
