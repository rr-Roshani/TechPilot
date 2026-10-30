import csv
import io
import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import normalize_career_goal

from assessment.models import (
    AssessmentAnswer,
    AssessmentAttempt,
    OnboardingQuestion,
    Question,
    PracticeLab,##ye add kia
    PracticeQuestionAttempt,
)

from .models import LearningProgress, StudentProfile
from techpilot.career_content import CAREER_CHOICES, CAREER_SKILLS


PRACTICE_SKILL_EXTRAS = {
    "Cloud Engineer": ["Terraform", "IAM", "CI/CD", "Monitoring", "Azure", "Bash"],
    "Full Stack Developer": ["HTML", "CSS", "REST APIs", "TypeScript", "PostgreSQL"],
    "Data Analyst": ["Excel", "Power BI", "Tableau", "Data Visualization", "Jupyter"],
    "AI/ML Engineer": ["scikit-learn", "PyTorch", "TensorFlow", "Model Evaluation"],
    "Android Developer": ["Android SDK", "Android Studio", "Kotlin", "Room Database", "Jetpack Compose"],
    "Cybersecurity Analyst": ["Nmap", "Wireshark", "Burp Suite", "SIEM", "Web Security", "Vulnerability Assessment"],
    "Not Sure Yet": ["Python", "SQL", "Git", "Linux", "Networking"],
}


def _practice_roadmap_choices():
    return [
        (
            career,
            "Penetration Testing / Cybersecurity Analyst"
            if career == "Cybersecurity Analyst" else career,
        )
        for career in CAREER_CHOICES
    ]


def _practice_skill_catalog():
    return {
        career: list(dict.fromkeys(
            CAREER_SKILLS.get(career, []) + PRACTICE_SKILL_EXTRAS.get(career, [])
        ))
        for career in CAREER_CHOICES
    }


def _can_manage_content(user, content):
    return user.is_superuser or content.created_by_id == user.id


def _visible_questions_for_admin(user):
    queryset = Question.objects.select_related("created_by")
    if user.is_superuser:
        return queryset
    return queryset.filter(Q(status="published") | Q(created_by=user))


def _visible_labs_for_admin(user):
    queryset = PracticeLab.objects.select_related("created_by")
    if user.is_superuser:
        return queryset
    return queryset.filter(Q(status="published") | Q(created_by=user))


@staff_member_required(login_url="/admin/login/")
def admin_main_view(request):
    if request.method == "POST":
        question_data = {
            "question_text": request.POST.get("question_text", "").strip(),
            "option_a": request.POST.get("option_a", "").strip(),
            "option_b": request.POST.get("option_b", "").strip(),
            "option_c": request.POST.get("option_c", "").strip(),
            "option_d": request.POST.get("option_d", "").strip(),
            "correct_answer": request.POST.get("correct_answer", "").strip(),
            "skill": request.POST.get("skill", "").strip(),
            "difficulty": request.POST.get("difficulty", "").strip(),
            "explanation": request.POST.get("explanation", "").strip(),
        }

        required_fields = (
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "skill",
            "difficulty",
        )

        if any(not question_data[field] for field in required_fields):
            messages.error(request, "Complete all required question fields.")
        elif (
            question_data["correct_answer"] not in {"A", "B", "C", "D"}
            or question_data["skill"] not in dict(Question.SKILL_CHOICES)
            or question_data["difficulty"] not in dict(Question.DIFFICULTY_CHOICES)
        ):
            messages.error(request, "Choose valid question answers, skills, and difficulty.")
        else:
            Question.objects.create(
                **question_data,
                created_by=request.user,
                status="draft",
            )
            messages.success(request, "Question added successfully.")

        return redirect("admin_main")

    search_query = request.GET.get("q", "").strip()
    users = (
        User.objects.filter(is_superuser=False, is_staff=False)
        .select_related("student_profile", "learning_progress")
        .prefetch_related(
            Prefetch(
                "assessment_attempts",
                queryset=AssessmentAttempt.objects.filter(
                    is_completed=True
                ).order_by("-completed_at", "-id"),
                to_attr="recent_assessment_attempts",
            )
        )
        .order_by("-date_joined")
    )

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    user_rows = []
    for user in users:
        try:
            profile = user.student_profile
        except StudentProfile.DoesNotExist:
            profile = None
        try:
            progress = user.learning_progress
        except LearningProgress.DoesNotExist:
            progress = None
        attempts = getattr(user, "recent_assessment_attempts", [])
        latest_attempt = attempts[0] if attempts else None
        user_rows.append(
            {
                "user": user,
                "profile": profile,
                "progress": progress,
                "latest_attempt": latest_attempt,
                "assessment_count": len(attempts),
            }
        )

    context = {
        "user_rows": user_rows,
        "user_count": User.objects.filter(
            is_superuser=False,
            is_staff=False,
        ).count(),
        "onboarded_count": StudentProfile.objects.filter(
            onboarding_completed=True
        ).count(),
        "question_count": Question.objects.count(),
        "assessment_count": AssessmentAttempt.objects.filter(
            is_completed=True
        ).count(),
        "question_skills": Question.SKILL_CHOICES,
        "question_difficulties": Question.DIFFICULTY_CHOICES,
        "search_query": search_query,
        "onboarding_questions": OnboardingQuestion.objects.order_by("id"),
        "assessment_activity": AssessmentAttempt.objects.filter(
            user__is_staff=False,
            user__is_superuser=False,
            is_completed=True,
        ).select_related("user").order_by("-completed_at")[:12],
        "admin_profile": request.user,
    }
    return render(request, "admin/main.html", context)


