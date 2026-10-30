from django.db import migrations


CAREER_CONTENT = {
    "Cloud Engineer": (
        ("Network map", "Networking", "Linux and cloud network basics", "Draw a subnet, route, and security-group flow for a small web service. Use a private test design and explain which ports should be reachable.", "A labeled diagram showing request flow, trust boundaries, and least-privilege rules.", "Separate routing decisions from traffic filtering; expose only the application entry point."),
        ("Storage permissions challenge", "AWS, IAM", "Cloud storage and access control", "For a fictional static site, write a checklist for private-by-default storage, narrowly scoped read access, versioning, and HTTPS delivery.", "A configuration checklist with one negative access test.", "Avoid account-wide public permissions and include a rollback step."),
    ),
    "Full Stack Developer": (
        ("Accessible web form", "HTML, CSS", "Semantic HTML and responsive CSS", "Build a small contact form with labels, required-field feedback, keyboard navigation, and a narrow-screen layout.", "A form that can be completed by keyboard and remains readable on mobile.", "Use associated labels and preserve a visible focus style."),
        ("Request-response challenge", "JavaScript, REST APIs", "Browser requests and API validation", "Trace a form submission from browser to a REST endpoint. Write a sample request, validation response, and success response.", "A short API contract with field errors and a success example.", "Treat client-side checks as a usability aid; validate again on the server."),
    ),
    "Data Analyst": (
        ("SQL quality checks", "SQL", "Filtering, aggregation, and data validation", "Given a small sales table, identify null dates, duplicate transaction IDs, and negative quantities with SQL queries.", "Queries plus a brief note describing the assumptions behind each check.", "Keep raw rows available and report counts before and after any exclusion."),
        ("Insight communication challenge", "SQL, Data Visualization", "Evidence-based analysis", "Choose one business question, define its metric and grain, and describe a chart that answers it without implying causation.", "A metric definition, chart sketch, and two-sentence evidence-based finding.", "State the comparison period and any data limitations."),
    ),
    "AI/ML Engineer": (
        ("Baseline model evaluation", "Python, Statistics", "Train/test separation and evaluation", "Plan a baseline classifier using a held-out test set. Identify one leakage risk and choose metrics for an imbalanced target.", "A reproducible evaluation plan with a baseline and metric rationale.", "Do not tune on the final test set; compare with a simple baseline."),
        ("Model error review challenge", "Python, Model Evaluation", "Error analysis and responsible reporting", "Review a fictional confusion matrix and propose two useful error slices plus a limitation to report.", "A short error-analysis note with a next experiment.", "Check slice size and uncertainty before drawing conclusions."),
    ),
    "Android Developer": (
        ("Kotlin state and layouts", "Kotlin, UI Layouts", "Input handling and accessible mobile UI", "Design a small profile screen that handles long names, missing values, and a narrow display without clipping.", "A screen mockup or implementation plus a short edge-case checklist.", "Use responsive constraints and meaningful labels rather than fixed-width text."),
        ("Offline notes challenge", "Room Database, Navigation", "Local persistence and navigation", "Outline how a notes screen saves edits locally and restores them after navigation or process recreation.", "A small data-flow diagram showing UI state, repository, and local storage.", "Keep durable data separate from temporary screen state."),
    ),
    "Cybersecurity Analyst": (
        ("Synthetic log triage", "Networking, Defensive Monitoring", "Log fields and defensive triage", "Review a short synthetic event timeline, identify what is known and unknown, and draft a scoped escalation note.", "A timeline, confidence notes, and a defensive follow-up suggestion.", "Use only supplied fictional data; do not probe real systems."),
        ("Web security review challenge", "Web Security, Vulnerability Assessment", "Safe defensive review", "Inspect a fictional login-flow description and list defensive checks for authorization, input validation, and session handling.", "A prioritized checklist with a safe verification plan.", "Only test systems for which you have written authorization."),
    ),
    "Not Sure Yet": (
        ("Technology interests inventory", "Career Exploration, Communication", "Career exploration and reflection", "Compare two technology roles using responsibilities, entry requirements, and the tasks you enjoy. Record questions that need confirmation.", "A one-page comparison with sources and a small next experiment.", "Use multiple current role descriptions and distinguish evidence from assumptions."),
        ("Try a small technical task", "Python, SQL, Git", "Structured career exploration", "Choose one small Python, SQL, or Git task, time-box the attempt, and record what felt engaging or difficult.", "A saved result and a short reflection that guides your next learning choice.", "The purpose is to gather evidence, not to claim mastery."),
    ),
}


def add_missing_starter_practice(apps, schema_editor):
    PracticeLab = apps.get_model("assessment", "PracticeLab")
    database = schema_editor.connection.alias
    for career, specs in CAREER_CONTENT.items():
        legacy_careers = (career, "Cybersecurity") if career == "Cybersecurity Analyst" else (career,)
        for index, spec in enumerate(specs):
            content_type = "lab" if index == 0 else "challenge"
            title, skill, objective, task, expected, hint = spec
            exists = PracticeLab.objects.using(database).filter(
                roadmap__in=legacy_careers,
                content_type=content_type,
                status="published",
            ).exists()
            if exists:
                continue
            full_title = f"TechPilot Starter: {title}"
            if PracticeLab.objects.using(database).filter(title=full_title).exists():
                continue
            PracticeLab.objects.using(database).create(
                title=full_title,
                roadmap=career,
                skill=skill,
                difficulty="beginner",
                description=objective,
                task=task,
                expected_answer=expected,
                explanation=hint,
                xp=0,
                content_type=content_type,
                status="published",
                created_by=None,
            )


class Migration(migrations.Migration):
    dependencies = [("assessment", "0011_alter_onboardingquestion_skill_alter_question_skill")]

    operations = [migrations.RunPython(add_missing_starter_practice, migrations.RunPython.noop)]
