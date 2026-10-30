from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assessment", "0002_assessmentattempt_assessmentanswer"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="is_admin_created",
            field=models.BooleanField(
                default=False,
                help_text="Only admin-created questions are assigned to student assessments.",
            ),
        ),
    ]