@staff_member_required(login_url="/admin/login/")
def admin_users_view(request):
    search_query = request.GET.get("q", "").strip()
    users = User.objects.filter(
        is_superuser=False,
        is_staff=False,
    ).order_by("-date_joined")
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )
    rows = []
    for user in users:
        try:
            profile = user.student_profile
        except StudentProfile.DoesNotExist:
            profile = None
        try:
            progress = user.learning_progress
        except LearningProgress.DoesNotExist:
            progress = None
        attempts = list(user.assessment_attempts.order_by("-completed_at"))
        rows.append({
            "user": user,
            "profile": profile,
            "progress": progress,
            "latest_attempt": attempts[0] if attempts else None,
            "assessment_count": len(attempts),
        })
    return render(
        request,
        "admin/users.html",
        {"user_rows": rows, "search_query": search_query},
    )

def _parse_question_csv(upload):
    if upload is None:
        raise ValueError("Choose a CSV file to upload.")
    if not upload.name.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported.")
    if upload.size > 5 * 1024 * 1024:
        raise ValueError("The CSV file must be 5 MB or smaller.")

    required = {
        "question_text", "option_a", "option_b", "option_c", "option_d",
        "correct_answer", "skill", "difficulty",
    }
    try:
        reader = csv.DictReader(
            io.StringIO(upload.read().decode("utf-8-sig"))
        )
    except (UnicodeDecodeError, csv.Error):
        raise ValueError("The CSV file could not be read as UTF-8 CSV.")
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))

    skills = dict(Question.SKILL_CHOICES)
    difficulties = dict(Question.DIFFICULTY_CHOICES)
    skill_values = {key.lower(): key for key in skills}
    skill_values.update({label.lower(): key for key, label in skills.items()})
    difficulty_values = {key.lower(): key for key in difficulties}
    difficulty_values.update({
        label.lower(): key for key, label in difficulties.items()
    })
    difficulty_values.update({
        "easy": "beginner",
        "medium": "intermediate",
        "hard": "advanced",
    })

    preview = []
    for row_number, row in enumerate(reader, start=2):
        data = {
            field: (row.get(field) or "").strip()
            for field in required
        }
        data["explanation"] = (row.get("explanation") or "").strip()
        if any(not data[field] for field in required):
            raise ValueError(f"Row {row_number}: all required fields are needed.")
        data["correct_answer"] = data["correct_answer"].upper()
        data["skill"] = skill_values.get(data["skill"].lower(), "")
        data["difficulty"] = difficulty_values.get(
            data["difficulty"].lower(), ""
        )
        if data["correct_answer"] not in {"A", "B", "C", "D"}:
            raise ValueError(f"Row {row_number}: correct_answer must be A, B, C, or D.")
        if not data["skill"] or not data["difficulty"]:
            raise ValueError(f"Row {row_number}: invalid skill or difficulty.")
        preview.append(data)
    if not preview:
        raise ValueError("The CSV file does not contain any questions.")
    return preview


