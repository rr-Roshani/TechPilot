from datetime import datetime, time, timedelta
import json
import re

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import StudentProfile
from accounts.models import DashboardChecklistProgress
from accounts.models import LearningProgress
from accounts.models import MissionProgress
from accounts.models import MissionQuizAttempt
from accounts.models import InterviewAnswer, InterviewDayProgress
from assessment.models import (
    AssessmentAttempt,
    OnboardingQuestion,
    Question,
    PracticeLab,
    PracticeLabAttempt,
    PracticeQuestionAttempt,
)
from accounts.dashboard_metrics import assessment_percentage, percentage, summarize_missions
from techpilot.career_content import (
    CAREER_CHOICES,
    CAREER_SKILLS,
    interviews_for_career,
    job_roles_for_career,
    projects_for_career,
)


class ProgressMetricTests(TestCase):
    def test_mission_progress_uses_all_twenty_available_missions(self):
        self.assertEqual(summarize_missions([])["mission_progress"], 0)
        one_completed = [
            {"day_number": day, "completed": day == 1, "xp": 10}
            for day in range(1, 21)
        ]
        self.assertEqual(summarize_missions(one_completed)["mission_progress"], 5)
        half_completed = [
            {"day_number": day, "completed": day <= 10, "xp": 10}
            for day in range(1, 21)
        ]
        self.assertEqual(summarize_missions(half_completed)["mission_progress"], 50)
        all_completed = [
            {"day_number": day, "completed": True, "xp": 10}
            for day in range(1, 21)
        ]
        self.assertEqual(summarize_missions(all_completed)["mission_progress"], 100)

    def test_assessment_percentage_requires_a_valid_completed_result(self):
        from types import SimpleNamespace

        self.assertEqual(assessment_percentage(None), 0)
        for score in (0, 60):
            attempt = SimpleNamespace(
                is_completed=True, total_questions=10,
                correct_answers=score // 10, score=99,
            )
            self.assertEqual(assessment_percentage(attempt), score)
        invalid = SimpleNamespace(
            is_completed=True, total_questions=0, correct_answers=5, score=60
        )
        self.assertEqual(assessment_percentage(invalid), 0)


