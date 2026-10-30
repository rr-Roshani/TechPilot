from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from accounts.decorators import onboarding_required
from accounts.skill_status import career_skill_status
from accounts.dashboard_metrics import assessment_percentage, percentage, summarize_missions
from accounts.models import (
    StudentProfile,
    MissionProgress,
    MissionQuizAttempt,
    LearningProgress,
    LearningAttendance,
    InterviewAnswer,
    InterviewDayProgress,
    normalize_career_goal,
)

from assessment.models import (
    Question,
    AssessmentAttempt,
    AssessmentAnswer,
    PracticeLab,
    PracticeLabAttempt,
    PracticeQuestionAttempt,
)
from .career_content import (
    CAREER_CHOICES,
    CAREER_SKILLS,
    DAY_TOPICS,
    interviews_for_career,
    job_roles_for_career,
    projects_for_career,
)


# =========================================================
# HELPER
# =========================================================

def get_student_name(request):
    return (
        request.user.first_name
        or request.user.username.split("@")[0]
    )


def save_career_selection(profile, value):
    career = normalize_career_goal(value)
    if career not in CAREER_CHOICES:
        return False
    if profile.career_goal != career:
        profile.career_goal = career
        profile.save(update_fields=["career_goal", "updated_at"])
    return True


def career_guidance(user, profile):
    career = normalize_career_goal(profile.career_goal)
    if career not in CAREER_CHOICES:
        return {
            "career_goal": profile.career_goal or "Choose a career on your Roadmap",
            "career_skills": [],
            "missing_skills": [],
            "recommended_next_topic": "Choose a career on your Roadmap to get a beginner starting point.",
            "recommended_project": None,
            "recommended_interview": None,
            "career_missions_completed": 0,
            "career_mission_count": 0,
            "career_progress_percent": None,
            "suggested_action": "Choose a career on your Roadmap.",
        }

    skills = CAREER_SKILLS[career]
    skill_status = career_skill_status(user, profile, career, skills)
    missing = skill_status["skills_to_build"]
    career_missions = MissionProgress.objects.filter(
        user=user,
        career_goal=career,
        day_number__gte=1,
        day_number__lte=20,
    )
    mission_metrics = summarize_missions(
        career_missions.values("day_number", "completed", "xp")
    )
    completed = mission_metrics["missions_completed"]
    mission_count = mission_metrics["mission_count"]
    project_level = (
        profile.skill_level.title()
        if profile.skill_level and profile.skill_level.title() in {
            "Beginner", "Intermediate", "Advanced"
        }
        else "Beginner"
    )
    projects = projects_for_career(career)
    recommended_project = next(
        (p for p in projects if p["level"] == project_level),
        projects[0] if projects else None,
    )
    questions = interviews_for_career(career).get("Beginner", [])
    answered_keys = set(
        InterviewAnswer.objects.filter(
            user=user,
            career_goal=career,
        ).values_list("question_key", flat=True)
    )
    recommended_interview = next(
        (q for q in questions if q["key"] not in answered_keys),
        questions[0] if questions else None,
    )
    return {
        "career_goal": career,
        "career_skills": skills,
        "missing_skills": missing,
        "known_skills": skill_status["known_skills"],
        "recommended_skills": skill_status["recommended_skills"],
        "learning_skills": skill_status["learning_skills"],
        "completed_skills": skill_status["completed_skills"],
        "assessment_skills": skill_status["assessment_skills"],
        "recommended_next_topic": missing[0] if missing else (skills[-1] if skills else "Explore career options"),
        "recommended_project": recommended_project,
        "recommended_interview": recommended_interview,
        "career_missions_completed": completed,
        "career_mission_count": mission_count,
        "career_progress_percent": mission_metrics["mission_progress"],
        "suggested_action": (
            "Start Day 1 of your career plan."
            if completed == 0
            else f"Continue with {missing[0]}."
            if missing
            else "Review your completed plan and choose an advanced challenge."
        ),
    }


# =========================================================
# ROADMAP
# =========================================================