@staff_member_required(login_url="/admin/login/")
def admin_questions_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "preview_csv":
            try:
                preview = _parse_question_csv(
                    request.FILES.get("question_file")
                )
            except ValueError as error:
                return render(
                    request,
                    "admin/questions.html",
                    {
                        "questions": _visible_questions_for_admin(request.user).order_by("-created_at"),
                        "question_skills": Question.SKILL_CHOICES,
                        "question_difficulties": Question.DIFFICULTY_CHOICES,
                        "content_statuses": Question.CONTENT_STATUS_CHOICES,
                        "csv_error": str(error),
                    },
                )
            request.session["question_csv_preview"] = preview
            return render(
                request,
                "admin/questions.html",
                {
                    "questions": _visible_questions_for_admin(request.user).order_by("-created_at"),
                    "question_skills": Question.SKILL_CHOICES,
                    "question_difficulties": Question.DIFFICULTY_CHOICES,
                    "content_statuses": Question.CONTENT_STATUS_CHOICES,
                    "csv_preview": preview,
                },
            )
        if action == "confirm_csv_import":
            preview = request.session.pop("question_csv_preview", [])
            if not preview:
                messages.error(request, "Upload a CSV file again before confirming.")
                return redirect("admin_questions")
            created = 0
            for data in preview:
                if not Question.objects.filter(
                    question_text=data["question_text"]
                ).exists():
                    Question.objects.create(
                        **data,
                        created_by=request.user,
                        status="draft",
                    )
                    created += 1
            messages.success(request, f"{created} question(s) imported.")
            return redirect("admin_questions")

        data = {
            field: request.POST.get(field, "").strip()
            for field in (
                "question_text", "option_a", "option_b", "option_c",
                "option_d", "correct_answer", "skill", "difficulty",
                "explanation",
            )
        }
        required = (
            "question_text", "option_a", "option_b", "option_c",
            "option_d", "correct_answer", "skill", "difficulty",
        )
        if any(not data[field] for field in required):
            messages.error(request, "Complete all required question fields.")
        else:
            if (
                data["correct_answer"] not in {"A", "B", "C", "D"}
                or data["skill"] not in dict(Question.SKILL_CHOICES)
                or data["difficulty"] not in dict(Question.DIFFICULTY_CHOICES)
            ):
                messages.error(request, "Choose valid question options.")
            else:
                Question.objects.create(
                    **data,
                    created_by=request.user,
                    status="draft",
                    assessment_enabled=request.POST.get("assessment_enabled") == "on",
                )
                messages.success(request, "Question saved.")
        return redirect("admin_questions")

    return render(
        request,
        "admin/questions.html",
        {
            "questions": _visible_questions_for_admin(request.user).order_by("-created_at"),
            "question_skills": Question.SKILL_CHOICES,
            "question_difficulties": Question.DIFFICULTY_CHOICES,
            "content_statuses": Question.CONTENT_STATUS_CHOICES,
        },
    )