class AuthFlowTests(TestCase):
    def _create_onboarded_student(self, career="Cloud Engineer"):
        User = get_user_model()
        student = User.objects.create_user(
            username=f"student-{StudentProfile.objects.count()}@example.com",
            password="secret123",
        )
        StudentProfile.objects.create(
            user=student,
            onboarding_completed=True,
            career_goal=career,
        )
        self.client.force_login(student)
        return student

    def test_all_careers_persist_across_learning_pages_refresh_and_login(self):
        student = self._create_onboarded_student(CAREER_CHOICES[0])
        AssessmentAttempt.objects.create(
            user=student, total_questions=1, correct_answers=1, score=100,
            is_completed=True, completed_at=timezone.now(),
        )
        self.client.logout()
        login = self.client.post(reverse("login"), {
            "email": student.username, "password": "secret123",
        })
        self.assertRedirects(login, reverse("dashboard"))
        paths = (
            reverse("edit_profile"), reverse("dashboard"), reverse("roadmap"),
            reverse("missions"), reverse("practice"), reverse("projects"),
            reverse("interviews"), reverse("jobs"), reverse("progress"),
        )

        for career in CAREER_CHOICES:
            with self.subTest(career=career):
                self.client.post(reverse("roadmap"), {"career": career})
                self.assertEqual(StudentProfile.objects.get(user=student).career_goal, career)
                for visit in range(2):  # Navigation then refresh.
                    for path in paths:
                        page = self.client.get(path)
                        self.assertEqual(page.status_code, 200, (career, path))
                        actual = page.context.get("career_goal")
                        if actual is None and page.context.get("profile"):
                            actual = page.context["profile"].career_goal
                        self.assertEqual(actual, career, (career, path))

                self.client.get(reverse("logout"))
                login = self.client.post(reverse("login"), {
                    "email": student.username, "password": "secret123",
                })
                self.assertRedirects(login, reverse("dashboard"))
                for path in paths:
                    page = self.client.get(path)
                    self.assertEqual(page.status_code, 200, ("after login", career, path))
                    actual = page.context.get("career_goal")
                    if actual is None and page.context.get("profile"):
                        actual = page.context["profile"].career_goal
                    self.assertEqual(actual, career, ("after login", career, path))

    def test_profile_and_teacher_lab_posts_enforce_csrf(self):
        student = self._create_onboarded_student("Data Analyst")
        student_client = Client(enforce_csrf_checks=True)
        student_client.force_login(student)
        profile_page = student_client.get(reverse("edit_profile"))
        self.assertEqual(profile_page.status_code, 200)
        profile_data = {
            "name": student.first_name, "education": "BTECH", "year": "2nd Year",
            "specialization": "Computer Science", "career_goal": "Cloud Engineer",
            "skills": ["SQL", "Terraform"], "skill_level": "Beginner",
            "study_time": "60", "preparation": "Skill Building",
        }
        self.assertEqual(
            student_client.post(reverse("edit_profile"), profile_data).status_code, 403
        )
        csrf_token = student_client.cookies["csrftoken"].value
        saved_profile = student_client.post(
            reverse("edit_profile"), profile_data,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertRedirects(saved_profile, reverse("dashboard"))
        profile = StudentProfile.objects.get(user=student)
        self.assertEqual(profile.career_goal, "Cloud Engineer")
        self.assertEqual(profile.skills, ["SQL", "Terraform"])
        invalid_data = {**profile_data, "career_goal": "Unsupported Career", "skills": ["Should Not Save"]}
        invalid = student_client.post(
            reverse("edit_profile"), invalid_data,
            HTTP_X_CSRFTOKEN=csrf_token,
            follow=True,
        )
        self.assertContains(invalid, "Please choose a valid career goal")
        profile.refresh_from_db()
        self.assertEqual(profile.career_goal, "Cloud Engineer")
        self.assertEqual(profile.skills, ["SQL", "Terraform"])

        User = get_user_model()
        teacher = User.objects.create_user(
            username="csrf-lab-teacher@example.com", password="secret123", is_staff=True,
        )
        teacher_client = Client(enforce_csrf_checks=True)
        teacher_client.force_login(teacher)
        lab_page = teacher_client.get(reverse("admin_practice_labs"))
        self.assertEqual(lab_page.status_code, 200)
        lab_data = {
            "action": "add", "title": "Draft only lab", "roadmap": "Cloud Engineer",
            "skills": ["Linux"], "difficulty": "beginner", "content_type": "lab",
            "description": "A draft exercise.", "task": "Complete the draft task.", "xp": "10",
        }
        self.assertEqual(
            teacher_client.post(reverse("admin_practice_labs"), lab_data).status_code, 403
        )
        csrf_token = teacher_client.cookies["csrftoken"].value
        response = teacher_client.post(
            reverse("admin_practice_labs"), lab_data,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertRedirects(response, reverse("admin_practice_labs"))
        draft = PracticeLab.objects.get(title="Draft only lab")
        self.assertEqual(draft.status, "draft")
        student_client.force_login(student)
        practice = student_client.get(reverse("practice"))
        self.assertNotIn(draft.id, [lab.id for lab in practice.context["skill_labs"] + practice.context["practice_challenges"]])

    def test_teacher_practice_lab_form_has_canonical_careers_and_career_skill_catalog(self):
        User = get_user_model()
        teacher = User.objects.create_user(
            username="catalog-teacher@example.com", password="secret123", is_staff=True,
        )
        self.client.force_login(teacher)
        response = self.client.get(reverse("admin_practice_labs"))
        self.assertEqual(response.status_code, 200)
        choices = response.context["roadmap_choices"]
        self.assertEqual([value for value, _label in choices], CAREER_CHOICES)
        self.assertIn(
            ("Cybersecurity Analyst", "Penetration Testing / Cybersecurity Analyst"),
            choices,
        )
        catalog = json.loads(response.context["skill_catalog_json"])
        self.assertIn("Power BI", catalog["Data Analyst"])
        self.assertIn("Pandas", catalog["Data Analyst"])
        self.assertIn("AWS", catalog["Cloud Engineer"])
        self.assertIn("Linux", catalog["Cybersecurity Analyst"])
        self.assertIn("Android SDK", catalog["Android Developer"])
        self.assertContains(response, "practice-skill-search")
        self.assertContains(response, "practiceSkillCatalog")
        self.assertContains(response, '<option value="Data Analyst">')
        self.assertContains(response, '<option value="Cybersecurity Analyst">')
        self.assertContains(response, "key(value).includes(query)")
        self.assertContains(response, "No matching skills")

    def test_teacher_lab_custom_skills_normalize_validate_and_canonicalize_career(self):
        User = get_user_model()
        teacher = User.objects.create_user(
            username="custom-lab-teacher@example.com", password="secret123", is_staff=True,
        )
        self.client.force_login(teacher)
        form = {
            "action": "add", "title": "Security tooling lab",
            "roadmap": "Penetration Testing / Cybersecurity Analyst",
            "skills": ["  Burp   Suite ", "burp suite", "Custom Scanner"],
            "difficulty": "beginner", "content_type": "lab",
            "description": "Practice safe scanning in a sandbox.",
            "task": "Document findings from the authorized target.", "xp": "10",
        }
        response = self.client.post(reverse("admin_practice_labs"), form, follow=True)
        lab = PracticeLab.objects.get(title="Security tooling lab")
        self.assertEqual(lab.roadmap, "Cybersecurity Analyst")
        self.assertEqual(lab.skill, "Burp Suite, Custom Scanner")
        self.assertEqual(lab.status, "draft")
        self.assertEqual(lab.created_by, teacher)
        self.assertContains(response, "Practice Lab saved")

        form.update(title="Invalid oversized lab", skills=["x" * 61])
        response = self.client.post(reverse("admin_practice_labs"), form, follow=True)
        self.assertFalse(PracticeLab.objects.filter(title="Invalid oversized lab").exists())
        self.assertContains(response, "60 characters or fewer")
        form.update(title="Invalid oversized combined skills", skills=["x" * 60, "y" * 40])
        response = self.client.post(reverse("admin_practice_labs"), form, follow=True)
        self.assertFalse(PracticeLab.objects.filter(title="Invalid oversized combined skills").exists())
        self.assertContains(response, "combined skills must fit within 100 characters")

    def test_teacher_lab_lifecycle_student_visibility_and_attempt_isolation(self):
        User = get_user_model()
        teacher = User.objects.create_user(
            username="lab-teacher@example.com", password="secret123", is_staff=True,
        )
        other_teacher = User.objects.create_user(
            username="other-teacher@example.com", password="secret123", is_staff=True,
        )
        student = self._create_onboarded_student("Data Analyst")
        other_student = User.objects.create_user(
            username="lab-student-2@example.com", password="secret123",
        )
        StudentProfile.objects.create(
            user=other_student, career_goal="Data Analyst", onboarding_completed=True,
        )

        self.client.force_login(teacher)
        self.client.post(reverse("admin_practice_labs"), {
            "action": "add", "title": "Data quality lab", "roadmap": "Data Analyst",
            "skills": ["SQL", "Statistics"], "difficulty": "beginner",
            "content_type": "challenge", "description": "Check a small dataset.",
            "task": "Find invalid rows and explain your checks.", "xp": "20",
            "status": "draft",
        })
        lab = PracticeLab.objects.get(title="Data quality lab")
        self.assertEqual(lab.created_by, teacher)
        self.assertEqual(lab.status, "draft")
        self.assertEqual(self.client.get(reverse("admin_practice_lab_edit", args=[lab.id])).status_code, 200)

        self.client.force_login(other_teacher)
        self.assertRedirects(
            self.client.get(reverse("admin_practice_lab_edit", args=[lab.id])),
            reverse("admin_practice_labs"),
        )
        self.client.force_login(teacher)
        self.client.post(reverse("admin_practice_lab_edit", args=[lab.id]), {
            "title": lab.title, "roadmap": lab.roadmap, "skill": lab.skill,
            "difficulty": lab.difficulty, "content_type": "challenge",
            "description": lab.description, "task": lab.task,
            "expected_answer": "No invalid rows remain.", "explanation": "Check nulls and ranges.",
            "xp": "20", "status": "published",
        })
        lab.refresh_from_db()
        self.assertEqual(lab.status, "published")

        self.client.force_login(student)
        page = self.client.get(reverse("practice"))
        self.assertContains(page, "Data quality lab")
        self.assertIn(
            lab.id, [item.id for item in page.context["practice_challenges"]]
        )
        self.client.post(reverse("practice"), {
            "action": "submit_lab", "lab_id": str(lab.id),
            "response": "Checked missing values and duplicates.", "completed": "on",
        })
        self.assertTrue(PracticeLabAttempt.objects.filter(
            user=student, lab=lab, completed=True,
        ).exists())
        other_page = Client()
        other_page.force_login(other_student)
        response = other_page.get(reverse("practice"))
        self.assertEqual(response.context["completed_practice_labs"], 0)

        self.client.force_login(teacher)
        self.client.post(reverse("admin_practice_lab_delete", args=[lab.id]))
        lab.refresh_from_db()
        self.assertEqual(lab.status, "archived")
        self.assertTrue(PracticeLabAttempt.objects.filter(lab=lab).exists())
        self.client.force_login(student)
        self.assertNotContains(self.client.get(reverse("practice")), "Data quality lab")

    def test_teacher_question_draft_publish_attempt_and_career_isolation(self):
        User = get_user_model()
        teacher = User.objects.create_user(
            username="question-teacher@example.com", password="secret123", is_staff=True,
        )
        other_teacher = User.objects.create_user(
            username="other-question-teacher@example.com", password="secret123", is_staff=True,
        )
        student = self._create_onboarded_student("Data Analyst")
        question = {
            "question_text": "Which SQL clause filters rows?",
            "option_a": "WHERE", "option_b": "ORDER BY",
            "option_c": "GROUP BY", "option_d": "JOIN",
            "correct_answer": "A", "skill": "sql", "difficulty": "beginner",
            "explanation": "WHERE filters rows before grouping.",
        }
        self.client.force_login(teacher)
        self.client.post(reverse("admin_questions"), {**question, "status": "draft"})
        saved = Question.objects.get(question_text=question["question_text"])
        self.assertEqual(saved.created_by, teacher)
        self.assertEqual(saved.status, "draft")
        self.assertEqual(
            self.client.get(reverse("admin_question_detail", args=[saved.id])).status_code,
            200,
        )
        self.client.force_login(other_teacher)
        self.assertRedirects(
            self.client.get(reverse("admin_question_detail", args=[saved.id])),
            reverse("admin_questions"),
        )
        self.client.force_login(student)
        self.assertNotContains(self.client.get(reverse("practice")), saved.question_text)
        self.client.force_login(teacher)
        self.client.post(
            reverse("admin_question_detail", args=[saved.id]),
            {**question, "status": "published"},
        )
        saved.refresh_from_db()
        self.assertEqual(saved.status, "published")

        self.client.force_login(student)
        page = self.client.get(reverse("practice"))
        self.assertContains(page, saved.question_text)
        self.client.post(reverse("practice"), {
            "action": "answer_question", "question_id": str(saved.id), "answer": "B",
        })
        self.client.post(reverse("practice"), {
            "action": "answer_question", "question_id": str(saved.id), "answer": "A",
        })
        self.assertTrue(PracticeQuestionAttempt.objects.filter(
            user=student, question=saved, career_goal="Data Analyst", is_correct=True,
        ).exists())
        practice_summary = self.client.get(reverse("practice"))
        self.assertEqual(practice_summary.context["practice_attempt_count"], 2)
        self.assertEqual(practice_summary.context["practice_accuracy"], 50)
        self.assertContains(practice_summary, "Review incorrect practice answers")
        self.client.post(reverse("roadmap"), {"career": "Full Stack Developer"})
        switched = self.client.get(reverse("practice"))
        self.assertEqual(switched.context["practice_attempt_count"], 0)
        self.assertEqual(
            PracticeQuestionAttempt.objects.filter(
                user=student, question=saved, career_goal="Data Analyst",
            ).count(),
            2,
        )
        self.client.force_login(teacher)
        self.client.post(
            reverse("admin_question_detail", args=[saved.id]),
            {**question, "status": "archived"},
        )
        saved.refresh_from_db()
        self.assertEqual(saved.status, "archived")
        self.assertEqual(
            PracticeQuestionAttempt.objects.filter(user=student, question=saved).count(),
            2,
        )
        self.client.force_login(student)
        self.client.post(reverse("roadmap"), {"career": "Data Analyst"})
        self.assertNotContains(self.client.get(reverse("practice")), saved.question_text)

    def test_every_career_has_published_practice_content_outside_assessment_pool(self):
        student = self._create_onboarded_student("Cloud Engineer")
        baseline_question = Question.objects.create(
            question_text="Assessment pool exclusion check",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A", skill="python", difficulty="beginner",
            assessment_enabled=True,
        )
        for career in CAREER_CHOICES:
            self.client.post(reverse("roadmap"), {"career": career})
            practice = self.client.get(reverse("practice"))
            self.assertEqual(practice.status_code, 200)
            self.assertTrue(practice.context["skill_labs"], career)
            self.assertTrue(practice.context["practice_challenges"], career)
            self.assertTrue(practice.context["practice_questions"], career)
            self.assertTrue(
                all(q.status == "published" for q in practice.context["practice_questions"]),
                career,
            )
            assessment = self.client.get(reverse("assessment"))
            attempt = assessment.context["attempt"]
            assigned = Question.objects.filter(id__in=attempt.question_ids)
            self.assertTrue(assigned.exists(), career)
            self.assertIn(baseline_question.id, attempt.question_ids)
            self.assertTrue(assigned.filter(assessment_enabled=False).count() == 0, career)
        self.assertEqual(StudentProfile.objects.get(user=student).career_goal, CAREER_CHOICES[-1])

    def test_edit_profile_recommendations_render_for_every_career_and_cyber_alias(self):
        student = self._create_onboarded_student("Cloud Engineer")
        profile = StudentProfile.objects.get(user=student)
        expected_skills = {
            "Cloud Engineer": {"Linux", "Networking", "AWS", "Azure", "Docker", "Kubernetes", "IAM", "CI/CD", "Monitoring", "Terraform"},
            "Full Stack Developer": {"HTML", "CSS", "JavaScript", "React", "Node.js", "Django", "REST APIs", "Git", "SQL", "Testing"},
            "Data Analyst": {"SQL", "Excel", "Python", "Pandas", "NumPy", "Statistics", "Data Visualization", "Power BI", "Tableau"},
            "AI/ML Engineer": {"Python", "NumPy", "Pandas", "Statistics", "Linear Algebra", "Machine Learning", "Scikit-learn", "Deep Learning", "TensorFlow", "Model Evaluation"},
            "Android Developer": {"Kotlin", "Java", "Android Studio", "Android SDK", "Activities", "Intents", "Jetpack Compose", "Room", "APIs", "Testing"},
            "Cybersecurity Analyst": {"Networking", "Linux", "Python", "Security Fundamentals", "OWASP Top 10", "Web Security", "Burp Suite", "Nmap", "Wireshark", "Vulnerability Assessment"},
            "Not Sure Yet": set(CAREER_SKILLS["Not Sure Yet"]),
        }
        for career, required in expected_skills.items():
            with self.subTest(career=career):
                profile.career_goal = career
                profile.save(update_fields=["career_goal", "updated_at"])
                response = self.client.get(reverse("edit_profile"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.context["current_career_skills"]), required)
                for skill in required:
                    self.assertContains(response, f'data-recommended-skill="{skill}"')
                    self.assertContains(response, f"Add {skill}")
                payload = re.search(
                    rb'<script id="careerSkillRecommendations" type="application/json">(.*?)</script>',
                    response.content,
                    re.DOTALL,
                )
                self.assertIsNotNone(payload)
                rendered_mapping = json.loads(payload.group(1))
                self.assertEqual(rendered_mapping[career], CAREER_SKILLS[career])

        StudentProfile.objects.filter(user=student).update(career_goal="Cybersecurity")
        alias_page = self.client.get(reverse("edit_profile"))
        self.assertContains(alias_page, "Recommended for <span id=\"recommendation-career\">Cybersecurity Analyst")
        self.assertIn("OWASP Top 10", alias_page.context["current_career_skills"])

    def test_edit_profile_json_skills_are_a_list_and_recommendations_save(self):
        student = self._create_onboarded_student("Data Analyst")
        profile = StudentProfile.objects.get(user=student)
        profile.skills = ["SQL", "Old Skill"]
        profile.save(update_fields=["skills", "updated_at"])
        page = self.client.get(reverse("edit_profile"))
        payload = re.search(
            rb'<script id="savedSkills" type="application/json">(.*?)</script>',
            page.content,
            re.DOTALL,
        )
        self.assertIsNotNone(payload)
        self.assertEqual(json.loads(payload.group(1)), ["SQL", "Old Skill"])
        self.assertContains(page, 'data-saved-skill="SQL"')

        self.client.post(reverse("edit_profile"), {
            "name": student.first_name,
            "education": "BTECH",
            "year": "2nd Year",
            "specialization": "Computer Science",
            "career_goal": "Data Analyst",
            "skills": ["SQL", "Old Skill", "Power BI", "Custom Data Tool"],
            "skill_level": "Intermediate",
            "study_time": "45",
            "preparation": "Skill Building",
        })
        profile.refresh_from_db()
        self.assertEqual(profile.skills, ["SQL", "Old Skill", "Power BI", "Custom Data Tool"])
        self.client.post(reverse("edit_profile"), {
            "name": student.first_name,
            "education": "BTECH",
            "year": "2nd Year",
            "specialization": "Computer Science",
            "career_goal": "Cloud Engineer",
            "skills": [*profile.skills, "Kubernetes"],
            "skill_level": "Intermediate",
            "study_time": "45",
            "preparation": "Skill Building",
        })
        profile.refresh_from_db()
        self.assertEqual(profile.career_goal, "Cloud Engineer")
        self.assertEqual(profile.skills, ["SQL", "Old Skill", "Power BI", "Custom Data Tool", "Kubernetes"])
        self.assertContains(self.client.get(reverse("edit_profile")), 'data-saved-skill="Custom Data Tool"')

    def test_edit_profile_preserves_deduplicates_and_saves_custom_skills(self):
        student = self._create_onboarded_student("Data Analyst")
        profile = StudentProfile.objects.get(user=student)
        profile.skills = ["  Python  ", "SQL", "Old Tool"]
        profile.save(update_fields=["skills", "updated_at"])

        page = self.client.get(reverse("edit_profile"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'data-saved-skill="  Python  "')
        self.assertContains(page, 'data-saved-skill="SQL"')
        self.assertContains(page, "Search recommended skills")
        self.assertContains(page, "recommendation-empty")
        self.assertContains(page, "Data Analyst")
        self.assertContains(page, "Power BI")
        self.assertContains(page, "savedSkills")
        self.assertContains(page, "Add another skill")
        self.assertContains(page, "Android Developer")
        self.assertContains(page, 'name="viewport"')
        self.assertContains(page, "@media (max-width:480px)")

        response = self.client.post(reverse("edit_profile"), {
            "name": student.first_name,
            "education": "BTECH",
            "year": "2nd Year",
            "specialization": "Computer Science",
            "career_goal": "Cloud Engineer",
            "skills": ["  Python  ", "python", "Old   Tool", "Terraform", "Kubernetes"],
            "skill_level": "Beginner",
            "study_time": "60",
            "preparation": "Skill Building",
        }, follow=True)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertContains(response, "Profile updated successfully")
        profile.refresh_from_db()
        self.assertEqual(profile.career_goal, "Cloud Engineer")
        self.assertEqual(profile.skills, ["Python", "Old Tool", "Terraform", "Kubernetes"])
        reopened = self.client.get(reverse("edit_profile"))
        self.assertEqual(reopened.status_code, 200)
        self.assertContains(reopened, 'data-saved-skill="Terraform"')
        self.assertContains(reopened, 'data-saved-skill="Kubernetes"')
        profile.refresh_from_db()
        self.assertIn("Terraform", profile.skills)
        self.assertIn("Kubernetes", profile.skills)
        self.client.logout()
        self.client.post("/", {"email": student.username, "password": "secret123"})
        after_login = self.client.get(reverse("edit_profile"))
        self.assertEqual(after_login.status_code, 200)
        self.assertContains(after_login, 'data-saved-skill="Terraform"')

    def test_profile_cancel_get_does_not_persist_unsaved_values(self):
        student = self._create_onboarded_student("Data Analyst")
        profile = StudentProfile.objects.get(user=student)
        profile.skills = ["SQL"]
        profile.save(update_fields=["skills", "updated_at"])

        response = self.client.get(reverse("edit_profile"))
        self.assertContains(response, 'href="/dashboard/"')
        profile.refresh_from_db()
        self.assertEqual(profile.career_goal, "Data Analyst")
        self.assertEqual(profile.skills, ["SQL"])

    def test_dashboard_and_learning_pages_share_saved_career_and_separate_skill_states(self):
        student = self._create_onboarded_student("Data Analyst")
        profile = StudentProfile.objects.get(user=student)
        profile.skills = ["SQL"]  # Self-report must not complete the roadmap skill.
        profile.save(update_fields=["skills", "updated_at"])
        MissionProgress.objects.create(
            user=student, career_goal="Data Analyst", day_number=1,
            title="Pandas practice", skill="Pandas", completed=False,
        )

        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.context["career_goal"], "Data Analyst")
        self.assertIn("SQL", dashboard.context["skills"])
        self.assertIn("Pandas", dashboard.context["learning_skills"])
        self.assertIn("SQL", dashboard.context["missing_skills"])
        self.assertContains(dashboard, "Recommended for Data Analyst")

        self.client.post(reverse("roadmap"), {"career": "Cloud Engineer"})
        for path in (
            reverse("dashboard"), reverse("roadmap"), reverse("missions"),
            reverse("practice"), reverse("projects"), reverse("interviews"),
            reverse("jobs"),
        ):
            page = self.client.get(path)
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, "Cloud Engineer")
        profile.refresh_from_db()
        self.assertEqual(profile.career_goal, "Cloud Engineer")
        self.assertEqual(profile.skills, ["SQL"])

    def test_dashboard_zero_metrics_and_percentage_rounding(self):
        student = self._create_onboarded_student("Data Analyst")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["assessment_score"], 0)
        self.assertEqual(response.context["mission_progress"], 0)
        self.assertEqual(response.context["missions_completed"], 0)
        self.assertEqual(response.context["career_mission_count"], 20)
        self.assertEqual(response.context["total_xp"], 0)
        self.assertEqual(response.context["streak"], 0)
        self.assertEqual(response.context["skills_count"], 0)
        self.assertEqual(percentage(0, 0), 0)
        self.assertEqual(percentage(1, 8), 13)  # 12.5 rounds half up.
        self.assertEqual(percentage(1, 3), 33)

    def test_dashboard_metrics_use_saved_missions_and_refresh_consistently(self):
        student = self._create_onboarded_student("Data Analyst")
        profile = StudentProfile.objects.get(user=student)
        profile.skills = ["Python", "SQL"]
        profile.save(update_fields=["skills", "updated_at"])
        LearningProgress.objects.create(user=student, current_streak=99)

        attempt = AssessmentAttempt.objects.create(
            user=student,
            total_questions=8,
            correct_answers=1,
            score=99,  # Dashboard must calculate from answer counts.
            is_completed=True,
            completed_at=timezone.now(),
        )
        today = timezone.localdate()
        today_at = timezone.make_aware(datetime.combine(today, time(12)))
        yesterday = today - timedelta(days=1)
        yesterday_at = timezone.make_aware(datetime.combine(yesterday, time(12)))

        MissionProgress.objects.create(
            user=student, career_goal="Data Analyst", day_number=1,
            title="SQL Basics", xp=40, completed=True, completed_at=today_at,
        )
        # Legacy duplicate rows for one logical day must not inflate counts/XP.
        MissionProgress.objects.create(
            user=student, career_goal="Data Analyst", day_number=1,
            title="SQL Basics duplicate", xp=40, completed=True,
            completed_at=today_at,
        )
        MissionProgress.objects.create(
            user=student, career_goal="Data Analyst", day_number=2,
            title="Python Basics", xp=50, completed=True,
            completed_at=yesterday_at,
        )
        MissionProgress.objects.create(
            user=student, career_goal="Data Analyst", day_number=3,
            title="Charts", xp=60, completed=False,
        )
        MissionProgress.objects.create(
            user=student, career_goal="Cloud Engineer", day_number=1,
            title="Cloud mission", xp=500, completed=True,
            completed_at=today_at,
        )

        expected = {
            "assessment_score": 13,
            "missions_completed": 2,
            "career_mission_count": 20,
            "mission_progress": 10,
            "total_xp": 90,
            "streak": 2,
            "skills_count": 2,
        }
        for _ in range(2):
            response = self.client.get("/dashboard/")
            self.assertEqual(response.status_code, 200)
            for key, value in expected.items():
                with self.subTest(key=key):
                    self.assertEqual(response.context[key], value)
        self.assertEqual(attempt.correct_answers, 1)

    def test_dashboard_metrics_switch_with_selected_career(self):
        student = self._create_onboarded_student("Data Analyst")
        MissionProgress.objects.create(
            user=student, career_goal="Data Analyst", day_number=1,
            title="Data task", xp=40, completed=True,
        )
        MissionProgress.objects.create(
            user=student, career_goal="Cloud Engineer", day_number=1,
            title="Cloud task", xp=70, completed=True,
        )
        response = self.client.get("/dashboard/")
        self.assertEqual(response.context["total_xp"], 40)
        self.assertEqual(response.context["missions_completed"], 1)

        self.assertRedirects(
            self.client.post("/roadmap/", {"career": "Cloud Engineer"}),
            "/roadmap/",
        )
        response = self.client.get("/dashboard/")
        self.assertEqual(response.context["career_goal"], "Cloud Engineer")
        self.assertEqual(response.context["total_xp"], 70)
        self.assertEqual(response.context["missions_completed"], 1)
        self.assertEqual(response.context["mission_progress"], 5)

    def test_checklist_state_survives_navigation_and_dashboard_refresh(self):
        student = self._create_onboarded_student("Data Analyst")
        endpoint = reverse("dashboard_checklist_update")
        response = self.client.post(
            endpoint,
            {"item_key": "skill_assessment", "completed": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["xp_awarded"], 20)
        saved = DashboardChecklistProgress.objects.get(
            user=student, career_goal="Data Analyst", item_key="skill_assessment"
        )
        self.assertTrue(saved.completed)

        self.assertEqual(self.client.get("/roadmap/").status_code, 200)
        for _ in range(2):
            dashboard = self.client.get("/dashboard/")
            self.assertEqual(dashboard.status_code, 200)
            task = next(
                item for item in dashboard.context["checklist_items"]
                if item["key"] == "skill_assessment"
            )
            self.assertTrue(task["completed"])
            self.assertEqual(dashboard.context["total_xp"], 20)
            self.assertContains(dashboard, 'aria-checked="true"')

        self.client.get("/logout/")
        self.client.force_login(student)
        returned = self.client.get("/dashboard/")
        self.assertTrue(
            next(
                item for item in returned.context["checklist_items"]
                if item["key"] == "skill_assessment"
            )["completed"]
        )

    def test_checklist_uncheck_and_recheck_never_awards_xp_twice(self):
        student = self._create_onboarded_student("Data Analyst")
        endpoint = reverse("dashboard_checklist_update")
        first = self.client.post(
            endpoint,
            {"item_key": "weakest_skill", "completed": "true"},
        )
        self.assertEqual(first.json()["xp_awarded"], 30)
        uncheck = self.client.post(
            endpoint,
            {"item_key": "weakest_skill", "completed": "false"},
        )
        self.assertFalse(uncheck.json()["completed"])
        self.assertEqual(uncheck.json()["xp_awarded"], 0)
        self.assertEqual(uncheck.json()["total_xp"], 30)
        recheck = self.client.post(
            endpoint,
            {"item_key": "weakest_skill", "completed": "true"},
        )
        self.assertTrue(recheck.json()["completed"])
        self.assertEqual(recheck.json()["xp_awarded"], 0)
        self.assertEqual(recheck.json()["total_xp"], 30)
        saved = DashboardChecklistProgress.objects.get(
            user=student, career_goal="Data Analyst", item_key="weakest_skill"
        )
        self.assertEqual(saved.xp_awarded, 30)

    def test_checklist_progress_is_isolated_by_user_and_career(self):
        first_student = self._create_onboarded_student("Data Analyst")
        endpoint = reverse("dashboard_checklist_update")
        self.client.post(
            endpoint,
            {"item_key": "personalized_roadmap", "completed": "true"},
        )

        self.client.post("/roadmap/", {"career": "Cloud Engineer"})
        cloud_dashboard = self.client.get("/dashboard/")
        self.assertFalse(
            next(
                item for item in cloud_dashboard.context["checklist_items"]
                if item["key"] == "personalized_roadmap"
            )["completed"]
        )
        self.client.post(
            endpoint,
            {"item_key": "personalized_roadmap", "completed": "true"},
        )
        self.assertEqual(
            DashboardChecklistProgress.objects.filter(
                user=first_student, item_key="personalized_roadmap"
            ).count(),
            2,
        )

        self.client.post("/roadmap/", {"career": "Data Analyst"})
        data_dashboard = self.client.get("/dashboard/")
        self.assertTrue(
            next(
                item for item in data_dashboard.context["checklist_items"]
                if item["key"] == "personalized_roadmap"
            )["completed"]
        )
        self.assertEqual(data_dashboard.context["total_xp"], 25)

        second_student = self._create_onboarded_student("Cloud Engineer")
        second_dashboard = self.client.get("/dashboard/")
        self.assertFalse(
            next(
                item for item in second_dashboard.context["checklist_items"]
                if item["key"] == "personalized_roadmap"
            )["completed"]
        )
        self.assertFalse(
            DashboardChecklistProgress.objects.filter(user=second_student).exists()
        )
        self.assertEqual(second_dashboard.context["total_xp"], 0)

    def test_checklist_endpoint_requires_csrf_and_valid_item(self):
        student = self._create_onboarded_student("Data Analyst")
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(student)
        endpoint = reverse("dashboard_checklist_update")
        denied = csrf_client.post(
            endpoint,
            {"item_key": "skill_assessment", "completed": "true"},
        )
        self.assertEqual(denied.status_code, 403)

        page = csrf_client.get("/dashboard/")
        token = csrf_client.cookies["csrftoken"].value
        saved = csrf_client.post(
            endpoint,
            {"item_key": "not-a-checklist-item", "completed": "true"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(saved.status_code, 400)
        valid = csrf_client.post(
            endpoint,
            {"item_key": "skill_assessment", "completed": "true"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(page.status_code, 200)

    def test_assessment_submission_saves_baseline_and_retest(self):
        student = self._create_onboarded_student()
        questions = [
            Question.objects.create(
                question_text=f"Assessment question {index}",
                option_a="Correct",
                option_b="Wrong",
                option_c="Wrong",
                option_d="Wrong",
                correct_answer="A",
                skill="python",
                difficulty="beginner",
            )
            for index in range(2)
        ]

        page = self.client.get("/assessment/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="question_id"')
        baseline = page.context["attempt"]
        payload = {"question_id": [str(q.id) for q in questions]}
        payload["attempt_id"] = str(baseline.id)
        payload.update({f"question_{q.id}": "A" for q in questions})
        response = self.client.post("/assessment/", payload)

        attempt = AssessmentAttempt.objects.get(user=student, is_completed=True)
        self.assertRedirects(response, f"/assessment/result/{attempt.id}/")
        self.assertEqual(attempt.attempt_type, "baseline")
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.score, 100)
        self.assertEqual(attempt.answers.count(), 2)
        self.assertEqual(self.client.get(f"/assessment/result/{attempt.id}/").status_code, 200)

        duplicate = self.client.post("/assessment/", payload)
        self.assertRedirects(duplicate, f"/assessment/result/{attempt.id}/")
        self.assertEqual(AssessmentAttempt.objects.filter(user=student).count(), 1)
        summary = self.client.get("/assessment/")
        self.assertEqual(summary.context["completed_attempt"].id, attempt.id)
        self.assertContains(summary, "Restart Assessment")

        restart = self.client.post("/assessment/", {"action": "restart"})
        self.assertRedirects(restart, "/assessment/")
        retest_page = self.client.get("/assessment/")
        retest = retest_page.context["attempt"]
        self.assertNotEqual(retest.id, attempt.id)
        self.assertEqual(retest.attempt_type, "retest")
        retest_payload = {
            "attempt_id": str(retest.id),
            "question_id": [str(q.id) for q in questions],
        }
        retest_payload.update(
            {f"question_{q.id}": ("A" if index == 0 else "B")
             for index, q in enumerate(questions)}
        )
        response = self.client.post("/assessment/", retest_payload)
        self.assertRedirects(response, f"/assessment/result/{retest.id}/")
        attempt.refresh_from_db()
        retest.refresh_from_db()
        self.assertEqual(attempt.score, 100)
        self.assertEqual(attempt.answers.count(), 2)
        self.assertEqual(retest.score, 50)
        self.assertEqual(retest.answers.count(), 2)
        self.assertEqual(AssessmentAttempt.objects.filter(user=student).count(), 2)
        self.assertEqual(
            AssessmentAttempt.objects.filter(user=student, attempt_type="retest").count(),
            1,
        )
        self.assertEqual(self.client.get("/dashboard/").context["assessment_score"], 50)
        self.assertEqual(self.client.get("/roadmap/").context["assessment_score"], 50)

    def test_completed_assessment_allows_navigation_and_keeps_summary(self):
        student = self._create_onboarded_student("Data Analyst")
        question = Question.objects.create(
            question_text="Persisted question",
            option_a="Correct", option_b="Wrong", option_c="Wrong", option_d="Wrong",
            correct_answer="A", skill="python", difficulty="beginner",
        )
        form = self.client.get("/assessment/")
        draft = form.context["attempt"]
        self.client.post(
            "/assessment/",
            {
                "attempt_id": draft.id,
                "question_id": [str(question.id)],
                f"question_{question.id}": "A",
            },
        )
        for path in (
            "/dashboard/", "/roadmap/", "/missions/", "/practice/",
            "/projects/", "/interviews/", "/jobs/", "/progress/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        summary = self.client.get("/assessment/")
        self.assertContains(summary, "Restart Assessment")
        self.assertEqual(AssessmentAttempt.objects.filter(user=student).count(), 1)
        self.client.get("/logout/")
        login_response = self.client.post(
            "/",
            {"email": student.username, "password": "secret123"},
            follow=True,
        )
        self.assertRedirects(login_response, "/dashboard/")

    def test_legacy_incomplete_retest_does_not_start_without_explicit_restart(self):
        student = self._create_onboarded_student()
        question = Question.objects.create(
            question_text="Baseline question",
            option_a="Correct", option_b="Wrong", option_c="Wrong", option_d="Wrong",
            correct_answer="A", skill="python", difficulty="beginner",
        )
        draft = self.client.get("/assessment/").context["attempt"]
        self.client.post(
            "/assessment/",
            {
                "attempt_id": str(draft.id),
                "question_id": [str(question.id)],
                f"question_{question.id}": "A",
            },
        )
        AssessmentAttempt.objects.create(
            user=student,
            attempt_type="retest",
            is_completed=False,
            total_questions=1,
            started_at=timezone.now(),
        )

        response = self.client.get("/assessment/")
        self.assertContains(response, "Restart Assessment")
        self.assertNotIn('id="assessmentForm"', response.content.decode())

    def test_assessment_submission_requires_csrf_and_attempt_ownership(self):
        student = self._create_onboarded_student()
        Question.objects.create(
            question_text="Secure submission question",
            option_a="Correct", option_b="Wrong", option_c="Wrong", option_d="Wrong",
            correct_answer="A", skill="python", difficulty="beginner",
        )
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(student)
        form = csrf_client.get("/assessment/")
        draft = form.context["attempt"]
        question_ids = [str(question_id) for question_id in draft.question_ids]
        payload = {"attempt_id": str(draft.id), "question_id": question_ids}
        payload.update({f"question_{question_id}": "A" for question_id in question_ids})

        denied = csrf_client.post("/assessment/", payload)
        self.assertEqual(denied.status_code, 403)
        draft.refresh_from_db()
        self.assertFalse(draft.is_completed)
        self.assertEqual(draft.answers.count(), 0)

        foreign_user = get_user_model().objects.create_user(
            username="foreign-assessment-user@example.com", password="secret123"
        )
        StudentProfile.objects.create(
            user=foreign_user, onboarding_completed=True
        )
        self.client.force_login(foreign_user)
        self.assertEqual(self.client.post("/assessment/", payload).status_code, 404)
        draft.refresh_from_db()
        self.assertFalse(draft.is_completed)
        self.assertEqual(draft.answers.count(), 0)

        token = csrf_client.cookies["csrftoken"].value
        valid = csrf_client.post(
            "/assessment/", payload, HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(valid.status_code, 302)
        draft.refresh_from_db()
        self.assertTrue(draft.is_completed)
        self.assertEqual(draft.answers.count(), len(question_ids))

        csrf_client.get("/assessment/")
        denied_restart = csrf_client.post(
            "/assessment/", {"action": "restart"}
        )
        self.assertEqual(denied_restart.status_code, 403)
        restarted = csrf_client.post(
            "/assessment/",
            {"action": "restart"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(restarted.status_code, 302)
        self.assertTrue(
            AssessmentAttempt.objects.filter(
                user=student, is_draft=True, is_explicit_restart=True
            ).exists()
        )

    def test_assessment_submission_rounds_half_up(self):
        student = self._create_onboarded_student()
        questions = [
            Question.objects.create(
                question_text=f"Rounding question {index}",
                option_a="Correct",
                option_b="Wrong",
                option_c="Wrong",
                option_d="Wrong",
                correct_answer="A",
                skill="python",
                difficulty="beginner",
            )
            for index in range(8)
        ]
        payload = {"question_id": [str(question.id) for question in questions]}
        payload.update({f"question_{question.id}": "B" for question in questions})
        payload[f"question_{questions[0].id}"] = "A"
        draft = self.client.get("/assessment/").context["attempt"]
        payload["attempt_id"] = str(draft.id)
        self.client.post("/assessment/", payload)

        attempt = AssessmentAttempt.objects.get(user=student)
        self.assertEqual(attempt.correct_answers, 1)
        self.assertEqual(attempt.total_questions, 8)
        self.assertEqual(attempt.score, 13)

    def test_incomplete_assessment_submission_remains_resumable(self):
        self._create_onboarded_student()
        questions = [
            Question.objects.create(
                question_text=f"Incomplete assessment question {index}",
                option_a="A", option_b="B", option_c="C", option_d="D",
                correct_answer="A", skill="python", difficulty="beginner",
            )
            for index in range(2)
        ]
        draft = self.client.get("/assessment/").context["attempt"]
        response = self.client.post(
            "/assessment/",
            {
                "attempt_id": str(draft.id),
                "question_id": [str(q.id) for q in questions],
                f"question_{questions[0].id}": "A",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please answer every assessment question")
        self.assertEqual(AssessmentAttempt.objects.filter(is_completed=True).count(), 0)
        self.assertEqual(AssessmentAttempt.objects.count(), 1)
        resumed = self.client.get("/assessment/")
        self.assertEqual(resumed.context["attempt"].id, draft.id)
        self.assertEqual(resumed.context["attempt"].question_ids, draft.question_ids)
        malformed = self.client.post(
            "/assessment/",
            {
                "attempt_id": str(draft.id),
                "question_id": "not-a-number",
                "question_not-a-number": "A",
            },
        )
        self.assertEqual(malformed.status_code, 200)
        self.assertEqual(AssessmentAttempt.objects.count(), 1)

    def test_selected_career_persists_across_dashboard_roadmap_and_missions(self):
        student = self._create_onboarded_student()
        response = self.client.post("/roadmap/", {"career": "Data Analyst"})
        self.assertRedirects(response, "/roadmap/")
        self.assertEqual(
            StudentProfile.objects.get(user=student).career_goal,
            "Data Analyst",
        )
        for path in ("/dashboard/", "/roadmap/", "/missions/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Data Analyst")

        self.assertTrue(
            MissionProgress.objects.filter(
                user=student, career_goal="Data Analyst"
            ).exists()
        )

    def test_get_career_selection_is_saved_for_older_roadmap_forms(self):
        student = self._create_onboarded_student("Cloud Engineer")
        response = self.client.get("/roadmap/?career=Data%20Analyst")
        self.assertRedirects(response, "/roadmap/")
        self.assertEqual(
            StudentProfile.objects.get(user=student).career_goal,
            "Data Analyst",
        )
        self.assertContains(self.client.get("/dashboard/"), "Data Analyst")

    def test_cybersecurity_alias_is_saved_and_used_consistently(self):
        student = self._create_onboarded_student("Cybersecurity")
        self.assertEqual(
            StudentProfile.objects.get(user=student).career_goal,
            "Cybersecurity Analyst",
        )
        for path in ("/dashboard/", "/roadmap/", "/missions/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Cybersecurity Analyst")
        profile = StudentProfile.objects.get(user=student)
        profile.career_goal = "Penetration Testing"
        profile.save(update_fields=["career_goal", "updated_at"])
        self.assertEqual(
            StudentProfile.objects.get(user=student).career_goal,
            "Cybersecurity Analyst",
        )

    def test_mission_completion_xp_and_progress_are_persisted_per_career(self):
        student = self._create_onboarded_student("Data Analyst")
        self.client.get("/missions/")
        data_mission = MissionProgress.objects.get(
            user=student,
            career_goal="Data Analyst",
            title="Python Fundamentals",
        )
        detail_url = (
            f"/missions/start/?mission={data_mission.title.replace(' ', '%20')}"
            f"&record_id={data_mission.id}"
        )
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200)
        quiz_answers = {
            question["id"]: str(question["correct"])
            for question in detail.context["questions"]
        }
        response = self.client.post(detail_url, quiz_answers)
        data_mission.refresh_from_db()
        self.assertTrue(data_mission.completed)
        self.assertEqual(response.context["result"]["score"], 10)
        attempts_after_completion = MissionQuizAttempt.objects.filter(
            user=student, mission=data_mission
        ).count()
        self.client.post(detail_url, quiz_answers)
        self.assertEqual(
            MissionQuizAttempt.objects.filter(
                user=student, mission=data_mission
            ).count(),
            attempts_after_completion,
        )

        dashboard = self.client.get("/dashboard/")
        self.assertContains(dashboard, str(data_mission.xp))
        self.assertContains(dashboard, "1/20 missions")
        self.assertEqual(LearningProgress.objects.get(user=student).total_xp, data_mission.xp)
        self.assertEqual(LearningProgress.objects.get(user=student).current_streak, 1)

        self.client.post("/roadmap/", {"career": "AI/ML Engineer"})
        self.client.get("/missions/")
        ai_mission = MissionProgress.objects.get(
            user=student,
            career_goal="AI/ML Engineer",
            title="Python Fundamentals",
        )
        self.assertNotEqual(data_mission.id, ai_mission.id)
        self.assertFalse(ai_mission.completed)

    def test_all_careers_have_ten_projects_three_levels_questions_and_roles(self):
        for career in CAREER_CHOICES:
            with self.subTest(career=career):
                projects = projects_for_career(career)
                self.assertEqual(len(projects), 10)
                self.assertEqual(
                    {level: sum(p["level"] == level for p in projects) for level in (
                        "Beginner", "Intermediate", "Advanced"
                    )},
                    {"Beginner": 5, "Intermediate": 3, "Advanced": 2},
                )
                interview_levels = interviews_for_career(career)
                self.assertEqual(
                    set(interview_levels),
                    {"Beginner", "Intermediate", "Advanced"},
                )
                for level_questions in interview_levels.values():
                    self.assertEqual(
                        sum(q["type"] == "technical" for q in level_questions), 2
                    )
                    self.assertEqual(
                        sum(q["type"] == "behavioral" for q in level_questions), 1
                    )
                self.assertTrue(job_roles_for_career(career))

                student = self._create_onboarded_student(career)
                project_page = self.client.get("/projects/")
                self.assertEqual(project_page.status_code, 200)
                self.assertEqual(len(project_page.context["project_cards"]), 10)
                for level, expected_count in (
                    ("Beginner", 5), ("Intermediate", 3), ("Advanced", 2)
                ):
                    filtered = self.client.get(
                        f"/projects/?difficulty={level}"
                    )
                    self.assertEqual(
                        len(filtered.context["project_cards"]),
                        expected_count,
                    )
                interview_page = self.client.get("/interviews/?level=Advanced")
                self.assertEqual(interview_page.status_code, 200)
                self.assertEqual(interview_page.context["selected_level"], "Advanced")
                self.assertEqual(len(interview_page.context["interview_questions"]), 3)
                jobs_page = self.client.get("/jobs/")
                self.assertEqual(jobs_page.status_code, 200)
                self.assertTrue(jobs_page.context["job_roles"])

    def test_interview_answers_reload_and_are_isolated_by_user_and_career(self):
        first_student = self._create_onboarded_student("Data Analyst")
        page = self.client.get("/interviews/?level=Beginner")
        question = next(
            q for q in page.context["interview_questions"]
            if q["type"] == "technical"
        )
        response = self.client.post(
            "/interviews/",
            {
                "action": "save_answer",
                "question_key": question["key"],
                "level": "Beginner",
                "answer": "I would validate the source rows and explain my assumptions.",
                "self_rating": "4",
                "feedback": "Add one concrete example.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        saved = InterviewAnswer.objects.get(
            user=first_student,
            career_goal="Data Analyst",
            question_key=question["key"],
        )
        self.assertEqual(saved.self_rating, 4)
        page = self.client.get("/interviews/?level=Beginner")
        reloaded = next(q for q in page.context["interview_questions"] if q["key"] == question["key"])
        self.assertEqual(reloaded["saved"].answer, saved.answer)

        behavioral = next(
            q for q in page.context["interview_questions"]
            if q["type"] == "behavioral"
        )
        self.client.post(
            "/interviews/",
            {
                "action": "save_answer",
                "question_key": behavioral["key"],
                "level": "Beginner",
                "answer": "Situation: ... Task: ... Action: ... Result: ...",
                "self_rating": "3",
                "feedback": "Add measurable detail.",
            },
        )
        page = self.client.get("/interviews/?level=Beginner")
        behavioral_reloaded = next(
            q for q in page.context["interview_questions"]
            if q["key"] == behavioral["key"]
        )
        self.assertIn("Situation:", behavioral_reloaded["saved"].answer)

        second_student = self._create_onboarded_student("Data Analyst")
        page = self.client.get("/interviews/?level=Beginner")
        other_question = next(q for q in page.context["interview_questions"] if q["key"] == question["key"])
        self.assertIsNone(other_question["saved"])

        self.client.force_login(first_student)
        self.client.post("/roadmap/", {"career": "Cloud Engineer"})
        page = self.client.get("/interviews/?level=Beginner")
        self.assertFalse(any(q.get("saved") for q in page.context["interview_questions"]))
        self.assertEqual(
            InterviewAnswer.objects.filter(user=first_student, career_goal="Data Analyst").count(),
            2,
        )
        self.assertEqual(InterviewAnswer.objects.filter(user=second_student).count(), 0)

    def test_interview_day_progress_persists_and_is_career_scoped(self):
        student = self._create_onboarded_student("Android Developer")
        response = self.client.post(
            "/interviews/",
            {
                "action": "complete_day",
                "day_number": "1",
                "level": "Beginner",
                "completed": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        saved = InterviewDayProgress.objects.get(
            user=student, career_goal="Android Developer", day_number=1
        )
        self.assertTrue(saved.completed)
        page = self.client.get("/interviews/")
        self.assertTrue(page.context["day_plan"][0]["progress"].completed)

        self.client.post("/roadmap/", {"career": "Data Analyst"})
        page = self.client.get("/interviews/")
        self.assertIsNone(page.context["day_plan"][0]["progress"])
        self.assertEqual(
            InterviewDayProgress.objects.filter(user=student, completed=True).count(),
            1,
        )

    def test_career_switch_updates_all_learning_pages(self):
        student = self._create_onboarded_student("Cloud Engineer")
        self.client.post("/roadmap/", {"career": "Android Developer"})
        paths = (
            ("/dashboard/", "Android Developer"),
            ("/roadmap/", "Android Developer"),
            ("/missions/", "Android Developer"),
            ("/practice/", "Android Developer"),
            ("/projects/", "Android Developer"),
            ("/interviews/", "Android Developer"),
            ("/jobs/", "Android Developer"),
            ("/progress/", "Android Developer"),
        )
        for path, career in paths:
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertEqual(page.status_code, 200)
                if page.context and "career_goal" in page.context:
                    self.assertEqual(page.context["career_goal"], career)
                else:
                    self.assertContains(page, career)
        self.assertEqual(
            StudentProfile.objects.get(user=student).career_goal,
            "Android Developer",
        )

    def test_project_career_filter_updates_the_saved_career(self):
        student = self._create_onboarded_student("Cloud Engineer")
        response = self.client.post(
            "/projects/",
            {"career": "Data Analyst", "difficulty": "Intermediate"},
        )
        self.assertRedirects(response, "/projects/?difficulty=Intermediate")
        self.assertEqual(
            StudentProfile.objects.get(user=student).career_goal,
            "Data Analyst",
        )
        page = self.client.get(response.url)
        self.assertEqual(len(page.context["project_cards"]), 3)

    def test_csv_preview_requires_confirmation_before_creating_questions(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="csv-admin@example.com",
            email="csv-admin@example.com",
            is_staff=True,
        )
        staff.set_password("secret123")
        staff.save()
        self.client.force_login(staff)
        initial_question_count = Question.objects.count()
        csv_data = (
            "question_text,option_a,option_b,option_c,option_d,correct_answer,skill,difficulty,explanation\n"
            "What is Django?,Python,Ruby,Go,Rust,A,django,beginner,A framework\n"
        ).encode()

        response = self.client.post(
            "/admin/main/questions/",
            {
                "action": "preview_csv",
                "question_file": SimpleUploadedFile(
                    "questions.csv", csv_data, content_type="text/csv"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What is Django?")
        self.assertEqual(Question.objects.count(), initial_question_count)

        response = self.client.post(
            "/admin/main/questions/",
            {"action": "confirm_csv_import"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), initial_question_count + 1)

    def test_invalid_csv_does_not_create_questions(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="invalid-csv-admin@example.com",
            email="invalid-csv-admin@example.com",
            is_staff=True,
        )
        staff.set_password("secret123")
        staff.save()
        self.client.force_login(staff)
        initial_question_count = Question.objects.count()

        response = self.client.post(
            "/admin/main/questions/",
            {
                "action": "preview_csv",
                "question_file": SimpleUploadedFile(
                    "questions.csv",
                    b"question_text,option_a\nBroken,Only two columns\n",
                    content_type="text/csv",
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Missing CSV columns")
        self.assertEqual(Question.objects.count(), initial_question_count)

    def test_csv_accepts_common_easy_medium_hard_difficulty_labels(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="difficulty-csv-admin@example.com",
            email="difficulty-csv-admin@example.com",
            is_staff=True,
        )
        staff.set_password("secret123")
        staff.save()
        self.client.force_login(staff)
        initial_question_count = Question.objects.count()
        csv_data = (
            "question_text,option_a,option_b,option_c,option_d,correct_answer,skill,difficulty\n"
            "Easy question,A,B,C,D,A,python,Easy\n"
            "Medium question,A,B,C,D,B,python,Medium\n"
            "Hard question,A,B,C,D,C,python,Hard\n"
        ).encode()

        response = self.client.post(
            "/admin/main/questions/",
            {
                "action": "preview_csv",
                "question_file": SimpleUploadedFile(
                    "python_50_questions.csv", csv_data, content_type="text/csv"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review 3 questions")
        self.assertEqual(Question.objects.count(), initial_question_count)

    def test_roadmap_test_submits_and_appears_in_admin_student_analytics(self):
        User = get_user_model()
        student = User.objects.create_user(
            username="roadmap-student@example.com",
            email="roadmap-student@example.com",
            password="secret123",
        )
        StudentProfile.objects.create(
            user=student,
            onboarding_completed=True,
            career_goal="Full Stack Developer",
        )
        staff = User.objects.create_user(
            username="roadmap-admin@example.com",
            email="roadmap-admin@example.com",
            password="secret123",
            is_staff=True,
        )
        question = Question.objects.create(
            question_text="Roadmap test question",
            option_a="Correct",
            option_b="Wrong",
            option_c="Wrong",
            option_d="Wrong",
            correct_answer="A",
            skill="python",
            difficulty="beginner",
        )

        self.client.force_login(student)
        response = self.client.get("/roadmap/test/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Roadmap Skill Test")
        self.assertContains(response, "Roadmap test question")
        draft = response.context["attempt"]

        response = self.client.post(
            "/roadmap/test/",
            {
                "attempt_id": str(draft.id),
                "question_id": str(question.id),
                f"question_{question.id}": "A",
            },
        )
        attempt = AssessmentAttempt.objects.get(user=student)
        self.assertRedirects(
            response,
            f"/assessment/result/{attempt.id}/",
        )
        self.assertEqual(attempt.score, 100)
        self.assertTrue(attempt.is_completed)

        self.client.force_login(staff)
        response = self.client.get(f"/admin/main/users/{student.id}/")
        self.assertContains(response, "100%")
        self.assertContains(response, "1 attempt")

    def test_learning_pages_render_after_onboarding(self):
        User = get_user_model()
        student = User.objects.create_user(
            username="learning-pages@example.com",
            email="learning-pages@example.com",
            password="secret123",
        )
        StudentProfile.objects.create(
            user=student,
            onboarding_completed=True,
            skills=["Python"],
        )
        self.client.force_login(student)
        for path, heading in (
            ("/practice/", "Practice"),
            ("/projects/", "Projects"),
            ("/jobs/", "Jobs"),
            ("/interviews/", "Interview Prep"),
            ("/progress/", "Your progress"),
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)

    def test_new_user_logs_in_and_is_sent_to_onboarding(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="secret123",
            first_name="New",
        )

        StudentProfile.objects.get_or_create(user=user)

        response = self.client.post(
            "/",
            {"email": "newuser@example.com", "password": "secret123"},
            follow=True,
        )

        self.assertRedirects(response, "/onboarding/")

    def test_onboarding_submission_redirects_to_initial_assessment(self):
        User = get_user_model()
        Question.objects.create(
            question_text="Initial onboarding assessment question",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A", skill="python", difficulty="beginner",
        )
        user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="secret123",
            first_name="Student",
        )

        self.client.force_login(user)

        response = self.client.post(
            "/onboarding/",
            {
                "education": "BTECH",
                "year": "2nd Year",
                "specialization": "Computer Science & Engineering",
                "career_goal": "Software Engineer",
                "skills": ["Python", "JavaScript", "SQL"],
                "skill_level": "Intermediate",
                "study_time": "60",
                "preparation": "Placement",
            },
            follow=True,
        )

        self.assertRedirects(response, "/assessment/")
        profile = StudentProfile.objects.get(user=user)
        self.assertTrue(profile.onboarding_completed)
        self.assertContains(response, "Initial onboarding assessment question")
        self.assertEqual(
            AssessmentAttempt.objects.filter(
                user=user, is_completed=False, attempt_type="baseline"
            ).count(),
            1,
        )

    def test_incomplete_users_are_warned_before_opening_app_pages(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="incomplete@example.com",
            email="incomplete@example.com",
            password="secret123",
        )

        self.client.force_login(user)

        for path in ("/dashboard/", "/roadmap/", "/missions/", "/assessment/", "/profile/"):
            with self.subTest(path=path):
                response = self.client.get(path, follow=True)
                self.assertRedirects(response, "/onboarding/")
                self.assertContains(
                    response,
                    "Please complete your onboarding profile before accessing this page.",
                )

    def test_profile_page_renders_saved_signup_and_onboarding_data(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="profile@example.com",
            email="profile@example.com",
            password="secret123",
            first_name="Profile Student",
        )
        StudentProfile.objects.create(
            user=user,
            education="BTECH",
            year="Final Year",
            specialization="Computer Science & Engineering",
            career_goal="Software Engineer",
            skills=["Python", "Django"],
            skill_level="Intermediate",
            study_time=60,
            preparation="Placement",
            onboarding_completed=True,
        )

        self.client.force_login(user)
        response = self.client.get("/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile@example.com")
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Django")
        self.assertNotContains(response, "```")

    def test_staff_admin_workspace_shows_users_and_adds_questions(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="secret123",
            is_staff=True,
        )
        learner = User.objects.create_user(
            username="learner@example.com",
            email="learner@example.com",
            password="secret123",
            first_name="Learner",
        )
        StudentProfile.objects.create(
            user=learner,
            career_goal="Backend Developer",
            onboarding_completed=True,
        )
        LearningProgress.objects.create(
            user=learner,
            total_xp=120,
            career_progress=35,
        )
        completed_attempt = AssessmentAttempt.objects.create(
            user=learner,
            total_questions=4,
            correct_answers=3,
            score=75,
            is_completed=True,
            question_ids=[1, 2, 3, 4],
            completed_at=timezone.now(),
        )

        self.client.force_login(staff)
        response = self.client.get("/admin/main/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "learner@example.com")
        self.assertContains(response, "Backend Developer")
        self.assertContains(response, "Question bank")
        self.assertContains(response, "Edit profile")
        self.assertContains(response, "learner@example.com")
        self.assertEqual(response.context["user_rows"][0]["latest_attempt"], completed_attempt)

        response = self.client.get(f"/admin/main/users/{learner.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student analytics")
        self.assertContains(response, "Backend Developer")

        response = self.client.get("/admin/main/users/")
        self.assertContains(response, "Registered students")
        self.assertContains(response, "learner@example.com")
        self.assertNotContains(response, "Add question")

        response = self.client.post(
            "/admin/main/",
            {
                "question_text": "Which language is used by Django?",
                "option_a": "Python",
                "option_b": "Ruby",
                "option_c": "Go",
                "option_d": "Rust",
                "correct_answer": "A",
                "skill": "django",
                "difficulty": "beginner",
                "explanation": "Django is a Python web framework.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Question.objects.filter(
                question_text="Which language is used by Django?"
            ).exists()
        )

        response = self.client.get("/admin/main/questions/")
        self.assertContains(response, "Editable assessment questions")
        self.assertContains(response, "Which language is used by Django?")

        response = self.client.get(
            f"/admin/main/questions/{Question.objects.get(question_text='Which language is used by Django?').id}/"
        )
        self.assertContains(response, "Times answered")

    def test_staff_can_edit_admin_profile(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="profile-admin@example.com",
            email="profile-admin@example.com",
            password="secret123",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.post(
            "/admin/main/profile/edit/",
            {
                "first_name": "Updated",
                "last_name": "Admin",
                "email": "updated-admin@example.com",
            },
            follow=True,
        )

        self.assertRedirects(response, "/admin/main/")
        staff.refresh_from_db()
        self.assertEqual(staff.get_full_name(), "Updated Admin")
        self.assertEqual(staff.email, "updated-admin@example.com")

    def test_overview_keeps_all_onboarding_questions_in_scrollable_section(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="onboarding-admin@example.com",
            email="onboarding-admin@example.com",
            password="secret123",
            is_staff=True,
        )
        for index in range(9):
            OnboardingQuestion.objects.create(
                question_text=f"Onboarding question {index}",
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
                correct_answer="A",
                skill="python",
                difficulty="beginner",
            )

        self.client.force_login(staff)
        response = self.client.get("/admin/main/")

        self.assertContains(response, "Onboarding question 0")
        self.assertContains(response, "Onboarding question 8")
        self.assertContains(response, "onboarding-questions")

    def test_non_staff_users_cannot_open_admin_workspace(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="secret123",
        )

        self.client.force_login(user)
        response = self.client.get("/admin/main/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_valid_admin_key_opens_admin_workspace_without_password(self):
        response = self.client.post(
            "/",
            {"account_type": "admin", "admin_key": "qwerty"},
            follow=True,
        )

        self.assertRedirects(response, "/admin/main/")
        self.assertTrue(response.wsgi_request.user.is_staff)

    def test_invalid_admin_key_shows_error_and_does_not_log_in(self):
        response = self.client.post(
            "/",
            {"account_type": "admin", "admin_key": "wrong-key"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid admin key.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_page_has_student_and_admin_modes(self):
        response = self.client.get("/")

        self.assertContains(response, "Student login")
        self.assertContains(response, "Admin / teacher")
        self.assertContains(response, "Admin access key")
