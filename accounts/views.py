from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from assessment.models import AssessmentAttempt
from .models import (
    StudentProfile,
    DashboardChecklistProgress,
    LearningProgress,
    LearningAttendance,
    MissionProgress,
    InterviewAnswer,
    normalize_career_goal,
)
from .decorators import onboarding_required
from .dashboard_metrics import assessment_percentage, current_day_streak, percentage, summarize_missions
from techpilot.career_content import (
    CAREER_CHOICES,
    CAREER_SKILLS,
    interviews_for_career,
    projects_for_career,
)
from .skill_status import career_skill_status


DASHBOARD_CHECKLIST_ITEMS = (
    {
        "key": "skill_assessment",
        "title": "Complete your first skill assessment",
        "subtitle": "Skill Assessment • 15 mins",
        "xp": 20,
    },
    {
        "key": "weakest_skill",
        "title": "Review your weakest skill",
        "subtitle": "Skill Improvement • 20 mins",
        "xp": 30,
    },
    {
        "key": "personalized_roadmap",
        "title": "Explore your personalized roadmap",
        "subtitle": "Career Planning • 10 mins",
        "xp": 25,
    },
)

# ============================================================
# HELPERS
# ============================================================

def redirect_to_next_step(user):
    profile, _ = StudentProfile.objects.get_or_create(user=user)

    if not profile.onboarding_completed:
        return redirect("onboarding")

    if not AssessmentAttempt.objects.filter(
        user=user, is_completed=True
    ).exists():
        return redirect("assessment")

    return redirect("dashboard")


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_main")
        return redirect_to_next_step(request.user)

    if request.method == "POST":
        account_type = request.POST.get("account_type", "student").strip().lower()

        if account_type == "admin":
            admin_key = request.POST.get("admin_key", "")

            if admin_key != settings.ADMIN_ACCESS_KEY:
                messages.error(request, "Invalid admin key.")
                return redirect("login")

            admin_user, created = User.objects.get_or_create(
                username="admin@techpilot.local",
                defaults={
                    "email": "admin@techpilot.local",
                    "first_name": "TechPilot Admin",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

            updates = []
            if not admin_user.is_staff:
                admin_user.is_staff = True
                updates.append("is_staff")
            if not admin_user.is_superuser:
                admin_user.is_superuser = True
                updates.append("is_superuser")
            if updates:
                admin_user.save(update_fields=updates)

            login(
                request,
                admin_user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            return redirect("admin_main")

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        if not email or not password:

            messages.error(
                request,
                "Please enter your email and password."
            )

            return redirect("login")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect_to_next_step(user)

        messages.error(
            request,
            "Invalid email or password."
        )

        return redirect("login")

    return render(
        request,
        "accounts/login.html",
        {
            "google_client_id": settings.GOOGLE_CLIENT_ID
        }
    )


# ============================================================
# GOOGLE LOGIN / SIGNUP
# ============================================================

def google_login(request):

    if request.method != "POST":
        return redirect("login")

    credential = request.POST.get(
        "credential",
        ""
    )

    if not credential:

        messages.error(
            request,
            "Google sign-in failed. Please try again."
        )

        return redirect("login")

    try:

        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        google_user_id = idinfo.get("sub")

        email = idinfo.get(
            "email",
            ""
        ).strip().lower()

        name = idinfo.get(
            "name",
            ""
        ).strip()

        if not google_user_id or not email:

            messages.error(
                request,
                "Google account information could not be verified."
            )

            return redirect("login")

        user = User.objects.filter(
            username=email
        ).first()

        if user is None:

            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=name
            )

            user.set_unusable_password()

            user.save()

        else:

            changed = False

            if not user.email:

                user.email = email
                changed = True

            if not user.first_name and name:

                user.first_name = name
                changed = True

            if changed:
                user.save()

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend"
        )

        return redirect_to_next_step(user)

    except ValueError:

        messages.error(
            request,
            "Invalid or expired Google sign-in."
        )

        return redirect("login")

    except Exception:

        messages.error(
            request,
            "Something went wrong with Google sign-in."
        )

        return redirect("login")


# ============================================================
# ONBOARDING
# ============================================================

@login_required(login_url="login")
def onboarding_view(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        # =========================================
        # EDUCATION
        # =========================================

        education = request.POST.get(
            "education",
            ""
        ).strip()


        # =========================================
        # YEAR
        # =========================================

        year = request.POST.get(
            "year",
            ""
        ).strip()


        # =========================================
        # SPECIALIZATION
        # =========================================

        specialization = request.POST.get(
            "specialization",
            ""
        ).strip()


        other_specialization = request.POST.get(
            "other_specialization",
            ""
        ).strip()


        if (
            specialization.lower() == "other"
            and other_specialization
        ):

            specialization = (
                other_specialization
            )


        # =========================================
        # CAREER GOAL
        # =========================================

        career_goal = request.POST.get(
            "career_goal",
            ""
        ).strip()


        other_career = request.POST.get(
            "other_career",
            ""
        ).strip()


        if (
            career_goal.lower() == "other"
            and other_career
        ):

            career_goal = (
                other_career
            )


        # =========================================
        # SKILLS
        # =========================================

        skills = request.POST.getlist(
            "skills"
        )


        other_skill = request.POST.get(
            "other_skill",
            ""
        ).strip()


        cleaned_skills = []


        for skill in skills:

            skill = skill.strip()


            if not skill:
                continue


            if skill.lower() == "other":

                if other_skill:
                    cleaned_skills.append(
                        other_skill
                    )

            else:

                cleaned_skills.append(
                    skill
                )


        # Remove duplicates
        # while preserving order

        skills = list(
            dict.fromkeys(
                cleaned_skills
            )
        )


        # =========================================
        # SKILL LEVEL
        # =========================================

        skill_level = request.POST.get(
            "skill_level",
            ""
        ).strip()


        # =========================================
        # STUDY TIME
        # =========================================

        study_time = request.POST.get(
            "study_time",
            "60"
        ).strip()


        try:

            study_time = int(
                study_time
            )

        except (
            ValueError,
            TypeError
        ):

            study_time = 60


        # =========================================
        # PREPARATION
        # =========================================

        preparation = request.POST.get(
            "preparation",
            ""
        ).strip()


        # =========================================
        # SAVE TO DATABASE
        # =========================================

        profile.education = education

        profile.year = year

        profile.specialization = (
            specialization
        )

        profile.career_goal = (
            normalize_career_goal(career_goal)
        )

        profile.skills = skills

        profile.skill_level = (
            skill_level
        )

        profile.study_time = (
            study_time
        )

        profile.preparation = (
            preparation
        )

        profile.onboarding_completed = True

        profile.save()


        # =========================================
        # REDIRECT
        # =========================================

        return redirect_to_next_step(request.user)


    # =============================================
    # GET
    # =============================================

    return render(
        request,
        "onboarding/onboarding.html",
        {
            "profile": profile,

            "student_name": (
                request.user.first_name
                or request.user.username.split("@")[0]
            )
        }
    )

# ============================================================
# REGISTER
# ============================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not name:

            messages.error(
                request,
                "Please enter your name."
            )

            return redirect("register")

        if not email:

            messages.error(
                request,
                "Please enter your email."
            )

            return redirect("register")

        if not password:

            messages.error(
                request,
                "Please create a password."
            )

            return redirect("register")

        if len(password) < 8:

            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

            return redirect("register")

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("register")

        if User.objects.filter(
            username=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

            return redirect("register")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        StudentProfile.objects.get_or_create(user=user)
        user.save()

        messages.success(
            request,
            "Account created successfully! Please sign in."
        )

        return redirect("login")

    return render(
        request,
        "accounts/register.html"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    return redirect("login")


# ============================================================
# DASHBOARD
# ============================================================

@onboarding_required

# ============================================================
# DASHBOARD
# ============================================================

@onboarding_required
def dashboard_view(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    student_name = (
        request.user.first_name
        or request.user.username.split("@")[0]
    )

    # --------------------------------------------------------
    # ASSESSMENT RESULT
    # AssessmentAttempt.score is already stored as a percentage.
    # Do not divide it by total_questions again.
    # --------------------------------------------------------
    latest_attempt = (
        AssessmentAttempt.objects
        .filter(user=request.user, is_completed=True)
        .order_by("-completed_at", "-id")
        .first()
    )

    assessment_score = assessment_percentage(latest_attempt)
    has_assessment = (
        latest_attempt is not None
        and latest_attempt.is_completed
        and latest_attempt.total_questions > 0
        and 0 <= latest_attempt.correct_answers <= latest_attempt.total_questions
    )

    current_career = normalize_career_goal(profile.career_goal)
    career_missions = MissionProgress.objects.filter(
        user=request.user,
        career_goal=current_career,
        day_number__gte=1,
        day_number__lte=20,
    )
    mission_metrics = summarize_missions(
        career_missions.order_by("day_number", "id").values(
            "day_number", "completed", "xp"
        )
    )
    completion_timestamps = MissionProgress.objects.filter(
        user=request.user,
        completed=True,
        completed_at__isnull=False,
    ).values_list("completed_at", flat=True)
    completion_dates = {
        timezone.localtime(completed_at).date()
        if timezone.is_aware(completed_at)
        else completed_at.date()
        for completed_at in completion_timestamps
    }
    streak = current_day_streak(completion_dates, timezone.localdate())
    saved_checklist = dict(
        DashboardChecklistProgress.objects.filter(
            user=request.user,
            career_goal=current_career,
        ).values_list("item_key", "completed")
    )
    checklist_items = [
        {**item, "completed": saved_checklist.get(item["key"], False)}
        for item in DASHBOARD_CHECKLIST_ITEMS
    ]
    checklist_xp = (
        DashboardChecklistProgress.objects.filter(
            user=request.user,
            career_goal=current_career,
        ).aggregate(total=Sum("xp_awarded"))["total"]
        or 0
    )
    career_skills = CAREER_SKILLS.get(current_career, [])
    skill_status = career_skill_status(
        request.user, profile, current_career, career_skills
    )
    missing_skills = skill_status["skills_to_build"]
    career_projects = projects_for_career(current_career)
    level = (
        profile.skill_level.title()
        if profile.skill_level and profile.skill_level.title()
        in {"Beginner", "Intermediate", "Advanced"}
        else "Beginner"
    )
    recommended_project = next(
        (item for item in career_projects if item["level"] == level),
        career_projects[0] if career_projects else None,
    )
    interview_catalog = interviews_for_career(current_career)
    answered_questions = set(
        InterviewAnswer.objects.filter(
            user=request.user,
            career_goal=current_career,
        ).values_list("question_key", flat=True)
    )
    recommended_interview = next(
        (
            question
            for question in interview_catalog.get("Beginner", [])
            if question["key"] not in answered_questions
        ),
        None,
    )

    context = {
        "student_name": student_name,
        "profile": profile,

        "career_goal": (
            current_career
            or "Choose your career goal"
        ),

        "education": (
            profile.education
            or "Not added"
        ),

        "year": (
            profile.year
            or "Not added"
        ),

        "specialization": (
            profile.specialization
            or "Not added"
        ),

        "skills": profile.skills or [],
        "skills_count": len(profile.skills or []),

        "skill_level": (
            profile.skill_level
            or "Not assessed"
        ),

        "study_time": profile.study_time,

        "preparation": (
            profile.preparation
            or "Skill Building"
        ),

        # Assessment data for dashboard
        "has_assessment": has_assessment,
        "assessment_score": assessment_score,
        "latest_attempt": latest_attempt,
        "total_xp": mission_metrics["earned_xp"] + checklist_xp,
        "checklist_items": checklist_items,
        "streak": streak,
        "missions_completed": mission_metrics["missions_completed"],
        "career_mission_count": mission_metrics["mission_count"],
        "mission_progress": mission_metrics["mission_progress"],
        "recommended_next_topic": (
            missing_skills[0] if missing_skills else "Review your strongest career skill"
        ),
        "recommended_project": recommended_project,
        "recommended_interview": recommended_interview,
        "missing_skills": missing_skills,
        "recommended_skills": skill_status["recommended_skills"],
        "learning_skills": skill_status["learning_skills"],
        "completed_skills": skill_status["completed_skills"],
        "assessment_skills": skill_status["assessment_skills"],
        "suggested_action": (
            "Start Day 1 of your career plan."
            if mission_metrics["mission_count"] == 0
            else f"Continue with {missing_skills[0]}."
            if missing_skills
            else "Review your completed plan and choose an advanced challenge."
        ),
    }

    return render(
        request,
        "dashboard.html",
        context
    )


@require_POST
@onboarding_required
def dashboard_checklist_update_view(request):
    item_key = request.POST.get("item_key", "")
    completed_value = request.POST.get("completed", "")
    item = next(
        (item for item in DASHBOARD_CHECKLIST_ITEMS if item["key"] == item_key),
        None,
    )
    if item is None or completed_value not in {"true", "false"}:
        return JsonResponse(
            {"error": "Choose a valid checklist item and completion state."},
            status=400,
        )

    completed = completed_value == "true"
    career_goal = normalize_career_goal(
        request.user.student_profile.career_goal
    )
    newly_awarded_xp = 0

    with transaction.atomic():
        progress, _ = DashboardChecklistProgress.objects.select_for_update().get_or_create(
            user=request.user,
            career_goal=career_goal,
            item_key=item_key,
        )
        if completed and not progress.completed:
            progress.completed = True
            if progress.xp_awarded == 0:
                progress.xp_awarded = item["xp"]
                newly_awarded_xp = item["xp"]
        elif not completed:
            progress.completed = False
        progress.save(update_fields=["completed", "xp_awarded", "updated_at"])

    mission_metrics = summarize_missions(
        MissionProgress.objects.filter(
            user=request.user,
            career_goal=career_goal,
            day_number__gte=1,
            day_number__lte=20,
        ).order_by("day_number", "id").values(
            "day_number", "completed", "xp"
        )
    )
    checklist_xp = (
        DashboardChecklistProgress.objects.filter(
            user=request.user,
            career_goal=career_goal,
        ).aggregate(total=Sum("xp_awarded"))["total"]
        or 0
    )
    return JsonResponse(
        {
            "completed": progress.completed,
            "xp_awarded": newly_awarded_xp,
            "total_xp": mission_metrics["earned_xp"] + checklist_xp,
        }
    )

# def dashboard_view(request):
# def dashboard_view(request):

#     profile, created = StudentProfile.objects.get_or_create(
#         user=request.user
#     )

#     student_name = (
#         request.user.first_name
#         or request.user.username.split("@")[0]
#     )

#     context = {

#         "student_name": student_name,

#         "profile": profile,

#         "career_goal": (
#             profile.career_goal
#             or "Choose your career goal"
#         ),

#         "education": (
#             profile.education
#             or "Not added"
#         ),

#         "year": (
#             profile.year
#             or "Not added"
#         ),

#         "specialization": (
#             profile.specialization
#             or "Not added"
#         ),

#         "skills": (
#             profile.skills
#             or []
#         ),

#         "skill_level": (
#             profile.skill_level
#             or "Not assessed"
#         ),

#         "study_time": profile.study_time,

#         "preparation": (
#             profile.preparation
#             or "Skill Building"
#         ),
#     }

#     return render(
#         request,
#         "dashboard.html",
#         context
#     )


# ============================================================
# EDIT PROFILE
# ============================================================

@onboarding_required
def edit_profile_view(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )
    profile.career_goal = normalize_career_goal(profile.career_goal)

    # --------------------------------------------------------
    # Save Updated Profile
    # --------------------------------------------------------

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        education = request.POST.get(
            "education",
            ""
        ).strip()

        year = request.POST.get(
            "year",
            ""
        ).strip()

        specialization = request.POST.get(
            "specialization",
            ""
        ).strip()

        career_goal = request.POST.get(
            "career_goal",
            ""
        ).strip()

        career_goal = normalize_career_goal(career_goal)
        if career_goal and career_goal not in CAREER_CHOICES:
            messages.error(request, "Please choose a valid career goal.")
            return redirect("edit_profile")

        skills = []
        seen_skills = set()
        for raw_skill in request.POST.getlist("skills"):
            skill = " ".join(raw_skill.split())
            key = skill.casefold()
            if skill and key not in seen_skills:
                skills.append(skill)
                seen_skills.add(key)
        if any(len(skill) > 100 for skill in skills):
            messages.error(request, "Each skill must be 100 characters or fewer.")
            return redirect("edit_profile")

        skill_level = request.POST.get(
            "skill_level",
            ""
        ).strip()

        study_time = request.POST.get(
            "study_time",
            "60"
        ).strip()

        preparation = request.POST.get(
            "preparation",
            ""
        ).strip()

        # ----------------------------------------------------
        # Update User Name
        # ----------------------------------------------------

        if name:

            request.user.first_name = name

            request.user.save()


        # ----------------------------------------------------
        # Convert Study Time
        # ----------------------------------------------------

        try:

            study_time = int(
                study_time
            )

        except (ValueError, TypeError):

            study_time = 60


        # ----------------------------------------------------
        # Update Student Profile
        # ----------------------------------------------------

        profile.education = education

        profile.year = year

        profile.specialization = specialization

        profile.career_goal = career_goal

        profile.skills = skills

        profile.skill_level = skill_level

        profile.study_time = study_time

        profile.preparation = preparation

        profile.onboarding_completed = True

        profile.save()


        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        messages.success(
            request,
            "Profile updated successfully! ✨"
        )

        return redirect("dashboard")


    # --------------------------------------------------------
    # Edit Profile Page
    # --------------------------------------------------------

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "profile": profile,

            "student_name": (
                request.user.first_name
                or request.user.username.split("@")[0]
            ),
            "skill_recommendations": CAREER_SKILLS,
            "current_career_skills": CAREER_SKILLS.get(
                profile.career_goal, CAREER_SKILLS["Not Sure Yet"]
            ),
            "saved_skills": profile.skills or [],
        }
    )
    
# ============================================================
# PROFILE
# ============================================================

@onboarding_required
def profile_view(request):

    # --------------------------------------------------------
    # STUDENT PROFILE
    # --------------------------------------------------------

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )


    # --------------------------------------------------------
    # STUDENT NAME
    # --------------------------------------------------------

    student_name = (
        request.user.first_name
        or request.user.username.split("@")[0]
    )


    # --------------------------------------------------------
    # LEARNING PROGRESS
    # --------------------------------------------------------

    learning_progress, created = (
        LearningProgress.objects.get_or_create(
            user=request.user
        )
    )


    # --------------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------------

    latest_attempt = (
        AssessmentAttempt.objects
        .filter(user=request.user, is_completed=True)
        .order_by("-completed_at", "-id")
        .first()
    )

    assessment_score = assessment_percentage(latest_attempt)
    has_assessment = (
        latest_attempt is not None
        and latest_attempt.is_completed
        and latest_attempt.total_questions > 0
        and 0 <= latest_attempt.correct_answers <= latest_attempt.total_questions
    )
    # assessment_score = 0

    # has_assessment = False


    # if latest_attempt:

    #     has_assessment = True

    #     total_questions = (
    #         latest_attempt.total_questions or 0
    #     )

    #     if total_questions > 0:

    #         assessment_score = round(
    #             (
    #                 latest_attempt.score
    #                 / total_questions
    #             ) * 100
    #         )


    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    attendance_records = (
        LearningAttendance.objects
        .filter(user=request.user)
        .order_by("-date")
    )


    total_learning_days = (
        attendance_records.count()
    )


    attended_days = (
        attendance_records
        .filter(attended=True)
        .count()
    )


    if total_learning_days > 0:

        attendance = round(
            (
                attended_days
                / total_learning_days
            ) * 100
        )

    else:

        attendance = 0


    # --------------------------------------------------------
    # MISSIONS
    # --------------------------------------------------------

    current_career = normalize_career_goal(profile.career_goal)
    missions_completed = (
        MissionProgress.objects
        .filter(
            user=request.user,
            career_goal=current_career,
            completed=True
        )
        .count()
    )


    mission_metrics = summarize_missions(
        MissionProgress.objects.filter(
            user=request.user,
            career_goal=current_career,
            day_number__gte=1,
            day_number__lte=20,
        ).values("day_number", "completed", "xp")
    )
    missions_completed = mission_metrics["missions_completed"]
    mission_progress = mission_metrics["mission_progress"]
    progress = mission_progress


    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        # Student
        "profile": profile,
        "student_name": student_name,

        # Assessment
        "assessment_score": assessment_score,
        "has_assessment": has_assessment,
        "latest_attempt": latest_attempt,

        # Progress
        "progress": progress,
        "attendance": attendance,

        # Learning Progress
        "streak": (
            learning_progress.current_streak
        ),
        "learning_progress": learning_progress,

        "total_xp": (
            MissionProgress.objects.filter(
                user=request.user,
                career_goal=current_career,
                completed=True,
            )
            .aggregate(total=Sum("xp"))["total"] or 0
        ),

        # Missions
        "missions_completed": (
            missions_completed
        ),

        "mission_progress": (
            mission_progress
        ),

        # Other learning
        "practice_completed": (
            learning_progress.practice_completed
        ),

        "projects_completed": (
            learning_progress.projects_completed
        ),

        "interviews_completed": (
            learning_progress.interviews_completed
        ),

    }


    return render(
        request,
        "accounts/profile.html",
        context
    )