@staff_member_required(login_url="/admin/login/")
def admin_question_detail_view(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if question.status != "published" and not _can_manage_content(request.user, question):
        return redirect("admin_questions")
    if request.method == "POST":
        if not _can_manage_content(request.user, question):
            return redirect("admin_questions")
        data = {
            field: request.POST.get(field, "").strip()
            for field in (
                "question_text", "option_a", "option_b", "option_c",
                "option_d", "correct_answer", "skill", "difficulty", "explanation",
            )
        }
        status = request.POST.get("status", "draft")
        valid = (
            all(data[field] for field in (
                "question_text", "option_a", "option_b", "option_c",
                "option_d", "correct_answer", "skill", "difficulty",
            ))
            and data["correct_answer"] in {"A", "B", "C", "D"}
            and data["skill"] in dict(Question.SKILL_CHOICES)
            and data["difficulty"] in dict(Question.DIFFICULTY_CHOICES)
            and status in dict(Question.CONTENT_STATUS_CHOICES)
        )
        if not valid:
            messages.error(request, "Check all required question fields and select valid choices.")
        else:
            for field, value in data.items():
                setattr(question, field, value)
            question.status = status
            question.assessment_enabled = request.POST.get("assessment_enabled") == "on"
            question.save()
            messages.success(request, "Question changes saved.")
            return redirect("admin_question_detail", question_id=question.id)
    answers = AssessmentAnswer.objects.filter(question=question)
    can_review = _can_manage_content(request.user, question)
    review_answers = answers if can_review else AssessmentAnswer.objects.none()
    practice_answers = (
        PracticeQuestionAttempt.objects.filter(question=question).select_related("user")
        if can_review else PracticeQuestionAttempt.objects.none()
    )
    return render(
        request,
        "admin/question_detail.html",
        {
            "question": question,
            "answer_count": review_answers.count() + practice_answers.count(),
            "correct_count": review_answers.filter(is_correct=True).count() + practice_answers.filter(is_correct=True).count(),
            "student_count": len(set(review_answers.values_list("attempt__user_id", flat=True)) | set(practice_answers.values_list("user_id", flat=True))),
            "recent_answers": review_answers.select_related("attempt__user").order_by("-id")[:25],
            "recent_practice_answers": practice_answers.order_by("-answered_at", "-id")[:25],
            "can_manage": _can_manage_content(request.user, question),
            "can_review": can_review,
            "question_skills": Question.SKILL_CHOICES,
            "question_difficulties": Question.DIFFICULTY_CHOICES,
            "content_statuses": Question.CONTENT_STATUS_CHOICES,
            "question_options": (
                ("A", question.option_a), ("B", question.option_b),
                ("C", question.option_c), ("D", question.option_d),
            ),
        },
    )


@staff_member_required(login_url="/admin/login/")
def admin_user_detail_view(request, user_id):
    student = get_object_or_404(
        User,
        id=user_id,
        is_staff=False,
        is_superuser=False,
    )
    profile, _ = StudentProfile.objects.get_or_create(user=student)
    progress, _ = LearningProgress.objects.get_or_create(user=student)
    attempts = list(
        AssessmentAttempt.objects.filter(
            user=student, is_completed=True
        ).order_by("-completed_at", "-id")
    )
    answers = AssessmentAnswer.objects.filter(
        attempt__user=student,
        attempt__is_completed=True,
    ).select_related("question")
    skill_stats = {}
    for answer in answers:
        skill = answer.question.get_skill_display()
        stats = skill_stats.setdefault(skill, {"total": 0, "correct": 0})
        stats["total"] += 1
        stats["correct"] += int(answer.is_correct)
    skill_analytics = [
        {
            "skill": skill,
            "total": stats["total"],
            "correct": stats["correct"],
            "percentage": round(stats["correct"] / stats["total"] * 100),
        }
        for skill, stats in sorted(skill_stats.items())
    ]
    return render(
        request,
        "admin/user_detail.html",
        {
            "student": student,
            "profile": profile,
            "progress": progress,
            "attempts": attempts,
            "skill_analytics": skill_analytics,
        },
    )


@staff_member_required(login_url="/admin/login/")
def admin_profile_edit_view(request):
    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        if not email:
            messages.error(request, "Email is required.")
        elif User.objects.exclude(pk=request.user.pk).filter(email=email).exists():
            messages.error(request, "That email is already in use.")
        else:
            request.user.email = email
            request.user.save(update_fields=["first_name", "last_name", "email"])
            messages.success(request, "Admin profile updated.")
            return redirect("admin_main")
    return render(
        request,
        "admin/profile_edit.html",
        {"admin_profile": request.user},
    )
# =========================================================
# PRACTICE LABS
# =========================================================

@staff_member_required(login_url="/admin/login/")
def admin_practice_labs_view(request):
    if request.method == "POST":
        action = request.POST.get("action", "add").strip()
        if action == "add":
            roadmap = normalize_career_goal(request.POST.get("roadmap", ""))
            submitted_skills = [" ".join(value.split()) for value in request.POST.getlist("skills")]
            skills = []
            seen_skills = set()
            for skill in submitted_skills:
                if skill and skill.casefold() not in seen_skills:
                    skills.append(skill)
                    seen_skills.add(skill.casefold())
            data = {
                "title": request.POST.get("title", "").strip(),
                "roadmap": roadmap,
                "skill": ", ".join(skills),
                "difficulty": request.POST.get("difficulty", "").strip(),
                "content_type": request.POST.get("content_type", "lab").strip(),
                "description": request.POST.get("description", "").strip(),
                "task": request.POST.get("task", "").strip(),
                "expected_answer": request.POST.get("expected_answer", "").strip(),
                "explanation": request.POST.get("explanation", "").strip(),
            }
            try:
                xp = int(request.POST.get("xp", "10"))
            except (TypeError, ValueError):
                xp = -1
            status = "draft"
            allowed_careers = dict(_practice_roadmap_choices())
            required = ("title", "roadmap", "skill", "difficulty", "description", "task")
            if any(not data[field] for field in required):
                messages.error(request, "Please complete all required Practice Lab fields.")
            elif data["roadmap"] not in allowed_careers:
                messages.error(request, "Choose a valid target career.")
            elif any(len(skill) > 60 for skill in skills) or len(data["skill"]) > 100:
                messages.error(request, "Skills must be 60 characters or fewer and fit within the 100-character skills field.")
            elif data["difficulty"] not in dict(PracticeLab.DIFFICULTY_CHOICES):
                messages.error(request, "Choose a valid difficulty.")
            elif data["content_type"] not in dict(PracticeLab.CONTENT_TYPE_CHOICES):
                messages.error(request, "Choose Skill Lab or Practice Challenge.")
            elif xp < 0 or status not in dict(PracticeLab.CONTENT_STATUS_CHOICES):
                messages.error(request, "Choose a valid XP value and content status.")
            else:
                PracticeLab.objects.create(
                    **data,
                    xp=xp,
                    status=status,
                    created_by=request.user,
                )
                messages.success(request, "Practice Lab saved.")
            return redirect("admin_practice_labs")

    search_query = request.GET.get("q", "").strip()
    labs = _visible_labs_for_admin(request.user).order_by("-created_at")
    if search_query:
        labs = labs.filter(
            Q(title__icontains=search_query)
            | Q(skill__icontains=search_query)
            | Q(roadmap__icontains=search_query)
            | Q(difficulty__icontains=search_query)
        )
    for lab in labs:
        lab.can_manage = _can_manage_content(request.user, lab)
        lab.practice_attempt_count = lab.practice_attempts.count()
        lab.recent_attempts = lab.practice_attempts.select_related("user").order_by("-submitted_at", "-id")[:5]
    return render(request, "admin/practice_labs.html", {
        "labs": labs,
        "roadmap_choices": _practice_roadmap_choices(),
        "skill_catalog_json": json.dumps(_practice_skill_catalog()),
        "difficulty_choices": PracticeLab.DIFFICULTY_CHOICES,
        "content_statuses": PracticeLab.CONTENT_STATUS_CHOICES,
        "content_type_choices": PracticeLab.CONTENT_TYPE_CHOICES,
        "search_query": search_query,
        "lab_count": labs.count(),
    })
###################################################################################################

# =========================================================
# EDIT PRACTICE LAB
# =========================================================

@staff_member_required(login_url="/admin/login/")
def admin_practice_lab_edit_view(request, lab_id):

    lab = get_object_or_404(
        PracticeLab,
        id=lab_id
    )
    if not _can_manage_content(request.user, lab):
        return redirect("admin_practice_labs")
    lab.roadmap = normalize_career_goal(lab.roadmap)

    if request.method == "POST":

        lab.title = request.POST.get(
            "title", ""
        ).strip()

        lab.roadmap = normalize_career_goal(request.POST.get(
            "roadmap", ""
        ).strip())

        lab.skill = request.POST.get(
            "skill", ""
        ).strip()

        lab.difficulty = request.POST.get(
            "difficulty", ""
        ).strip()
        lab.content_type = request.POST.get("content_type", "lab").strip()

        lab.description = request.POST.get(
            "description", ""
        ).strip()

        lab.task = request.POST.get(
            "task", ""
        ).strip()

        lab.expected_answer = request.POST.get(
            "expected_answer", ""
        ).strip()

        lab.explanation = request.POST.get(
            "explanation", ""
        ).strip()
        status = request.POST.get("status", "draft")

        try:

            lab.xp = int(
                request.POST.get(
                    "xp", "10"
                )
            )

            if (
                lab.roadmap not in dict(_practice_roadmap_choices())
                or lab.difficulty not in dict(PracticeLab.DIFFICULTY_CHOICES)
                or lab.content_type not in dict(PracticeLab.CONTENT_TYPE_CHOICES)
                or status not in dict(PracticeLab.CONTENT_STATUS_CHOICES)
                or lab.xp < 0
                or len(lab.skill) > 100
                or not all((lab.title, lab.skill, lab.description, lab.task))
            ):
                raise ValueError
            lab.status = status
            lab.save()

            messages.success(
                request,
                "Practice Lab updated successfully."
            )

            return redirect(
                "admin_practice_labs"
            )

        except (ValueError, TypeError):

            messages.error(request, "Check required fields, career, difficulty, content type, publication status, skills, and XP.")


    return render(
        request,
        "admin/practice_lab_edit.html",
        {
            "lab": lab,
            "roadmap_choices": _practice_roadmap_choices(),
            "difficulty_choices": PracticeLab.DIFFICULTY_CHOICES,
            "content_statuses": PracticeLab.CONTENT_STATUS_CHOICES,
            "content_type_choices": PracticeLab.CONTENT_TYPE_CHOICES,
        }
    )


# =========================================================
# DELETE PRACTICE LAB
# =========================================================

@staff_member_required(login_url="/admin/login/")
def admin_practice_lab_delete_view(request, lab_id):

    lab = get_object_or_404(
        PracticeLab,
        id=lab_id
    )
    if not _can_manage_content(request.user, lab):
        return redirect("admin_practice_labs")

    if request.method == "POST":

        lab.status = "archived"
        lab.save(update_fields=["status"])

        messages.success(
            request,
            "Practice Lab archived. Student work and content history were retained."
        )

    return redirect(
        "admin_practice_labs"
    )
