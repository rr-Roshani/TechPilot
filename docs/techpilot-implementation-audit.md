# TechPilot implementation audit

Audit date: 2026-10-29. Database: `/Users/mac/Desktop/techpilot copy/db.sqlite3`.

## Existing relationships and affected areas

- `StudentProfile.user` is a one-to-one link to Django `User`; `career_goal` is the saved career and `skills` is a JSON list.
- `MissionProgress.user` links mission history to a student and stores `career_goal`, `skill`, completion, date, and XP. Checklist progress is separately keyed by user and career.
- `AssessmentAttempt.user` links each attempt to a student. `AssessmentAnswer.attempt` and `.question` preserve answer history and the question used.
- `Question` is the assessment/practice question bank. `PracticeLab` stores staff-authored labs. Neither content model currently has an owner or publication state.
- Admin/teacher pages are implemented in `accounts/admin_views.py`, routed in `techpilot/urls.py`, and use `templates/admin/`. The lab edit route references `admin/practice_lab_edit.html`, which is absent; current lab deletion physically removes records.
- Student practice is rendered by `practice_view` in `techpilot/views.py` and `templates/learning/resource_page.html`; it reads question/lab records without a publication filter.
- Assessment submission and restart logic is in `techpilot/views.py`, with regression coverage in `accounts/tests.py`.

## `question_ids` error diagnosis

The configured database path is `BASE_DIR / "db.sqlite3"`. The active database passes `PRAGMA integrity_check`; `assessment_assessmentattempt` contains `question_ids`; migration `assessment.0007_assessmentattempt_is_completed_and_more` and subsequent migrations are recorded as applied. The model field is declared in `assessment/models.py`, and the admin query loads `AssessmentAttempt` rows in `accounts/admin_views.py`. Therefore the reported no-column error is not reproducible against this checkout's active database. The likely cause is a different/stale SQLite database or a process using a database from before migration 0007. Do not add a duplicate column migration to this already-correct database. For the database that actually raises the error, confirm its configured path, back it up, then apply the existing pending migrations with `python manage.py migrate`.

## Data risks and implementation order

1. Preserve the active database and verify its backup before edits. No change to `AssessmentAttempt.question_ids` is indicated for this database.
2. Add ownership and publication state to existing teacher-managed `Question` and `PracticeLab` records. Keep fields nullable/defaulted so existing rows remain intact and visible as published; new teacher-created content starts as draft.
3. Enforce ownership and status transitions in server views, retain archived records, and filter student queries to published content. Add separate assessment eligibility so practice-only questions never leak into baseline/retest selection.
4. Add persisted per-user lab and question attempts, a career-filtered practice workflow, starter labs/challenges for missing career content, and missing teacher edit/archive templates.
5. Review and apply additive assessment migrations, then run system checks, migration checks, assessment/accounts tests, and an active-database admin smoke request.

The applied migrations `assessment.0010`–`assessment.0014` add nullable owners/status metadata, practice content type and attempt tables, skill choices, assessment eligibility, and starter practice content. Existing records remain published and are not deleted or reassigned. Migration `0012` fills only missing career/type combinations, and `0014` creates practice-only questions. No migration alters or removes student, assessment attempt, answer, mission, or progress history.

The initial backup and verified integrity result are under `backups/2026-10-29-master-recovery/`. A second pre-`0013` database backup was also taken before applying the final assessment eligibility and practice-question migrations.