@onboarding_required
def roadmap_view(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    career_selection = (
        request.POST.get("career")
        if request.method == "POST"
        else request.GET.get("career")
    )
    if career_selection is not None:
        save_career_selection(profile, career_selection)
        return redirect("roadmap")

    roadmap_choices = CAREER_CHOICES
    career_goal = normalize_career_goal(profile.career_goal) or "Not Sure Yet"
    career_goal = normalize_career_goal(career_goal)
    skills = profile.skills or []
    skill_level = profile.skill_level or "Beginner"

    latest_attempt = (
        AssessmentAttempt.objects
        .filter(user=request.user, is_completed=True)
        .order_by("-completed_at", "-id")
        .first()
    )

    assessment_score = assessment_percentage(latest_attempt)
    skill_scores = {}
    priority_skills = []

    if latest_attempt:

        answers = (
            AssessmentAnswer.objects
            .filter(attempt=latest_attempt)
            .select_related("question")
        )

        skill_stats = {}

        for answer in answers:

            skill = (
                answer.question.skill
                .lower()
                .strip()
            )

            if skill not in skill_stats:
                skill_stats[skill] = {
                    "total": 0,
                    "correct": 0,
                }

            skill_stats[skill]["total"] += 1

            if answer.is_correct:
                skill_stats[skill]["correct"] += 1

        for skill, data in skill_stats.items():

            total = data["total"]
            correct = data["correct"]

            if total:
                percentage = round(
                    (correct / total) * 100
                )
            else:
                percentage = 0

            skill_scores[skill] = percentage

            if percentage < 60:
                priority_skills.append({
                    "skill": (
                        skill
                        .replace("_", " ")
                        .title()
                    ),
                    "percentage": percentage,
                })

        priority_skills.sort(
            key=lambda item: item["percentage"]
        )

    # =====================================================
    # ROADMAP DATA
    # =====================================================

    roadmap_data = {

        "Cloud Engineer": [

            {
                "title": "Programming Foundations",
                "description": (
                    "Strengthen Python and programming fundamentals."
                ),
                "skills": [
                    "Python",
                    "Problem Solving",
                ],
                "status": "completed",
                "progress": 100,
            },

            {
                "title": "Linux & Networking",
                "description": (
                    "Learn Linux commands, networking and "
                    "system fundamentals."
                ),
                "skills": [
                    "Linux",
                    "Networking",
                ],
                "status": "in_progress",
                "progress": 60,
            },

            {
                "title": "Cloud Fundamentals",
                "description": (
                    "Understand cloud computing, regions, "
                    "services and architecture."
                ),
                "skills": [
                    "Cloud Computing",
                    "AWS",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "AWS Core Services",
                "description": (
                    "Learn EC2, S3, IAM, VPC and "
                    "essential AWS services."
                ),
                "skills": [
                    "AWS",
                    "EC2",
                    "S3",
                    "IAM",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "DevOps & Deployment",
                "description": (
                    "Learn Docker, CI/CD and "
                    "application deployment."
                ),
                "skills": [
                    "Docker",
                    "CI/CD",
                    "Git",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Cloud Projects & Job Ready",
                "description": (
                    "Build cloud projects and prepare "
                    "for cloud engineering interviews."
                ),
                "skills": [
                    "Projects",
                    "Resume",
                    "Interview",
                ],
                "status": "locked",
                "progress": 0,
            },
        ],

        "Full Stack Developer": [

            {
                "title": "Programming Foundations",
                "description": (
                    "Build strong programming and "
                    "problem-solving fundamentals."
                ),
                "skills": [
                    "Python",
                    "JavaScript",
                ],
                "status": "completed",
                "progress": 100,
            },

            {
                "title": "Frontend Development",
                "description": (
                    "Learn HTML, CSS, JavaScript and "
                    "modern frontend concepts."
                ),
                "skills": [
                    "HTML",
                    "CSS",
                    "JavaScript",
                ],
                "status": "in_progress",
                "progress": 60,
            },

            {
                "title": "React Development",
                "description": (
                    "Build interactive applications "
                    "using React."
                ),
                "skills": [
                    "React",
                    "JavaScript",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Backend Development",
                "description": (
                    "Learn APIs, authentication and "
                    "backend development."
                ),
                "skills": [
                    "Django",
                    "Node.js",
                    "REST API",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Databases & Deployment",
                "description": (
                    "Work with databases and deploy "
                    "full-stack applications."
                ),
                "skills": [
                    "SQL",
                    "MongoDB",
                    "Docker",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Full Stack Projects & Job Ready",
                "description": (
                    "Build portfolio projects and "
                    "prepare for interviews."
                ),
                "skills": [
                    "Projects",
                    "GitHub",
                    "Interview",
                ],
                "status": "locked",
                "progress": 0,
            },
        ],

        "Data Analyst": [

            {
                "title": "Data & Programming Foundations",
                "description": (
                    "Build Python and analytical "
                    "thinking fundamentals."
                ),
                "skills": [
                    "Python",
                    "Statistics",
                ],
                "status": "completed",
                "progress": 100,
            },

            {
                "title": "SQL & Databases",
                "description": (
                    "Learn SQL queries, joins, aggregation "
                    "and database concepts."
                ),
                "skills": [
                    "SQL",
                    "Databases",
                ],
                "status": "in_progress",
                "progress": 60,
            },

            {
                "title": "Data Analysis with Python",
                "description": (
                    "Analyze and clean datasets "
                    "using Python."
                ),
                "skills": [
                    "Python",
                    "Pandas",
                    "NumPy",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Data Visualization",
                "description": (
                    "Create meaningful dashboards "
                    "and visualizations."
                ),
                "skills": [
                    "Tableau",
                    "Power BI",
                    "Charts",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Analytics Projects",
                "description": (
                    "Solve real-world business "
                    "and data problems."
                ),
                "skills": [
                    "Projects",
                    "Analytics",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Job Ready",
                "description": (
                    "Prepare your portfolio, resume "
                    "and analyst interviews."
                ),
                "skills": [
                    "Resume",
                    "Portfolio",
                    "Interview",
                ],
                "status": "locked",
                "progress": 0,
            },
        ],

        "AI/ML Engineer": [

            {
                "title": "Python & Mathematics",
                "description": (
                    "Build programming, statistics "
                    "and mathematics foundations."
                ),
                "skills": [
                    "Python",
                    "Statistics",
                    "Math",
                ],
                "status": "completed",
                "progress": 100,
            },

            {
                "title": "Data Analysis",
                "description": (
                    "Learn NumPy, Pandas and "
                    "data preprocessing."
                ),
                "skills": [
                    "NumPy",
                    "Pandas",
                    "Data",
                ],
                "status": "in_progress",
                "progress": 60,
            },

            {
                "title": "Machine Learning",
                "description": (
                    "Learn supervised and "
                    "unsupervised machine learning."
                ),
                "skills": [
                    "Machine Learning",
                    "Scikit-learn",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Deep Learning",
                "description": (
                    "Understand neural networks "
                    "and deep learning concepts."
                ),
                "skills": [
                    "Neural Networks",
                    "Deep Learning",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "AI Projects",
                "description": (
                    "Build practical AI and "
                    "machine learning projects."
                ),
                "skills": [
                    "AI",
                    "ML",
                    "Projects",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "AI/ML Job Ready",
                "description": (
                    "Prepare your portfolio and "
                    "technical interviews."
                ),
                "skills": [
                    "Portfolio",
                    "Resume",
                    "Interview",
                ],
                "status": "locked",
                "progress": 0,
            },
        ],

        "Cybersecurity": [

            {
                "title": "Programming Foundations",
                "description": (
                    "Build Python and "
                    "problem-solving fundamentals."
                ),
                "skills": [
                    "Python",
                    "Programming",
                ],
                "status": "completed",
                "progress": 100,
            },

            {
                "title": "Linux & Networking",
                "description": (
                    "Understand operating systems, "
                    "networks and Linux."
                ),
                "skills": [
                    "Linux",
                    "Networking",
                ],
                "status": "in_progress",
                "progress": 60,
            },

            {
                "title": "Cybersecurity Fundamentals",
                "description": (
                    "Learn core security concepts, "
                    "threats and vulnerabilities."
                ),
                "skills": [
                    "Security",
                    "Threats",
                    "Vulnerabilities",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Ethical Hacking",
                "description": (
                    "Learn security testing "
                    "and defensive concepts."
                ),
                "skills": [
                    "Web Security",
                    "Security Testing",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Security Projects",
                "description": (
                    "Build practical cybersecurity "
                    "projects and labs."
                ),
                "skills": [
                    "Labs",
                    "Projects",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Cybersecurity Job Ready",
                "description": (
                    "Prepare your resume, portfolio "
                    "and security interviews."
                ),
                "skills": [
                    "Resume",
                    "Portfolio",
                    "Interview",
                ],
                "status": "locked",
                "progress": 0,
            },
        ],

        "Android Developer": [
            {
                "title": "Kotlin & Android Foundations",
                "description": "Learn Kotlin, Android Studio, and app structure.",
                "skills": ["Kotlin", "Android Studio"],
                "status": "locked", "progress": 0,
            },
            {
                "title": "Layouts & App Interaction",
                "description": "Build accessible screens and handle user input.",
                "skills": ["Layouts", "Compose", "Accessibility"],
                "status": "locked", "progress": 0,
            },
            {
                "title": "Lifecycle & Navigation",
                "description": "Manage screen state and app navigation.",
                "skills": ["Activities", "Lifecycle", "Navigation"],
                "status": "locked", "progress": 0,
            },
            {
                "title": "Persistence & APIs",
                "description": "Store app data locally and consume APIs safely.",
                "skills": ["Room", "REST APIs", "Coroutines"],
                "status": "locked", "progress": 0,
            },
            {
                "title": "Testing & Release",
                "description": "Test, package, and prepare Android projects for release.",
                "skills": ["Testing", "Security", "Release"],
                "status": "locked", "progress": 0,
            },
            {
                "title": "Android Portfolio & Interview Prep",
                "description": "Demonstrate reliable mobile projects and explain design choices.",
                "skills": ["Portfolio", "Architecture", "Interview"],
                "status": "locked", "progress": 0,
            },
        ],

        "Not Sure Yet": [

            {
                "title": "Explore Tech Careers",
                "description": (
                    "Understand different "
                    "technology career paths."
                ),
                "skills": [
                    "Career Discovery",
                ],
                "status": "in_progress",
                "progress": 40,
            },

            {
                "title": "Skill Assessment",
                "description": (
                    "Assess your current technical "
                    "strengths and weaknesses."
                ),
                "skills": [
                    "Assessment",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Career Match",
                "description": (
                    "Discover roles that match "
                    "your interests and skills."
                ),
                "skills": [
                    "Career Match",
                ],
                "status": "locked",
                "progress": 0,
            },

            {
                "title": "Choose Your Path",
                "description": (
                    "Select the career path "
                    "that fits you best."
                ),
                "skills": [
                    "Career Goal",
                ],
                "status": "locked",
                "progress": 0,
            },
        ],
    }

# =====================================================
# CAREER ROADMAP CHOICE
# =====================================================

    # roadmap_choices = [
    #     "Cloud Engineer",
    #     "Full Stack Developer",
    #     "Data Analyst",
    #     "AI/ML Engineer",
    #     "Cybersecurity",
    #     "DevOps Engineer",
    # ]

    # selected_roadmap = request.GET.get("career", "").strip()

    # # If user has selected a roadmap, use that.
    # # Otherwise use their onboarding career goal.
    # if selected_roadmap in roadmap_choices:
    #     career_goal = selected_roadmap
    # else:
    #     selected_roadmap = career_goal

    # # If onboarding career goal is not one of the available
    # # roadmap choices, show the chooser first.
    # if selected_roadmap not in roadmap_choices:
    #     stages = []
    #     career_goal = ""
    # else:
    #     stages = roadmap_data.get(
    #         selected_roadmap,
    #         roadmap_data["Not Sure Yet"]
    #     )


# =====================================================
# CAREER ROADMAP CHOICES
# =====================================================

    roadmap_choices = CAREER_CHOICES

    selected_roadmap = normalize_career_goal(profile.career_goal)


# User-selected roadmap
    career_goal = selected_roadmap or career_goal
    if selected_roadmap not in roadmap_choices:
        selected_roadmap = ""


# =====================================================
# SELECT ROADMAP
# =====================================================

    if selected_roadmap:

        stages = roadmap_data.get(
            "Cybersecurity" if selected_roadmap == "Cybersecurity Analyst" else selected_roadmap,
            []  
        )

        # The curated stage list is a curriculum outline. Start its progress
        # empty, then personalize it only from saved assessment evidence.
        for stage in stages:
            stage["status"] = "locked"
            stage["progress"] = 0

    else:

        stages = []
    # =====================================================
    # ASSESSMENT-BASED PERSONALIZATION
    # =====================================================

    aliases = {
        "python": ["python"],
        "sql": ["sql"],
        "git": ["git"],
        "aws": ["aws"],
        "linux": ["linux"],
        "javascript": ["javascript", "js"],
        "dsa": ["dsa"],
        "problem_solving": ["dsa"],
        "databases": ["sql"],
        "cloud_computing": ["aws"],
    }

    if latest_attempt and skill_scores:

        for stage in stages:

            matched_scores = []

            for stage_skill in stage["skills"]:

                normalized = (
                    stage_skill
                    .lower()
                    .replace("-", "_")
                    .replace(" ", "_")
                    .strip()
                )

                if normalized in skill_scores:

                    matched_scores.append(
                        skill_scores[normalized]
                    )

                    continue

                for alias in aliases.get(
                    normalized,
                    []
                ):

                    if alias in skill_scores:

                        matched_scores.append(
                            skill_scores[alias]
                        )

                        break

            if matched_scores:

                stage_progress = round(
                    sum(matched_scores)
                    / len(matched_scores)
                )

                stage["progress"] = stage_progress

                if stage_progress >= 80:
                    stage["status"] = "completed"

                elif stage_progress >= 40:
                    stage["status"] = "in_progress"

                else:
                    stage["status"] = "needs_focus"

    # =====================================================
    # OVERALL ROADMAP PROGRESS
    # =====================================================

    roadmap_missions = MissionProgress.objects.filter(
        user=request.user,
        career_goal=normalize_career_goal(career_goal),
    )
    completed_roadmap_missions = roadmap_missions.filter(completed=True).count()
    total_progress = (
        round(completed_roadmap_missions / 20 * 100)
        if roadmap_missions.exists()
        else None
    )

    # =====================================================
    # SKILL GAP MESSAGE
    # =====================================================

    if priority_skills:

        skill_gap_message = (
            "Your assessment identified skills that "
            "need more practice. TechPilot has prioritized "
            "them in your learning journey."
        )

    elif latest_attempt:

        skill_gap_message = (
            "Great work! Your assessment shows "
            "a strong technical foundation."
        )

    else:

        skill_gap_message = (
            "Complete your assessment to unlock "
            "your personalized skill gap."
        )

    # =====================================================
    # CONTEXT
    # =====================================================

    guidance = career_guidance(request.user, profile)
    context = {

        "profile": profile,

        "student_name": get_student_name(request),

        "career_goal": career_goal,
        "roadmap_choices": roadmap_choices,
        "selected_roadmap": selected_roadmap,

        "skills": skills,

        "skill_level": skill_level,

        "stages": stages,

        "total_progress": total_progress,
        "completed_missions": completed_roadmap_missions,

        "latest_attempt": latest_attempt,

        "assessment_score": assessment_score,

        "skill_scores": skill_scores,

        "priority_skills": priority_skills,

        "skill_gap_message": skill_gap_message,

        "has_assessment": bool(latest_attempt),
        "guidance": guidance,
    }

    return render(
        request,
        "roadmap/roadmap.html",
        context
    )


# =========================================================
# DAILY MISSIONS
# =========================================================


# =========================================================
# DAILY MISSIONS — 20 DAY PERSONALIZED PLAN
# =========================================================

@onboarding_required
def missions_view(request):
    today = timezone.localdate()

    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user
    )

    # Daily Missions must follow the currently selected roadmap.
    career_goal = normalize_career_goal(profile.career_goal) or "Not Sure Yet"

    skills = profile.skills or []
    study_time = profile.study_time or 60

    # -----------------------------------------------------
    # CAREER-SPECIFIC 20-DAY PLANS
    # Each item: title, category, description, minutes, XP
    # -----------------------------------------------------

    plans = {
        "Cloud Engineer": [
            ("Linux Command Sprint", "Linux",
             "Practice pwd, ls, cd, mkdir and file commands.", 20, 40),
            ("Cloud Computing Basics", "Cloud",
             "Understand cloud computing and its benefits.", 20, 40),
            ("AWS Fundamentals", "AWS",
             "Explore AWS and its core services.", 25, 50),
            ("Git Essentials", "Git",
             "Practice git init, add, commit and status.", 20, 40),
            ("Networking Basics", "Networking",
             "Learn IP, DNS, HTTP and ports.", 25, 50),
            ("AWS EC2 Introduction", "AWS",
             "Understand virtual machines and EC2.", 25, 50),
            ("AWS S3 Introduction", "AWS",
             "Learn buckets, objects and storage classes.", 25, 50),
            ("IAM and Security", "Security",
             "Understand users, roles and permissions.", 25, 50),
            ("Linux Permissions", "Linux",
             "Practice file permissions and ownership.", 20, 40),
            ("Cloud Architecture Quiz", "Quiz",
             "Revise cloud service and architecture concepts.", 15, 30),
            ("VPC Fundamentals", "AWS",
             "Learn virtual networks, subnets and security groups.", 25, 50),
            ("Monitoring Basics", "Cloud",
             "Understand logs, metrics and monitoring.", 20, 40),
            ("Python for Cloud", "Python",
             "Practice variables, loops and functions.", 25, 50),
            ("Shell Scripting Basics", "Linux",
             "Write a simple shell script.", 25, 50),
            ("Docker Introduction", "DevOps",
             "Understand containers and images.", 25, 50),
            ("CI/CD Fundamentals", "DevOps",
             "Learn the stages of a deployment pipeline.", 25, 50),
            ("Deploy a Sample App", "Project",
             "Plan a basic cloud application deployment.", 30, 60),
            ("Cloud Troubleshooting", "Debugging",
             "Identify common connectivity and permission issues.", 25, 50),
            ("Cloud Interview Practice", "Interview",
             "Answer five beginner cloud interview questions.", 20, 40),
            ("Cloud Roadmap Review", "Revision",
             "Review your progress and plan a mini cloud project.", 30, 60),
        ],

        "Full Stack Developer": [
            ("HTML Fundamentals", "HTML",
             "Create a basic webpage with semantic HTML.", 20, 40),
            ("CSS Fundamentals", "CSS",
             "Practice selectors, colors, spacing and typography.", 25, 50),
            ("Responsive Profile Card", "Frontend",
             "Build a responsive profile card.", 30, 60),
            ("JavaScript Variables", "JavaScript",
             "Practice variables, data types and operators.", 25, 50),
            ("Conditions and Loops", "JavaScript",
             "Solve basic problems using conditions and loops.", 25, 50),
            ("Functions and Arrays", "JavaScript",
             "Practice functions and array operations.", 25, 50),
            ("DOM Manipulation", "Frontend",
             "Change page content using JavaScript.", 25, 50),
            ("Form Validation", "Frontend",
             "Validate a simple form using JavaScript.", 30, 60),
            ("Git Essentials", "Git",
             "Practice add, commit, status and log.", 20, 40),
            ("HTTP and APIs", "Backend",
             "Understand requests, responses and REST APIs.", 25, 50),
            ("Python Fundamentals", "Python",
             "Practice variables, loops and functions.", 25, 50),
            ("Django Introduction", "Backend",
             "Understand URLs, views and templates.", 30, 60),
            ("Database Fundamentals", "SQL",
             "Practice tables, SELECT and WHERE queries.", 25, 50),
            ("CRUD Concepts", "Backend",
             "Understand create, read, update and delete.", 30, 60),
            ("Authentication Basics", "Backend",
             "Learn login, logout and protected pages.", 25, 50),
            ("React Fundamentals", "React",
             "Understand components, props and state.", 30, 60),
            ("API Integration", "Full Stack",
             "Plan how a frontend communicates with a backend.", 30, 60),
            ("Debugging Practice", "Debugging",
             "Find and fix common frontend or backend errors.", 25, 50),
            ("Mini Project Planning", "Project",
             "Define features and milestones for a small app.", 30, 60),
            ("Full Stack Review", "Interview",
             "Review your stack and explain your mini project.", 30, 60),
        ],

        "Data Analyst": [
            ("Data Analytics Overview", "Analytics",
             "Understand the data analysis workflow.", 20, 40),
            ("Excel Fundamentals", "Excel",
             "Practice sorting, filtering and basic formulas.", 25, 50),
            ("SQL SELECT and WHERE", "SQL",
             "Write basic SELECT and WHERE queries.", 25, 50),
            ("SQL Sorting and Filtering", "SQL",
             "Practice ORDER BY, LIMIT and filtering.", 25, 50),
            ("SQL Aggregations", "SQL",
             "Practice COUNT, SUM, AVG, MIN and MAX.", 25, 50),
            ("SQL GROUP BY", "SQL",
             "Summarize data using GROUP BY and HAVING.", 25, 50),
            ("SQL Joins", "SQL",
             "Understand INNER JOIN and LEFT JOIN.", 30, 60),
            ("Python Fundamentals", "Python",
             "Practice lists, dictionaries and loops.", 25, 50),
            ("Pandas Introduction", "Python",
             "Explore DataFrames and basic data operations.", 30, 60),
            ("Data Cleaning", "Analytics",
             "Identify missing values and duplicate rows.", 25, 50),
            ("Statistics Basics", "Statistics",
             "Review mean, median, mode and range.", 25, 50),
            ("Data Visualization", "Visualization",
             "Choose charts for different data questions.", 25, 50),
            ("Power BI Fundamentals", "Power BI",
             "Understand reports, visuals and dashboards.", 30, 60),
            ("Dashboard Design", "Visualization",
             "Sketch a clear dashboard layout.", 30, 60),
            ("Data Interpretation", "Analytics",
             "Analyze a small dataset and identify patterns.", 25, 50),
            ("Business Questions", "Analytics",
             "Turn a business problem into analysis questions.", 20, 40),
            ("Mini Analysis Project", "Project",
             "Plan a small end-to-end data analysis.", 30, 60),
            ("Insights and Recommendations", "Analytics",
             "Write three findings supported by data.", 25, 50),
            ("Analyst Interview Practice", "Interview",
             "Answer beginner SQL and analytics questions.", 25, 50),
            ("Data Roadmap Review", "Revision",
             "Review your skills and plan your next project.", 30, 60),
        ],

        "AI/ML Engineer": [
            ("Python Fundamentals", "Python",
             "Practice variables, conditions and loops.", 25, 50),
            ("Python Functions", "Python",
             "Write and call reusable functions.", 25, 50),
            ("Lists and Dictionaries", "Python",
             "Practice common data structures.", 25, 50),
            ("NumPy Basics", "Python",
             "Understand arrays and simple numerical operations.", 25, 50),
            ("Pandas Basics", "Data",
             "Load and inspect tabular data.", 30, 60),
            ("Data Cleaning", "Data",
             "Handle missing values and duplicates.", 25, 50),
            ("Statistics Basics", "Statistics",
             "Review mean, median, variance and standard deviation.", 25, 50),
            ("Probability Basics", "Mathematics",
             "Practice simple probability examples.", 25, 50),
            ("Machine Learning Overview", "Machine Learning",
             "Understand features, labels and model training.", 25, 50),
            ("Supervised Learning", "Machine Learning",
             "Compare classification and regression.", 25, 50),
            ("Unsupervised Learning", "Machine Learning",
             "Understand clustering and grouping.", 25, 50),
            ("Train and Test Data", "Machine Learning",
             "Learn why datasets are split for evaluation.", 25, 50),
            ("Model Evaluation", "Machine Learning",
             "Understand accuracy, precision and recall.", 30, 60),
            ("Linear Regression", "Machine Learning",
             "Explore the purpose of linear regression.", 30, 60),
            ("Classification Basics", "Machine Learning",
             "Understand a simple classification task.", 30, 60),
            ("Overfitting and Underfitting", "Machine Learning",
             "Learn how models can generalize poorly.", 25, 50),
            ("AI Ethics and Bias", "AI",
             "Review fairness, privacy and responsible AI.", 20, 40),
            ("Mini ML Project", "Project",
             "Plan a small dataset-based ML project.", 30, 60),
            ("ML Interview Practice", "Interview",
             "Answer beginner machine learning questions.", 25, 50),
            ("AI/ML Roadmap Review", "Revision",
             "Review concepts and plan your next experiment.", 30, 60),
        ],

        "Cybersecurity": [
            ("Cybersecurity Overview", "Security",
             "Understand threats, vulnerabilities and risk.", 20, 40),
            ("Linux Command Sprint", "Linux",
             "Practice basic Linux navigation commands.", 25, 50),
            ("Linux Permissions", "Linux",
             "Understand file permissions and access control.", 25, 50),
            ("Networking Fundamentals", "Networking",
             "Learn IP addresses, DNS, ports and protocols.", 25, 50),
            ("HTTP and HTTPS", "Networking",
             "Understand web requests and secure connections.", 20, 40),
            ("Common Cyber Threats", "Security",
             "Review phishing, malware and social engineering.", 25, 50),
            ("Password Security", "Security",
             "Learn password hygiene and multi-factor authentication.", 20, 40),
            ("Access Control Basics", "Security",
             "Understand authentication and authorization.", 25, 50),
            ("Web Security Basics", "Web Security",
             "Learn common web risks and safe coding principles.", 25, 50),
            ("OWASP Concepts", "Web Security",
             "Review common web application security risks.", 25, 50),
            ("Logs and Monitoring", "Security",
             "Understand the purpose of system and security logs.", 25, 50),
            ("Incident Response", "Security",
             "Learn the basic stages of incident response.", 25, 50),
            ("Cryptography Basics", "Cryptography",
             "Understand hashing, encryption and digital signatures.", 25, 50),
            ("Secure Configuration", "Security",
             "Review updates, permissions and secure defaults.", 25, 50),
            ("Threat Modelling", "Security",
             "Identify assets, threats and mitigations.", 30, 60),
            ("Security Awareness Quiz", "Quiz",
             "Test your knowledge of basic security concepts.", 15, 30),
            ("Defensive Security Lab Plan", "Lab",
             "Plan a safe local security learning exercise.", 30, 60),
            ("Vulnerability Report Practice", "Project",
             "Write a sample finding with impact and mitigation.", 30, 60),
            ("Security Interview Practice", "Interview",
             "Answer beginner networking and security questions.", 25, 50),
            ("Cybersecurity Roadmap Review", "Revision",
             "Review your progress and choose your next lab.", 30, 60),
        ],
        "Android Developer": [
            ("Android Development Overview", "Android", "Understand Android apps and the development workflow.", 20, 40),
            ("Kotlin Fundamentals", "Kotlin", "Learn variables, types and basic syntax.", 25, 50),
            ("Conditions and Loops", "Kotlin", "Practise conditions and loops.", 25, 50),
            ("Functions in Kotlin", "Kotlin", "Write reusable functions.", 25, 50),
            ("Classes and Objects", "Kotlin", "Understand classes, objects and constructors.", 25, 50),
            ("Android Studio Basics", "Android", "Explore projects and the Android Studio interface.", 20, 40),
            ("Activities and Lifecycle", "Android", "Understand Activities and their lifecycle.", 30, 60),
            ("Layouts and Views", "Android", "Build screens using layouts and views.", 25, 50),
            ("User Input and Events", "Android", "Handle basic input and click events.", 25, 50),
            ("Navigation Basics", "Android", "Understand navigation between screens.", 25, 50),
            ("RecyclerView Concepts", "Android", "Learn how lists are displayed efficiently.", 30, 60),
            ("Android Resources", "Android", "Use strings, colors and drawable resources.", 20, 40),
            ("App Permissions", "Android", "Understand Android runtime permissions.", 25, 50),
            ("Local Data Storage", "Android", "Compare preferences, files and databases.", 30, 60),
            ("API Integration Basics", "Android", "Understand how an app consumes a REST API.", 30, 60),
            ("App Debugging", "Debugging", "Practise reading errors and using Logcat.", 25, 50),
            ("Testing Fundamentals", "Android", "Understand basic app testing.", 25, 50),
            ("Build a Mini App", "Project", "Plan a small Android application.", 30, 60),
            ("Android Interview Practice", "Interview", "Review beginner Android development questions.", 25, 50),
            ("Android Roadmap Review", "Revision", "Review your skills and plan your next app.", 30, 60),
        ],
        "Penetration Testing": [
            ("Penetration Testing Overview", "Security", "Understand authorised security testing and its scope.", 20, 40),
            ("Linux Command Sprint", "Linux", "Practise navigation and file commands.", 25, 50),
            ("Networking Fundamentals", "Networking", "Learn IP addresses, DNS, ports and protocols.", 25, 50),
            ("HTTP and HTTPS", "Networking", "Understand requests, responses and TLS.", 25, 50),
            ("Reconnaissance Concepts", "Penetration Testing", "Learn passive reconnaissance and scope boundaries.", 25, 50),
            ("Scanning Fundamentals", "Networking", "Understand service discovery in an authorised lab.", 25, 50),
            ("Web Application Basics", "Web Security", "Review requests, sessions and forms.", 25, 50),
            ("Authentication and Sessions", "Web Security", "Understand login sessions and secure authentication.", 25, 50),
            ("Common Web Vulnerabilities", "Web Security", "Study common web risks and their prevention.", 30, 60),
            ("Input Validation", "Web Security", "Learn why untrusted input must be validated.", 25, 50),
            ("Access Control Testing", "Security", "Understand authorisation checks in a test application.", 25, 50),
            ("Password Security", "Security", "Review password hashing and multi-factor authentication.", 25, 50),
            ("Cryptography Basics", "Cryptography", "Understand hashing, encryption and TLS.", 25, 50),
            ("Security Tools Overview", "Penetration Testing", "Learn the purpose of common testing tools in a lab.", 25, 50),
            ("Vulnerability Verification", "Security", "Learn to verify findings safely and reproducibly.", 30, 60),
            ("Risk and Severity", "Security", "Assess impact, likelihood and severity.", 25, 50),
            ("Write a Finding Report", "Project", "Document evidence, impact and remediation.", 30, 60),
            ("Remediation and Retesting", "Security", "Understand fixes and controlled retesting.", 25, 50),
            ("Penetration Testing Interview", "Interview", "Review beginner security testing questions.", 25, 50),
            ("Security Roadmap Review", "Revision", "Review lab progress and plan the next safe exercise.", 30, 60),
        ],
    }

    # Support the existing profile value used in some screens.
    plan_career = "Cybersecurity" if career_goal == "Cybersecurity Analyst" else career_goal

    if plan_career not in plans:
        career_goal = "Not Sure Yet"
        plan_career = career_goal
        plans[career_goal] = [
            ("Discover Tech Careers", "Career",
             "Explore technology roles and their responsibilities.", 15, 30),
            ("Skill Discovery", "Skills",
             "Identify skills you want to develop.", 20, 40),
            ("Python Practice Sprint", "Python",
             "Practice beginner programming concepts.", 25, 50),
            ("SQL Query Challenge", "SQL",
             "Practice SELECT and WHERE queries.", 25, 50),
            ("Git Essentials", "Git",
             "Learn basic version control commands.", 20, 40),
            ("Linux Basics", "Linux",
             "Practice basic terminal commands.", 20, 40),
            ("Networking Fundamentals", "Networking",
             "Learn IP, DNS and HTTP concepts.", 25, 50),
            ("Communication Practice", "Communication",
             "Practice a short spoken self-introduction.", 15, 30),
            ("Problem Solving", "Programming",
             "Solve a beginner logic problem.", 25, 50),
            ("Database Basics", "SQL",
             "Understand tables, rows and columns.", 20, 40),
            ("Web Fundamentals", "Web",
             "Understand how websites work.", 25, 50),
            ("Cloud Computing Basics", "Cloud",
             "Learn the purpose of cloud computing.", 20, 40),
            ("Debugging Practice", "Debugging",
             "Find and explain a simple code error.", 25, 50),
            ("Technical Quiz", "Quiz",
             "Revise programming and database fundamentals.", 20, 40),
            ("Resume Skills Review", "Career",
             "List your current skills and learning goals.", 20, 40),
            ("Project Idea", "Project",
             "Choose a small project idea and define its purpose.", 25, 50),
            ("Project Planning", "Project",
             "Break your project into manageable tasks.", 25, 50),
            ("Interview Introduction", "Interview",
             "Prepare a concise personal introduction.", 20, 40),
            ("Mock Interview", "Interview",
             "Practice technical and HR questions.", 25, 50),
            ("Career Roadmap Review", "Revision",
             "Review your progress and plan the next steps.", 30, 60),
        ]

    plan = plans[plan_career]

    # -----------------------------------------------------
    # PROGRAM START DATE
    # Reuse the existing plan start date when available.
    # Old records are not deleted.
    # -----------------------------------------------------

    plan_titles = [item[0] for item in plan]

    existing_dates = MissionProgress.objects.filter(
        user=request.user,
        career_goal=career_goal,
        title__in=plan_titles,
        mission_date__isnull=False,
        day_number__gte=1,
        day_number__lte=20,
    ).values_list("mission_date", flat=True)

    start_date = min(existing_dates) if existing_dates else today

    elapsed_days = (today - start_date).days
    current_day = max(1, min(elapsed_days + 1, 20))

    # -----------------------------------------------------
    # CREATE/REUSE THE 20 SCHEDULED MISSION RECORDS
    # -----------------------------------------------------

    missions = []

    for index, item in enumerate(plan, start=1):
        title, category, description, duration, xp = item
        mission_date = start_date + timedelta(days=index - 1)

        record = MissionProgress.objects.filter(
            user=request.user,
            career_goal=career_goal,
            title=title,
            day_number=index,
            mission_date=mission_date,
        ).first()

        if record is None:
            record = MissionProgress.objects.create(
                user=request.user,
                career_goal=career_goal,
                title=title,
                category=category,
                skill=category,
                difficulty="Beginner",
                duration=duration,
                xp=xp,
                day_number=index,
                mission_date=mission_date,
            )

        missions.append({
            "title": record.title,
            "category": record.category,
            "skill": record.skill,
            "description": description,
            "duration": record.duration,
            "xp": record.xp,
            "difficulty": record.difficulty,
            "day_number": record.day_number,
            "mission_date": record.mission_date,
            "completed": record.completed,
            "is_today": record.mission_date == today,
            "record_id": record.id,
        })

    completed_count = MissionProgress.objects.filter(
        user=request.user,
        career_goal=career_goal,
        title__in=plan_titles,
        completed=True,
        day_number__gte=1,
        day_number__lte=20,
    ).count()

    guidance = career_guidance(request.user, profile)
    context = {
        "profile": profile,
        "student_name": get_student_name(request),
        "career_goal": career_goal,
        "skills": skills,
        "study_time": study_time,
        "missions": missions,
        "mission_count": len(missions),
        "total_xp": sum(mission["xp"] for mission in missions if mission["completed"]),
        "available_xp": sum(mission["xp"] for mission in missions),
        "mission_progress": round(completed_count / len(missions) * 100) if missions else 0,
        "completed_count": completed_count,
        "current_day": current_day,
        "today": today,
        "program_start_date": start_date,
        "guidance": guidance,
    }

    return render(request, "missions/missions.html", context)

# =========================================================
# ASSESSMENT
# =========================================================

def _render_assessment_form(request, attempt, question_count, is_roadmap_test=False, error=None):
    question_ids = [str(question_id) for question_id in attempt.question_ids]
    questions_by_id = {
        str(question.id): question
        for question in Question.objects.filter(id__in=question_ids)
    }
    questions = [
        questions_by_id[question_id]
        for question_id in question_ids
        if question_id in questions_by_id
    ]

    if len(questions) != len(question_ids):
        error = error or "Some questions are no longer available. A new question set was loaded."
        questions = list(
            Question.objects.filter(
                status="published", assessment_enabled=True
            ).order_by("?")[:question_count]
        )
        attempt.question_ids = [question.id for question in questions]
        attempt.total_questions = len(questions)
        attempt.save(update_fields=["question_ids", "total_questions"])

    if not attempt.question_ids:
        questions = list(
            Question.objects.filter(
                status="published", assessment_enabled=True
            ).order_by("?")[:question_count]
        )
        attempt.question_ids = [question.id for question in questions]
        attempt.total_questions = len(questions)
        attempt.save(update_fields=["question_ids", "total_questions"])

    return render(
        request,
        "assessment/assessment.html",
        {
            "questions": questions,
            "attempt": attempt,
            "error": error,
            "is_roadmap_test": is_roadmap_test,
        },
    )


def _assessment_flow(request, question_count=15, is_roadmap_test=False):
    completed_attempt = (
        AssessmentAttempt.objects
        .filter(user=request.user, is_completed=True)
        .order_by("-completed_at", "-id")
        .first()
    )

    if request.method == "POST" and request.POST.get("action") == "restart":
        if is_roadmap_test or completed_attempt is None:
            return redirect("assessment")

        with transaction.atomic():
            attempt = (
                AssessmentAttempt.objects.select_for_update()
                .filter(
                    user=request.user,
                    attempt_type="retest",
                    is_completed=False,
                    is_draft=True,
                    is_explicit_restart=True,
                )
                .order_by("-started_at", "-id")
                .first()
            )
            if attempt is None:
                AssessmentAttempt.objects.create(
                    user=request.user,
                    attempt_type="retest",
                    is_completed=False,
                    is_draft=True,
                    is_explicit_restart=True,
                    started_at=timezone.now(),
                )
        return redirect("assessment")

    if completed_attempt is not None and not is_roadmap_test and request.method == "GET":
        active_draft = (
            AssessmentAttempt.objects
            .filter(
                user=request.user,
                is_completed=False,
                is_draft=True,
                is_explicit_restart=True,
            )
            .order_by("-started_at", "-id")
            .first()
        )
        if active_draft is not None:
            return _render_assessment_form(request, active_draft, question_count)
        return render(
            request,
            "assessment/assessment.html",
            {"completed_attempt": completed_attempt, "questions": []},
        )

    if is_roadmap_test and completed_attempt is not None and request.method == "GET":
        return redirect("assessment")

    if request.method == "POST":
        attempt_id = request.POST.get("attempt_id", "").strip()
        if not attempt_id.isdecimal():
            messages.error(
                request,
                "This assessment session expired. Please open the current assessment and try again.",
            )
            return redirect("assessment")

        attempt = get_object_or_404(
            AssessmentAttempt, id=attempt_id, user=request.user
        )
        if attempt.is_completed:
            return redirect("assessment_result", attempt_id=attempt.id)
        if not attempt.is_draft:
            messages.error(
                request,
                "This incomplete historical attempt cannot be resumed. Please start the current assessment.",
            )
            return redirect("assessment")
        if completed_attempt is not None and not attempt.is_explicit_restart:
            messages.info(
                request,
                "Please use Restart Assessment to begin another attempt.",
            )
            return redirect("assessment")

        submitted_ids = request.POST.getlist("question_id")
        expected_ids = [str(question_id) for question_id in attempt.question_ids]
        questions_by_id = {
            str(question.id): question
            for question in Question.objects.filter(id__in=expected_ids)
        }
        answers_are_valid = all(
            request.POST.get(f"question_{question_id}", "").upper()
            in {"A", "B", "C", "D"}
            for question_id in expected_ids
        )
        valid_submission = (
            bool(expected_ids)
            and set(submitted_ids) == set(expected_ids)
            and len(set(submitted_ids)) == len(expected_ids)
            and len(questions_by_id) == len(expected_ids)
            and answers_are_valid
        )
        if not valid_submission:
            return _render_assessment_form(
                request,
                attempt,
                question_count,
                is_roadmap_test,
                "Please answer every assessment question and submit the assigned question set.",
            )

        with transaction.atomic():
            locked_attempt = AssessmentAttempt.objects.select_for_update().get(
                id=attempt.id, user=request.user
            )
            if locked_attempt.is_completed:
                return redirect(
                    "assessment_result", attempt_id=locked_attempt.id
                )

            correct_count = 0
            answer_rows = []
            for question_id in expected_ids:
                question = questions_by_id[question_id]
                selected_answer = request.POST[
                    f"question_{question_id}"
                ].upper()
                is_correct = selected_answer == question.correct_answer.upper()
                correct_count += int(is_correct)
                answer_rows.append(
                    AssessmentAnswer(
                        attempt=locked_attempt,
                        question=question,
                        selected_answer=selected_answer,
                        is_correct=is_correct,
                    )
                )

            AssessmentAnswer.objects.bulk_create(answer_rows)
            locked_attempt.total_questions = len(expected_ids)
            locked_attempt.correct_answers = correct_count
            locked_attempt.score = percentage(correct_count, len(expected_ids))
            locked_attempt.is_completed = True
            locked_attempt.is_draft = False
            locked_attempt.completed_at = timezone.now()
            locked_attempt.save(
                update_fields=[
                    "total_questions", "correct_answers", "score",
                    "is_completed", "completed_at",
                    "is_draft",
                ]
            )

        return redirect(
            "assessment_result", attempt_id=locked_attempt.id
        )

    draft = (
        AssessmentAttempt.objects
        .filter(user=request.user, is_completed=False, is_draft=True)
        .order_by("started_at", "id")
        .first()
    )
    if draft is None:
        attempt_type = "retest" if completed_attempt is not None else "baseline"
        draft = AssessmentAttempt.objects.create(
            user=request.user,
            attempt_type=attempt_type,
            is_completed=False,
            is_draft=True,
            started_at=timezone.now(),
        )

    return _render_assessment_form(
        request, draft, question_count, is_roadmap_test
    )


@onboarding_required
def assessment_view(request):
    return _assessment_flow(request)


@onboarding_required
def roadmap_test_view(request):
    return _assessment_flow(request, question_count=50, is_roadmap_test=True)


# =========================================================
# ASSESSMENT RESULT
# =========================================================

@onboarding_required
def assessment_result_view(
    request,
    attempt_id
):

    attempt = get_object_or_404(
        AssessmentAttempt,
        id=attempt_id,
        user=request.user,
        is_completed=True,
    )

    answers = list(
        AssessmentAnswer.objects
        .filter(attempt=attempt)
        .select_related("question")
    )

    # =====================================================
    # INCORRECT
    # =====================================================

    incorrect_answers = (
        attempt.total_questions
        - attempt.correct_answers
    )

    if incorrect_answers < 0:
        incorrect_answers = 0

    # =====================================================
    # SKILL DATA
    # =====================================================

    skill_data = {}

    for answer in answers:

        skill = answer.question.skill

        if skill not in skill_data:

            skill_data[skill] = {
                "total": 0,
                "correct": 0,
            }

        skill_data[skill]["total"] += 1

        if answer.is_correct:
            skill_data[skill]["correct"] += 1

    # =====================================================
    # PERFORMANCE
    # =====================================================

    performance = []

    try:
        skill_names = dict(
            Question.SKILL_CHOICES
        )
    except AttributeError:
        skill_names = {}

    for skill, data in skill_data.items():

        total = data["total"]
        correct = data["correct"]

        if total > 0:

            percentage = round(
                (correct / total) * 100
            )

        else:
            percentage = 0

        if percentage >= 80:
            status = "Strong"

        elif percentage >= 60:
            status = "Good"

        elif percentage >= 40:
            status = "Needs Practice"

        else:
            status = "Focus Area"

        performance.append({

            "skill": skill,

            "skill_name": skill_names.get(
                skill,
                skill
                .replace("_", " ")
                .title()
            ),

            "total": total,

            "correct": correct,

            "percentage": percentage,

            "status": status,
        })

    performance.sort(
        key=lambda item: item["percentage"],
        reverse=True
    )

    # =====================================================
    # STRONGEST / WEAKEST
    # =====================================================

    strongest_skill = None
    weakest_skill = None

    if performance:

        strongest_skill = performance[0]
        weakest_skill = performance[-1]

    # =====================================================
    # FOCUS AREAS
    # =====================================================

    focus_areas = [
        item
        for item in performance
        if item["percentage"] < 60
    ]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "attempt": attempt,

        "assessment_score": assessment_percentage(attempt),

        "answers": answers,

        "performance": performance,

        "strongest_skill": strongest_skill,

        "weakest_skill": weakest_skill,

        "focus_areas": focus_areas,

        "incorrect_answers": incorrect_answers,
    }

    return render(
        request,
        "assessment/result.html",
        context
    )


# =========================================================
# PRACTICE
# =========================================================

@onboarding_required
def practice_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    guidance = career_guidance(request.user, profile)
    career = normalize_career_goal(profile.career_goal)
    career_skill_filters = {
        "Cloud Engineer": ["aws", "linux", "networking", "docker", "git", "azure", "iam"],
        "Data Analyst": ["sql", "python", "statistics", "powerbi"],
        "Full Stack Developer": ["html_css", "javascript", "react", "django", "nodejs", "git", "sql"],
        "AI/ML Engineer": ["python", "dsa", "statistics"],
        "Android Developer": ["kotlin", "android", "java", "git"],
        "Cybersecurity Analyst": ["linux", "networking", "web_security", "security_fundamentals"],
        "Not Sure Yet": ["python", "sql", "git"],
    }
    selected_skills = career_skill_filters.get(career, [])
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "answer_question":
            question_id = request.POST.get("question_id", "")
            answer = request.POST.get("answer", "").upper()
            question = get_object_or_404(
                Question,
                id=question_id,
                status="published",
                skill__in=selected_skills,
            )
            if answer not in {"A", "B", "C", "D"}:
                messages.error(request, "Choose an answer before submitting.")
            else:
                PracticeQuestionAttempt.objects.create(
                    user=request.user,
                    question=question,
                    career_goal=career,
                    selected_answer=answer,
                    is_correct=answer == question.correct_answer,
                )
                messages.success(request, "Your practice answer was saved.")
            return redirect("practice")
        if action == "submit_lab":
            lab_id = request.POST.get("lab_id", "")
            lab_query = PracticeLab.objects.filter(status="published")
            lab_query = (
                lab_query.filter(roadmap__in=("Cybersecurity", "Cybersecurity Analyst"))
                if career == "Cybersecurity Analyst"
                else lab_query.filter(roadmap=career)
            )
            lab = get_object_or_404(lab_query, id=lab_id)
            response_text = request.POST.get("response", "").strip()
            completed = request.POST.get("completed") == "on"
            if not response_text:
                messages.error(request, "Add a short response before saving your lab work.")
            else:
                PracticeLabAttempt.objects.create(
                    user=request.user,
                    lab=lab,
                    response=response_text,
                    completed=completed,
                )
                messages.success(request, "Your lab work was saved.")
            return redirect("practice")

    question_skill_filter = request.GET.get("skill", "")
    question_difficulty_filter = request.GET.get("difficulty", "")
    question_query = Question.objects.filter(
        status="published", skill__in=selected_skills
    )
    if question_skill_filter in selected_skills:
        question_query = question_query.filter(skill=question_skill_filter)
    else:
        question_skill_filter = ""
    if question_difficulty_filter in dict(Question.DIFFICULTY_CHOICES):
        question_query = question_query.filter(difficulty=question_difficulty_filter)
    else:
        question_difficulty_filter = ""
    questions = question_query.order_by("skill", "difficulty", "-created_at")[:30]

    labs = PracticeLab.objects.filter(status="published")
    if career == "Cybersecurity Analyst":
        labs = labs.filter(roadmap__in=("Cybersecurity", "Cybersecurity Analyst"))
    elif career:
        labs = labs.filter(roadmap=career)
    else:
        labs = PracticeLab.objects.none()
    labs = labs.order_by("-created_at")
    labs = list(labs)
    lab_attempts = PracticeLabAttempt.objects.filter(
        user=request.user, lab__in=labs
    ).select_related("lab").order_by("-submitted_at", "-id")
    latest_lab_attempt = {}
    completed_lab_ids = set()
    for saved_attempt in lab_attempts:
        latest_lab_attempt.setdefault(saved_attempt.lab_id, saved_attempt)
        if saved_attempt.completed:
            completed_lab_ids.add(saved_attempt.lab_id)
    for lab in labs:
        lab.latest_attempt = latest_lab_attempt.get(lab.id)
    labs_by_type = {
        "lab": [lab for lab in labs if lab.content_type == "lab"],
        "challenge": [lab for lab in labs if lab.content_type == "challenge"],
    }
    practice_answers = PracticeQuestionAttempt.objects.filter(
        user=request.user,
        career_goal=career,
        question__in=questions,
    ).select_related("question").order_by("question_id", "-answered_at", "-id")
    latest_question_attempt = {}
    for saved_answer in practice_answers:
        latest_question_attempt.setdefault(saved_answer.question_id, saved_answer)
    for question in questions:
        question.latest_practice_attempt = latest_question_attempt.get(question.id)
    question_attempt_count = practice_answers.count()
    correct_practice_count = practice_answers.filter(is_correct=True).count()
    wrong_answers = practice_answers.filter(is_correct=False).select_related("question")

    return render(
        request,
        "learning/resource_page.html",
        {
            "page_title": "Practice & Skill Labs",
            "page_subtitle": (
                f"Career-focused practice for {career or 'your selected roadmap'}."
            ),
            "active_page": "practice",
            "career_goal": career,
            "guidance": guidance,
            "practice_labs": labs,
            "skill_labs": labs_by_type["lab"],
            "practice_challenges": labs_by_type["challenge"],
            "practice_questions": questions,
            "wrong_answers": wrong_answers,
            "practice_attempt_count": question_attempt_count,
            "practice_correct_count": correct_practice_count,
            "practice_accuracy": percentage(correct_practice_count, question_attempt_count),
            "completed_practice_labs": len(completed_lab_ids),
            "question_skill_filter": question_skill_filter,
            "question_difficulty_filter": question_difficulty_filter,
            "practice_skill_choices": [
                (value, label) for value, label in Question.SKILL_CHOICES
                if value in selected_skills
            ],
            "practice_difficulty_choices": Question.DIFFICULTY_CHOICES,
        },
    )


# =========================================================
# PRACTICE LABS
# =========================================================

@onboarding_required
def practice_labs_view(request):
    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user
    )

    # Active roadmap gets priority
    career_goal = normalize_career_goal(profile.career_goal)
    lab_roadmap = career_goal

    # Match old Cybersecurity value with Practice Lab value
    if lab_roadmap == "Cybersecurity Analyst":
        lab_roadmap = "Cybersecurity"

    # Show only labs belonging to the student's roadmap
    labs = PracticeLab.objects.filter(status="published")
    if career_goal == "Cybersecurity Analyst":
        labs = labs.filter(roadmap__in=("Cybersecurity", "Cybersecurity Analyst"))
    else:
        labs = labs.filter(roadmap=lab_roadmap)
    labs = labs.order_by("-created_at")

    context = {
        "labs": labs,
        "career_goal": career_goal,
        "active_page": "practice_labs",
        "student_name": get_student_name(request),
    }

    return render(
        request,
        "practice_labs/practice_labs.html",
        context
    )


# =========================================================
# PROJECTS
# =========================================================

@onboarding_required
def projects_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        selected = request.POST.get("career", "")
        if selected and not save_career_selection(profile, selected):
            messages.error(request, "Choose one of the available career paths.")
        difficulty = request.POST.get("difficulty", "All")
        if difficulty not in {"All", "Beginner", "Intermediate", "Advanced"}:
            difficulty = "All"
        return redirect(
            f"{reverse('projects')}?difficulty={difficulty}"
        )
    if "career" in request.GET:
        # Accept links from the previous GET-based filter while the current
        # form uses POST for account-level career changes.
        save_career_selection(profile, request.GET.get("career"))
        query = request.GET.copy()
        query.pop("career", None)
        return redirect(f"{reverse('projects')}?{query.urlencode()}" if query else "projects")

    career = normalize_career_goal(profile.career_goal)
    guidance = career_guidance(request.user, profile)
    all_projects = projects_for_career(career)
    difficulty = request.GET.get("difficulty", "All")
    if difficulty not in {"All", "Beginner", "Intermediate", "Advanced"}:
        difficulty = "All"
    visible_projects = (
        all_projects if difficulty == "All"
        else [project for project in all_projects if project["level"] == difficulty]
    )
    return render(
        request,
        "learning/resource_page.html",
        {
            "page_title": "Projects",
            "page_subtitle": (
                f"Ten roadmap-aligned project briefs for {career or 'your selected career'}."
            ),
            "active_page": "projects",
            "career_goal": career,
            "career_choices": CAREER_CHOICES,
            "difficulty_choices": ["All", "Beginner", "Intermediate", "Advanced"],
            "difficulty_filter": difficulty,
            "project_cards": visible_projects,
            "security_scope_note": (
                "Only test systems you own or have explicit written authorization to assess."
                if career == "Cybersecurity Analyst" else ""
            ),
            "project_counts": {
                level: sum(project["level"] == level for project in all_projects)
                for level in ("Beginner", "Intermediate", "Advanced")
            },
            "guidance": guidance,
        },
    )


# =========================================================
# JOBS
# =========================================================

@onboarding_required
def jobs_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    career = normalize_career_goal(profile.career_goal)
    guidance = career_guidance(request.user, profile)
    roles = job_roles_for_career(career)

    return render(
        request,
        "learning/resource_page.html",
        {
            "page_title": "Jobs",
            "page_subtitle": (
                "Career role suggestions, not verified live vacancies."
            ),
            "active_page": "jobs",
            "career_goal": career,
            "job_roles": roles,
            "guidance": guidance,
            "roles_are_live_listings": False,
        },
    )


# =========================================================
# INTERVIEWS
# =========================================================

@onboarding_required
def interviews_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    career = normalize_career_goal(profile.career_goal)
    catalog = interviews_for_career(career)
    level_choices = ["Beginner", "Intermediate", "Advanced"]
    level = request.GET.get("level", "Beginner").title()
    if level not in level_choices:
        level = "Beginner"

    if request.method == "POST":
        action = request.POST.get("action")
        requested_level = request.POST.get("level", "Beginner").title()
        if requested_level not in level_choices:
            messages.error(request, "Choose a valid interview level.")
            return redirect("interviews")

        if action == "save_answer":
            question_key = request.POST.get("question_key", "")
            question = next(
                (
                    item
                    for question_set in catalog.values()
                    for item in question_set
                    if item["key"] == question_key
                    and item["level"] == requested_level
                ),
                None,
            )
            answer = request.POST.get("answer", "").strip()
            feedback = request.POST.get("feedback", "").strip()
            rating_raw = request.POST.get("self_rating", "").strip()
            rating_is_valid = not rating_raw or rating_raw in {"1", "2", "3", "4", "5"}
            try:
                rating = int(rating_raw) if rating_raw else None
            except ValueError:
                rating = None
            if (
                not question
                or not answer
                or len(answer) > 10000
                or len(feedback) > 2000
                or not rating_is_valid
            ):
                messages.error(request, "Check the answer, rating, and feedback fields, then try again.")
            else:
                InterviewAnswer.objects.update_or_create(
                    user=request.user,
                    career_goal=career,
                    question_key=question["key"],
                    defaults={
                        "level": requested_level,
                        "question_type": question["type"],
                        "answer": answer,
                        "self_rating": rating,
                        "feedback": feedback,
                    },
                )
                messages.success(request, "Your answer has been saved.")
            return redirect(f"{reverse('interviews')}?level={requested_level}")

        if action == "complete_day":
            try:
                day_number = int(request.POST.get("day_number", ""))
            except ValueError:
                day_number = 0
            if day_number not in range(1, 31):
                messages.error(request, "Choose a valid practice day.")
            else:
                completed = request.POST.get("completed") == "on"
                progress, _ = InterviewDayProgress.objects.get_or_create(
                    user=request.user,
                    career_goal=career,
                    day_number=day_number,
                    defaults={
                        "completed": completed,
                        "completed_at": timezone.now() if completed else None,
                    },
                )
                if progress.completed != completed:
                    progress.completed = completed
                    progress.completed_at = timezone.now() if completed else None
                    progress.save(update_fields=["completed", "completed_at"])
                messages.success(request, "Day progress saved.")
            return redirect(f"{reverse('interviews')}?level={requested_level}#day-plan")

        messages.error(request, "That interview action is not available.")
        return redirect("interviews")

    saved_answers = {
        answer.question_key: answer
        for answer in InterviewAnswer.objects.filter(
            user=request.user, career_goal=career
        )
    }
    current_questions = catalog.get(level, [])
    for question in current_questions:
        question["saved"] = saved_answers.get(question["key"])

    saved_days = {
        item.day_number: item
        for item in InterviewDayProgress.objects.filter(
            user=request.user, career_goal=career
        )
    }
    topics = DAY_TOPICS.get(career, [])
    day_plan = []
    if topics:
        for day_number in range(1, 31):
            day_level = level_choices[(day_number - 1) // 10]
            day_topic = topics[(day_number - 1) % 10]
            day_questions = catalog[day_level]
            day_plan.append({
                "number": day_number,
                "title": f"Day {day_number}: {day_topic}",
                "level": day_level,
                "topic": day_topic,
                "technical_questions": [q for q in day_questions if q["type"] == "technical"],
                "behavioral_question": next(q for q in day_questions if q["type"] == "behavioral"),
                "speaking_exercise": f"Explain {day_topic} aloud for two minutes, then give one example from a project or lab.",
                "progress": saved_days.get(day_number),
            })
    completed_days = sum(
        item.completed for item in saved_days.values()
    )
    guidance = career_guidance(request.user, profile)

    return render(
        request,
        "learning/resource_page.html",
        {
            "page_title": "Interview Prep",
            "page_subtitle": f"Technical and behavioural practice for {career or 'your selected roadmap'}.",
            "active_page": "interviews",
            "career_goal": career,
            "interview_levels": level_choices,
            "selected_level": level,
            "interview_questions": current_questions,
            "day_plan": day_plan,
            "completed_days": completed_days,
            "guidance": guidance,
        },
    )


# =========================================================
# PROGRESS
# =========================================================

@onboarding_required
def progress_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    career = normalize_career_goal(profile.career_goal)
    attempts = list(
        AssessmentAttempt.objects
        .filter(user=request.user, is_completed=True)
        .order_by("-completed_at", "-id")
    )

    latest = attempts[0] if attempts else None

    average_score = (
        round(
            sum(attempt.score for attempt in attempts)
            / len(attempts)
        )
        if attempts
        else None
    )

    best_score = max(
        (attempt.score for attempt in attempts),
        default=None,
    )

    readiness_score = assessment_percentage(latest)

    mission_qs = MissionProgress.objects.filter(
        user=request.user, career_goal=career, day_number__gte=1, day_number__lte=20
    )
    mission_metrics = summarize_missions(
        mission_qs.values("day_number", "completed", "xp")
    )
    mission_total = mission_metrics["mission_count"]
    missions_completed = mission_metrics["missions_completed"]
    earned_xp = mission_qs.filter(completed=True).aggregate(total=Sum("xp"))["total"] or 0
    interview_answer_count = InterviewAnswer.objects.filter(
        user=request.user, career_goal=career
    ).count()
    interview_days_completed = InterviewDayProgress.objects.filter(
        user=request.user, career_goal=career, completed=True
    ).count()
    practice_question_attempts = PracticeQuestionAttempt.objects.filter(
        user=request.user, career_goal=career
    )
    practice_questions_answered = practice_question_attempts.count()
    practice_questions_correct = practice_question_attempts.filter(is_correct=True).count()
    career_lab_roadmaps = (
        ("Cybersecurity", "Cybersecurity Analyst")
        if career == "Cybersecurity Analyst" else (career,)
    )
    practice_labs_completed = PracticeLabAttempt.objects.filter(
        user=request.user,
        lab__roadmap__in=career_lab_roadmaps,
        completed=True,
    ).values("lab_id").distinct().count()
    guidance = career_guidance(request.user, profile)

    return render(
        request,
        "learning/progress.html",
        {
            "attempts": attempts,
            "latest_attempt": latest,
            "average_score": average_score,
            "best_score": best_score,
            "readiness_score": readiness_score,
            "career_goal": career,
            "career_progress": percentage(missions_completed, 20),
            "missions_completed": missions_completed,
            "mission_total": mission_total,
            "earned_xp": earned_xp,
            "interview_answer_count": interview_answer_count,
            "interview_days_completed": interview_days_completed,
            "practice_questions_answered": practice_questions_answered,
            "practice_questions_correct": practice_questions_correct,
            "practice_accuracy": percentage(practice_questions_correct, practice_questions_answered),
            "practice_labs_completed": practice_labs_completed,
            "guidance": guidance,
        },
    )


# =========================================================
# MISSION DETAIL
# =========================================================
# =========================================================


# =========================================================
# MISSION DETAIL — PERSISTENT COMPLETION
# =========================================================

@onboarding_required
def mission_detail_view(request):
    mission_title = request.GET.get("mission", "").strip()
    record_id = request.GET.get("record_id", "").strip()

    if not mission_title:
        return redirect("missions")

    record = None
    if record_id.isdigit():
        record = MissionProgress.objects.filter(
            id=int(record_id), user=request.user, title=mission_title
        ).first()

    if record is None:
        record = MissionProgress.objects.filter(
            user=request.user,
            career_goal=normalize_career_goal(
                request.user.student_profile.career_goal
            ),
            title=mission_title,
        ).order_by("mission_date", "id").first()

    if record is None:
        return redirect("missions")

    mission_data = {
        "Discover Tech Careers": {
            "objective": "Explore technology careers and identify suitable roles.",
            "steps": ["Explore Cloud Engineering", "Explore Full Stack Development",
                      "Explore Data Analytics", "Explore AI/ML", "Explore Cybersecurity"],
            "challenge": "Choose two careers you want to explore further.",
        },
        "Skill Discovery": {
            "objective": "Identify skills that match your career direction.",
            "steps": ["Review your current skills", "Choose relevant career skills",
                      "Identify your strongest skill", "Select one skill to improve"],
            "challenge": "Write down three skills you want to practise.",
        },
        "Git Essentials": {
            "objective": "Understand how Git tracks project changes.",
            "steps": ["Understand Git", "Learn git init", "Learn git add",
                      "Learn git commit", "Learn git status", "Learn git log"],
            "challenge": "Create a repository and make your first commit.",
        },
        "Python Practice Sprint": {
            "objective": "Practise variables, conditions and loops.",
            "steps": ["Review variables", "Practise if-else", "Practise for loops",
                      "Practise while loops", "Solve a small Python problem"],
            "challenge": "Write a program that checks whether a number is even or odd.",
        },
        "SQL Query Challenge": {
            "objective": "Practise SQL queries for real-world data.",
            "steps": ["Review SELECT", "Practise WHERE", "Practise ORDER BY",
                      "Practise GROUP BY", "Practise aggregate functions"],
            "challenge": "Write a SQL query to find employees earning more than 50000.",
        },
        "Linux Command Sprint": {
            "objective": "Build confidence using the Linux terminal.",
            "steps": ["Learn pwd", "Learn ls", "Learn cd", "Learn mkdir",
                      "Learn touch", "Learn file permissions"],
            "challenge": "Create a folder and a file using terminal commands.",
        },
        "AWS Fundamentals": {
            "objective": "Understand the purpose of major AWS services.",
            "steps": ["Understand cloud computing", "Learn what AWS is",
                      "Understand EC2", "Understand S3", "Understand IAM"],
            "challenge": "Explain what EC2 and S3 are used for.",
        },
    }

    detail = mission_data.get(mission_title, {
        "objective": "Build practical knowledge related to your personalised roadmap.",
        "steps": ["Read the mission description", "Review the concepts",
                  "Practise what you learned", "Complete the quiz"],
        "challenge": "Apply what you learned in a small practical task.",
    })

    mission = {
        "category": record.category,
        "duration": record.duration,
        "xp": record.xp,
        "difficulty": record.difficulty or "Beginner",
        "description": (
            f"Complete this {record.category or 'technology'} mission "
            "to strengthen your skills."
        ),
        "objective": detail["objective"],
        "steps": detail["steps"],
        "challenge": detail["challenge"],
    }

    # Choose quiz questions using the mission title and category.
    quiz_topic_text = f"{record.title} {record.category or ''} {record.skill or ''}".lower()

    cloud_questions = [
        ("Which AWS service provides resizable virtual servers?",
         ["Amazon EC2", "Amazon S3", "Amazon Route 53", "AWS IAM"], 0,
         "EC2 provides virtual compute instances."),
        ("Which AWS service stores objects in buckets?",
         ["Amazon S3", "Amazon EC2", "Amazon VPC", "AWS IAM"], 0,
         "S3 is an object storage service."),
        ("What is AWS IAM used for?",
         ["Managing identities and permissions", "Hosting virtual machines",
          "Storing objects", "Creating DNS records"], 0,
         "IAM manages users, roles, policies and access permissions."),
        ("What does a VPC provide?",
         ["An isolated virtual network", "A programming language",
          "A file format", "A database query"], 0,
         "A VPC provides networking isolation within AWS."),
        ("What is a subnet?",
         ["A subdivision of an IP network", "A storage bucket",
          "A virtual machine image", "An IAM password"], 0,
         "Subnets divide a network address range."),
        ("Which service can collect AWS metrics and logs?",
         ["Amazon CloudWatch", "Amazon S3 only", "AWS IAM", "Amazon Route 53"], 0,
         "CloudWatch supports monitoring with metrics, logs and alarms."),
        ("What is the purpose of a security group?",
         ["Control traffic to supported resources", "Store source code",
          "Create database tables", "Compile Python"], 0,
         "Security groups act as virtual firewalls for supported resources."),
        ("Which AWS service provides managed relational databases?",
         ["Amazon RDS", "Amazon S3", "Amazon VPC", "AWS IAM"], 0,
         "RDS manages supported relational database engines."),
        ("What is cloud elasticity?",
         ["Adjusting resources to demand", "Encrypting every file manually",
          "Removing all networks", "Writing HTML"], 0,
         "Elasticity allows capacity to scale with demand."),
        ("What is the principle of least privilege?",
         ["Grant only the access needed", "Give everyone administrator access",
          "Share all passwords", "Disable all authentication"], 0,
         "Least privilege reduces unnecessary permissions."),
    ]

    android_questions = [
        ("Which language is officially supported for Android development?",
         ["Kotlin", "SQL", "CSS", "Bash"], 0,
         "Kotlin is a first-class language for Android development."),
        ("What is an Android Activity commonly used for?",
         ["Representing a user-facing screen", "Storing SQL backups",
          "Managing cloud billing", "Compiling CSS"], 0,
         "An Activity is an application component associated with user interaction."),
        ("What is Android Studio?",
         ["An Android development IDE", "A database engine",
          "A cloud storage bucket", "A Linux command"], 0,
         "Android Studio is the official IDE for Android development."),
        ("What is the purpose of an XML layout in traditional Android views?",
         ["Describe screen UI structure", "Store user passwords in plaintext",
          "Manage DNS", "Compile Kotlin by itself"], 0,
         "Layouts can describe UI elements and their arrangement."),
        ("Which file declares many Android app components and permissions?",
         ["AndroidManifest.xml", "README.txt", "index.css", "requirements.txt"], 0,
         "The manifest declares app components and other app information."),
        ("What is an Intent used for?",
         ["Requesting an action or launching a component", "Styling text",
          "Creating an SQL index", "Compressing images only"], 0,
         "Intents can request actions such as opening another Activity."),
        ("What is Logcat useful for?",
         ["Viewing app and system logs", "Designing database schemas",
          "Creating cloud accounts", "Writing CSS selectors"], 0,
         "Logcat helps developers inspect logs and diagnose issues."),
        ("What is RecyclerView commonly used for?",
         ["Displaying efficient scrollable lists", "Managing app permissions",
          "Encrypting network packets", "Compiling Kotlin"], 0,
         "RecyclerView efficiently displays collections of items."),
        ("Why should Android runtime permissions be checked when required?",
         ["To obtain user-authorised access to protected resources",
          "To increase screen resolution", "To create a Git branch",
          "To remove app lifecycle callbacks"], 0,
         "Dangerous permissions may require approval at runtime."),
        ("What is an Android Activity lifecycle?",
         ["The sequence of states an Activity passes through",
          "A database backup schedule", "A CSS layout rule",
          "A cloud billing method"], 0,
         "Lifecycle callbacks represent changes in an Activity's state."),
    ]

    pentest_questions = [
        ("What must be established before a penetration test?",
         ["Authorisation and scope", "A public target without permission",
          "A shared administrator password", "A plan to delete evidence"], 0,
         "Testing must be authorised and stay within the agreed scope."),
        ("What is passive reconnaissance?",
         ["Collecting information without directly probing the target",
          "Changing target files", "Disabling a firewall",
          "Deleting server logs"], 0,
         "Passive reconnaissance uses sources that do not directly interact with the target."),
        ("What does DNS primarily do?",
         ["Maps domain names to resource records such as IP addresses",
          "Encrypts every file", "Runs Android apps", "Stores SQL tables"], 0,
         "DNS resolves names using records such as A and AAAA."),
        ("What does HTTPS protect?",
         ["Data in transit using TLS", "All devices from every attack",
          "A database from all errors", "Passwords stored in plaintext"], 0,
         "HTTPS protects communication in transit but does not guarantee a site is safe."),
        ("What is a vulnerability?",
         ["A weakness that could be exploited", "A confirmed business requirement",
          "A software update", "A network cable"], 0,
         "A vulnerability is a weakness that can affect security."),
        ("What is the purpose of input validation?",
         ["Check data against expected rules", "Give every user admin rights",
          "Disable authentication", "Hide all error messages from developers"], 0,
         "Validation checks whether input meets expected constraints."),
        ("What is the purpose of an access-control test?",
         ["Verify users can access only permitted resources",
          "Measure screen brightness", "Compress web images",
          "Create a new programming language"], 0,
         "Access-control testing checks whether permissions are enforced correctly."),
        ("Which practice helps protect stored passwords?",
         ["Salted password hashing with a suitable password-hashing algorithm",
          "Plaintext storage", "Sharing passwords in logs",
          "Using the same password for every account"], 0,
         "Passwords should be stored using suitable password-hashing algorithms."),
        ("What should a useful vulnerability report include?",
         ["Evidence, impact and remediation", "Only the tester's name",
          "Unverified claims only", "Users' private passwords"], 0,
         "A report should make findings reproducible and explain how to fix them."),
        ("What is retesting after remediation?",
         ["Checking whether the fix addresses the finding",
          "Publishing credentials", "Deleting the scope",
          "Running unrelated tests on public systems"], 0,
         "Retesting verifies the fix in the authorised environment."),
    ]

    data_questions = [
        ("Which SQL command retrieves rows from a table?",
         ["SELECT", "DELETE", "DROP", "UPDATE"], 0,
         "SELECT retrieves data from tables or other query sources."),
        ("Which SQL clause filters rows?",
         ["WHERE", "ORDER BY", "GROUP BY", "CREATE"], 0,
         "WHERE filters rows according to a condition."),
        ("Which SQL clause sorts query results?",
         ["ORDER BY", "WHERE", "INSERT", "ALTER"], 0,
         "ORDER BY sorts the result set."),
        ("Which function counts rows?",
         ["COUNT()", "TOTALROWS()", "NUMBEROF()", "ROWSUM()"], 0,
         "COUNT() returns the number of rows or non-NULL values, depending on its argument."),
        ("What does GROUP BY do?",
         ["Groups rows for aggregation", "Deletes duplicate tables",
          "Sorts files on disk", "Creates a Python function"], 0,
         "GROUP BY groups rows that share values for aggregate calculations."),
        ("What does an INNER JOIN return?",
         ["Rows matching the join condition in both sources",
          "Every possible row regardless of matching",
          "Only rows from the left table", "Only column names"], 0,
         "INNER JOIN returns rows that satisfy the join condition."),
        ("In Pandas, what is a DataFrame?",
         ["A two-dimensional labelled data structure",
          "A cloud virtual machine", "A CSS selector",
          "A Linux permission"], 0,
         "A DataFrame stores tabular data with labelled rows and columns."),
        ("What is a missing value in a dataset?",
         ["An absent or unavailable value", "Always a value of zero",
          "Always a duplicate row", "A chart title"], 0,
         "Missing values represent data that is absent or unavailable."),
        ("Which measure is the middle value of sorted observations?",
         ["Median", "Mean", "Range", "Variance"], 0,
         "The median is the middle observation after sorting."),
        ("Which chart is often suitable for comparing values across categories?",
         ["Bar chart", "Network cable diagram", "Password list",
          "Source-code comment"], 0,
         "Bar charts are commonly used to compare category values."),
    ]

    linux_questions = [
        ("Which command prints the current working directory?",
         ["pwd", "cd", "mkdir", "touch"], 0,
         "pwd prints the current working directory."),
        ("Which command lists directory contents?",
         ["ls", "pwd", "whoami", "clear"], 0,
         "ls lists files and directories."),
        ("Which command creates a directory?",
         ["mkdir", "rmdir", "pwd", "cat"], 0,
         "mkdir creates a directory."),
        ("Which command changes the current directory?",
         ["cd", "ls", "touch", "echo"], 0,
         "cd changes the shell's current directory."),
        ("What does chmod change?",
         ["File permissions", "DNS records", "Python versions",
          "Database rows"], 0,
         "chmod changes file permission bits."),
        ("What does grep commonly do?",
         ["Searches text for matching patterns", "Creates a user account",
          "Changes file ownership", "Starts a web browser"], 0,
         "grep searches input for lines matching a pattern."),
        ("Which command displays a file's text in the terminal?",
         ["cat", "mkdir", "chmod", "cd"], 0,
         "cat can display file contents."),
        ("What is a shell script?",
         ["A file containing shell commands", "A database table",
          "A cloud storage class", "An Android layout"], 0,
         "A shell script automates commands for a shell."),
        ("What does git commit do?",
         ["Records staged changes in repository history",
          "Uploads every file automatically", "Deletes a repository",
          "Creates a Linux user"], 0,
         "A commit records a snapshot of staged changes."),
        ("What is the purpose of git status?",
         ["Shows the working tree and staging state",
          "Starts a cloud server", "Changes DNS records",
          "Executes an SQL query"], 0,
         "git status summarises changes and repository state."),
    ]

    web_questions = [
        ("What does HTML primarily define?",
         ["Webpage structure", "Database permissions", "Cloud billing",
          "Network routing"], 0,
         "HTML describes the structure and content of web pages."),
        ("What is CSS used for?",
         ["Styling webpage presentation", "Querying SQL tables",
          "Managing Linux users", "Creating AWS IAM roles"], 0,
         "CSS controls presentation such as layout, colour and typography."),
        ("Which language commonly adds interactivity to webpages?",
         ["JavaScript", "SQL", "Bash only", "XML only"], 0,
         "JavaScript can implement interactive browser behaviour."),
        ("What is a REST API used for?",
         ["Allowing software systems to communicate over HTTP",
          "Styling a webpage", "Changing file permissions",
          "Replacing every database"], 0,
         "APIs define how software components exchange data and operations."),
        ("What does HTTP status 404 usually mean?",
         ["Resource not found", "Request succeeded",
          "Server permanently stopped", "User authenticated successfully"], 0,
         "404 indicates that the requested resource was not found."),
        ("What is Django?",
         ["A Python web framework", "A SQL aggregate function",
          "A Linux filesystem", "An Android permission"], 0,
         "Django provides tools for building web applications with Python."),
        ("What is a React component?",
         ["A reusable UI building block", "A DNS record",
          "A database password", "A Linux command"], 0,
         "Components help organise user interfaces into reusable pieces."),
        ("What does CRUD stand for?",
         ["Create, Read, Update, Delete", "Copy, Run, Upload, Download",
          "Compile, Restart, Use, Deploy", "Connect, Route, Use, Debug"], 0,
         "CRUD describes four common data operations."),
        ("Why validate form input on the server?",
         ["Client-side checks can be bypassed", "Browsers cannot display text",
          "It removes the need for authentication", "It prevents all outages"], 0,
         "Server-side validation is essential because client-side checks can be bypassed."),
        ("What is Git mainly used for?",
         ["Version control", "Photo editing", "DNS resolution",
          "Database hosting"], 0,
         "Git tracks changes to files over time."),
    ]

    python_questions = [
        ("Which Python keyword defines a function?",
         ["def", "func", "function", "method"], 0,
         "Python uses def to define a function."),
        ("Which type is used for an ordered, mutable collection?",
         ["list", "tuple", "str", "bool"], 0,
         "Lists are ordered and mutable."),
        ("What does len([2, 4, 6]) return?",
         ["3", "2", "6", "12"], 0,
         "The list contains three elements."),
        ("Which operator tests equality?",
         ["==", "=", "!=", ":="], 0,
         "== compares two values for equality."),
        ("What does a for loop do?",
         ["Iterates over items in an iterable", "Always creates a class",
          "Deletes a Python environment", "Connects to AWS automatically"], 0,
         "A for loop iterates over items in an iterable."),
        ("Which structure stores key-value pairs?",
         ["dict", "list only", "int", "bool"], 0,
         "A dictionary maps keys to values."),
        ("What does an import statement do?",
         ["Makes a module or its names available",
          "Deletes a module from disk", "Creates an SQL table",
          "Changes file permissions"], 0,
         "import loads a module namespace for use."),
        ("What is an exception?",
         ["An error condition handled during execution",
          "A CSS property", "An AWS storage bucket",
          "A database column type only"], 0,
         "Exceptions signal errors or unusual conditions during execution."),
        ("What does return do inside a function?",
         ["Sends a result back to the caller", "Prints every variable",
          "Always repeats the loop", "Installs a package"], 0,
         "return exits the function and optionally provides a value."),
        ("What is debugging?",
         ["Finding and fixing software defects", "Deleting every test",
          "Changing all variable names", "Disabling version control"], 0,
         "Debugging helps locate and correct defects."),
    ]

    generic_questions = [
        ("Which language is commonly used for AI and automation?",
         ["Python", "HTML", "CSS", "PNG"], 0,
         "Python has libraries for automation, data work and AI."),
        ("What is SQL mainly used for?",
         ["Querying and managing relational data",
          "Styling webpages", "Editing photographs", "Managing screen brightness"], 0,
         "SQL is used to query and manage relational databases."),
        ("What is Git mainly used for?",
         ["Version control", "Sending email", "Creating images",
          "Managing monitor settings"], 0,
         "Git tracks changes to project files."),
        ("Which command shows the current Linux directory?",
         ["pwd", "mkdir", "touch", "clear"], 0,
         "pwd prints the current working directory."),
        ("What is cloud computing?",
         ["Using computing services over a network",
          "Only saving files on USB", "Writing without a computer",
          "A type of keyboard"], 0,
         "Cloud services provide computing resources over a network."),
        ("What does debugging mean?",
         ["Finding and fixing errors", "Deleting every file",
          "Changing a password", "Installing a font"], 0,
         "Debugging means identifying and correcting defects."),
        ("What does an operating system do?",
         ["Manages hardware and software resources",
          "Only styles webpages", "Only stores spreadsheets",
          "Only creates presentations"], 0,
         "An operating system manages system resources and provides common services."),
        ("What is authentication?",
         ["Verifying identity", "Choosing a chart colour",
          "Sorting a spreadsheet", "Compressing a folder"], 0,
         "Authentication verifies who or what is requesting access."),
        ("What is an API?",
         ["An interface for software communication",
          "A type of keyboard", "A Linux file permission",
          "A chart axis"], 0,
         "An API defines how software components interact."),
        ("Why test software?",
         ["To find defects and verify expected behaviour",
          "To guarantee no future bugs ever", "To remove all documentation",
          "To disable user feedback"], 0,
         "Testing checks whether software behaves as expected."),
    ]

    if any(k in quiz_topic_text for k in (
        "cloud", "aws", "ec2", "s3", "iam", "vpc", "deploy",
        "monitoring", "architecture", "cicd", "devops"
    )):
        raw_questions = cloud_questions
    elif any(k in quiz_topic_text for k in (
        "android", "kotlin", "activity", "recyclerview", "mobile app"
    )):
        raw_questions = android_questions
    elif any(k in quiz_topic_text for k in (
        "penetration", "cybersecurity", "security", "vulnerability",
        "cryptography", "owasp", "threat", "incident response",
        "access control", "password"
    )):
        raw_questions = pentest_questions
    elif any(k in quiz_topic_text for k in (
        "data analyst", "analytics", "sql", "pandas", "power bi",
        "excel", "statistics", "visualization", "dashboard", "data cleaning"
    )):
        raw_questions = data_questions
    elif any(k in quiz_topic_text for k in (
        "linux", "shell", "git", "networking", "dns", "http", "ip address"
    )):
        raw_questions = linux_questions
    elif any(k in quiz_topic_text for k in (
        "html", "css", "javascript", "frontend", "full stack", "django",
        "react", "api", "backend", "crud", "web"
    )):
        raw_questions = web_questions
    elif any(k in quiz_topic_text for k in (
        "python", "machine learning", "ai/ml", "numpy", "supervised",
        "unsupervised", "model evaluation", "probability"
    )):
        raw_questions = python_questions
    else:
        raw_questions = generic_questions

    questions = [
        {
            "id": f"q{i}",
            "text": item[0],
            "options": [
                {"value": str(j), "text": option}
                for j, option in enumerate(item[1])
            ],
            "correct": item[2],
            "explanation": item[3],
        }
        for i, item in enumerate(raw_questions, start=1)
    ]

    result = None
    selected_answers = {}
    latest_attempts = MissionQuizAttempt.objects.filter(
        user=request.user, mission=record
    )[:5]

    if request.method == "POST" and not record.completed:
        for q in questions:
            value = request.POST.get(q["id"], "")
            if value in ("0", "1", "2", "3"):
                selected_answers[q["id"]] = value

        if len(selected_answers) != 10:
            result = {
                "error": "Please answer all 10 questions before submitting."
            }
        else:
            score = sum(
                1 for q in questions
                if selected_answers[q["id"]] == str(q["correct"])
            )

            with transaction.atomic():
                attempt = MissionQuizAttempt.objects.create(
                    user=request.user,
                    mission=record,
                    score=score,
                    total_questions=10,
                    answers=selected_answers,
                )

                record.completed = True
                record.completed_at = timezone.now()
                record.save(update_fields=["completed", "completed_at"])

                learning_progress, _ = LearningProgress.objects.get_or_create(
                    user=request.user
                )
                learning_progress.total_xp += record.xp
                learning_progress.missions_completed += 1
                attended_date = timezone.localdate()
                attendance, attendance_created = LearningAttendance.objects.get_or_create(
                    user=request.user,
                    date=attended_date,
                    defaults={
                        "minutes_spent": record.duration,
                        "missions_completed": 1,
                        "attended": True,
                    },
                )
                if not attendance_created:
                    attendance.minutes_spent += record.duration
                    attendance.missions_completed += 1
                    attendance.attended = True
                    attendance.save(
                        update_fields=[
                            "minutes_spent", "missions_completed", "attended"
                        ]
                    )

                attended_dates = list(
                    LearningAttendance.objects.filter(
                        user=request.user, attended=True
                    ).order_by("-date").values_list("date", flat=True)
                )
                streak_anchor = (
                    attended_date
                    if attended_dates and attended_dates[0] == attended_date
                    else attended_date - timedelta(days=1)
                )
                current_streak = 0
                for attended_day in attended_dates:
                    if attended_day != streak_anchor:
                        break
                    current_streak += 1
                    streak_anchor -= timedelta(days=1)
                learning_progress.current_streak = current_streak
                learning_progress.longest_streak = max(
                    learning_progress.longest_streak, current_streak
                )
                learning_progress.save(
                    update_fields=[
                        "total_xp", "missions_completed", "current_streak",
                        "longest_streak", "updated_at"
                    ]
                )

            result = {
                "score": score,
                "total": 10,
                "attempt_id": attempt.id,
                "review": [
                    {
                        "number": i,
                        "question": q["text"],
                        "chosen": q["options"][
                            int(selected_answers[q["id"]])
                        ]["text"],
                        "correct": q["options"][q["correct"]]["text"],
                        "is_correct": (
                            selected_answers[q["id"]] == str(q["correct"])
                        ),
                        "explanation": q["explanation"],
                    }
                    for i, q in enumerate(questions, start=1)
                ],
            }

            latest_attempts = MissionQuizAttempt.objects.filter(
                user=request.user, mission=record
            )[:5]

    context = {
        "student_name": get_student_name(request),
        "mission_title": record.title,
        "mission": mission,
        "completed": record.completed,
        "mission_record": record,
        "day_number": record.day_number,
        "mission_date": record.mission_date,
        "questions": questions,
        "selected_answers": selected_answers,
        "result": result,
        "latest_attempts": latest_attempts,
    }
    return render(request, "missions/mission_detail.html", context)

