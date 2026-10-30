from django.contrib import admin
from django.urls import path

from accounts.views import (
    login_view,
    register_view,
    logout_view,
    dashboard_view,
    dashboard_checklist_update_view,
    google_login,
    onboarding_view,
    profile_view,
    edit_profile_view,
)

from .views import (
    roadmap_view,
    missions_view,
    mission_detail_view,
    assessment_view,
    roadmap_test_view,
    assessment_result_view,
    practice_view,
    projects_view,
    jobs_view,
    interviews_view,
    progress_view,
)
from accounts.admin_views import (
    admin_main_view,
    admin_questions_view,
    admin_question_detail_view,
    admin_users_view,
    admin_profile_edit_view,
    admin_user_detail_view,
    admin_practice_labs_view,
    admin_practice_lab_edit_view,
    admin_practice_lab_delete_view,
)


urlpatterns = [

    # =====================================
    # ADMIN
    # =====================================

   # =====================================
# ADMIN
# =====================================

path(
    "admin/main/",
    admin_main_view,
    name="admin_main",
),

path(
    "admin/main/users/<int:user_id>/",
    admin_user_detail_view,
    name="admin_user_detail",
),

path(
    "admin/main/users/",
    admin_users_view,
    name="admin_users",
),

path(
    "admin/main/questions/",
    admin_questions_view,
    name="admin_questions",
),

# =====================================
# PRACTICE LABS
# =====================================

path(
    "admin/main/practice-labs/",
    admin_practice_labs_view,
    name="admin_practice_labs",
),

path(
    "admin/main/practice-labs/<int:lab_id>/edit/",
    admin_practice_lab_edit_view,
    name="admin_practice_lab_edit",
),

path(
    "admin/main/practice-labs/<int:lab_id>/delete/",
    admin_practice_lab_delete_view,
    name="admin_practice_lab_delete",
),

# =====================================
# QUESTION DETAIL
# =====================================

path(
    "admin/main/questions/<int:question_id>/",
    admin_question_detail_view,
    name="admin_question_detail",
),

path(
    "admin/main/profile/edit/",
    admin_profile_edit_view,
    name="admin_profile_edit",
),

path(
    "admin/",
    admin.site.urls
),
    # =====================================
    # AUTHENTICATION
    # =====================================

    path(
        "",
        login_view,
        name="login"
    ),

    path(
        "register/",
        register_view,
        name="register"
    ),

    path(
        "logout/",
        logout_view,
        name="logout"
    ),

    # Google Login / Signup
    path(
        "google-login/",
        google_login,
        name="google_login"
    ),


    # =====================================
    # ONBOARDING
    # =====================================

    path(
        "onboarding/",
        onboarding_view,
        name="onboarding"
    ),


    # =====================================
    # DASHBOARD
    # =====================================

    path(
        "dashboard/",
        dashboard_view,
        name="dashboard"
    ),

    path(
        "dashboard/checklist/",
        dashboard_checklist_update_view,
        name="dashboard_checklist_update",
    ),


    # =====================================
    # PROFILE
    # =====================================

    path(
        "profile/",
        profile_view,
        name="profile"
    ),
    
    path(
        "profile/edit/",
        edit_profile_view,
        name="edit_profile"
    ),


    # =====================================
    # ROADMAP
    # =====================================

    path(
        "roadmap/",
        roadmap_view,
        name="roadmap"
    ),


    # =====================================
    # DAILY MISSIONS
    # =====================================

    path(
        "missions/",
        missions_view,
        name="missions"
    ),

    # Start / Open Mission
    path(
        "missions/start/",
        mission_detail_view,
        name="mission_detail"
    ),


    # =====================================
    # ASSESSMENT
    # =====================================

    path(
        "assessment/",
        assessment_view,
        name="assessment"
    ),

    path(
        "roadmap/test/",
        roadmap_test_view,
        name="roadmap_test"
    ),

    path(
        "assessment/result/<int:attempt_id>/",
        assessment_result_view,
        name="assessment_result"
    ),


    # =====================================
    # PRACTICE
    # =====================================

    path(
        "practice/",
        practice_view,
        name="practice"
    ),


    # =====================================
    # PROJECTS
    # =====================================

    path(
        "projects/",
        projects_view,
        name="projects"
    ),


    # =====================================
    # JOBS
    # =====================================

    path(
        "jobs/",
        jobs_view,
        name="jobs"
    ),


    # =====================================
    # INTERVIEWS
    # =====================================

    path(
        "interviews/",
        interviews_view,
        name="interviews"
    ),

    path(
        "progress/",
        progress_view,
        name="progress"
    ),

]
