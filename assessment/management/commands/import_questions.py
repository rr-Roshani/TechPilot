# import csv
# from pathlib import Path

# from django.core.management.base import BaseCommand
# from django.conf import settings
# from assessment.models import OnboardingQuestion


# class Command(BaseCommand):
#     help = "Import questions from a CSV file"

#     def add_arguments(self, parser):
#         parser.add_argument(
#             "--file",
#             default=str(settings.BASE_DIR / "assessment" / "questions.csv"),
#             help="Path to the questions CSV file",
#         )

#     def handle(self, *args, **options):
#         file_path = Path(options["file"])

#         if not file_path.is_file():
#             self.stdout.write(
#                 self.style.ERROR(
#                     f"CSV file not found: {file_path}"
#                 )
#             )
#             return

#         created = 0
#         skipped = 0

#         with open(
#             file_path,
#             "r",
#             encoding="utf-8-sig",
#             newline=""
#         ) as file:

#             reader = csv.DictReader(file)

#             for row in reader:

#                 question_text = row["question_text"].strip()

#                 if not question_text:
#                     skipped += 1
#                     continue

#                 if OnboardingQuestion.objects.filter(
#                     question_text=question_text
#                 ).exists():
#                     skipped += 1
#                     continue

#                 OnboardingQuestion.objects.create(
#                     question_text=question_text,
#                     option_a=row["option_a"].strip(),
#                     option_b=row["option_b"].strip(),
#                     option_c=row["option_c"].strip(),
#                     option_d=row["option_d"].strip(),
#                     correct_answer=row["correct_answer"].strip().upper(),
#                     skill=row["skill"].strip(),
#                     difficulty=row["difficulty"].strip(),
#                     explanation=row.get("explanation", "").strip(),
#                 )

#                 created += 1

#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"Import completed: {created} questions added, "
#                 f"{skipped} skipped."
#             )
#         )
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from assessment.models import Question


class Command(BaseCommand):
    help = "Import questions from a CSV file into the main Question bank"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=str(
                settings.BASE_DIR
                / "assessment"
                / "questions.csv"
            ),
            help="Path to the questions CSV file",
        )

    def handle(self, *args, **options):

        file_path = Path(options["file"])

        # -------------------------------------------------
        # CHECK CSV FILE
        # -------------------------------------------------

        if not file_path.is_file():
            self.stdout.write(
                self.style.ERROR(
                    f"CSV file not found: {file_path}"
                )
            )
            return

        created = 0
        updated = 0
        skipped = 0

        # -------------------------------------------------
        # VALID VALUES FROM MODEL
        # -------------------------------------------------

        valid_skills = {
            value
            for value, label in Question.SKILL_CHOICES
        }

        valid_difficulties = {
            value
            for value, label in Question.DIFFICULTY_CHOICES
        }

        valid_roadmaps = {
            value
            for value, label in Question.ROADMAP_CHOICES
        }

        # -------------------------------------------------
        # READ CSV
        # -------------------------------------------------

        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            # ---------------------------------------------
            # CHECK REQUIRED COLUMNS
            # ---------------------------------------------

            required_columns = {
                "question_text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_answer",
                "skill",
                "difficulty",
                "roadmap",
            }

            csv_columns = set(reader.fieldnames or [])

            missing_columns = required_columns - csv_columns

            if missing_columns:

                self.stdout.write(
                    self.style.ERROR(
                        "CSV is missing required columns: "
                        + ", ".join(sorted(missing_columns))
                    )
                )

                return

            # ---------------------------------------------
            # PROCESS QUESTIONS
            # ---------------------------------------------

            for row_number, row in enumerate(
                reader,
                start=2
            ):

                question_text = (
                    row.get("question_text", "")
                    .strip()
                )

                if not question_text:
                    skipped += 1
                    continue

                option_a = (
                    row.get("option_a", "")
                    .strip()
                )

                option_b = (
                    row.get("option_b", "")
                    .strip()
                )

                option_c = (
                    row.get("option_c", "")
                    .strip()
                )

                option_d = (
                    row.get("option_d", "")
                    .strip()
                )

                correct_answer = (
                    row.get("correct_answer", "")
                    .strip()
                    .upper()
                )

                skill = (
                    row.get("skill", "")
                    .strip()
                    .lower()
                )

                difficulty = (
                    row.get("difficulty", "")
                    .strip()
                    .lower()
                )

                roadmap = (
                    row.get("roadmap", "")
                    .strip()
                )

                explanation = (
                    row.get("explanation", "")
                    .strip()
                )

                # -----------------------------------------
                # BASIC VALIDATION
                # -----------------------------------------

                if not all(
                    [
                        option_a,
                        option_b,
                        option_c,
                        option_d,
                        correct_answer,
                        skill,
                        difficulty,
                        roadmap,
                    ]
                ):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Row {row_number} skipped: "
                            "missing required value."
                        )
                    )

                    skipped += 1
                    continue

                # -----------------------------------------
                # VALIDATE ANSWER
                # -----------------------------------------

                if correct_answer not in {
                    "A",
                    "B",
                    "C",
                    "D",
                }:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Row {row_number} skipped: "
                            f"invalid correct_answer "
                            f"'{correct_answer}'."
                        )
                    )

                    skipped += 1
                    continue

                # -----------------------------------------
                # VALIDATE SKILL
                # -----------------------------------------

                if skill not in valid_skills:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Row {row_number} skipped: "
                            f"invalid skill '{skill}'. "
                            f"Allowed values: "
                            f"{', '.join(sorted(valid_skills))}"
                        )
                    )

                    skipped += 1
                    continue

                # -----------------------------------------
                # VALIDATE DIFFICULTY
                # -----------------------------------------

                if difficulty not in valid_difficulties:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Row {row_number} skipped: "
                            f"invalid difficulty "
                            f"'{difficulty}'. "
                            f"Allowed values: "
                            f"{', '.join(sorted(valid_difficulties))}"
                        )
                    )

                    skipped += 1
                    continue

                # -----------------------------------------
                # VALIDATE ROADMAP
                # -----------------------------------------

                if roadmap not in valid_roadmaps:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Row {row_number} skipped: "
                            f"invalid roadmap "
                            f"'{roadmap}'. "
                            f"Allowed values: "
                            f"{', '.join(valid_roadmaps)}"
                        )
                    )

                    skipped += 1
                    continue

                # -----------------------------------------
                # CREATE OR UPDATE QUESTION
                # -----------------------------------------

                question, was_created = (
                    Question.objects.update_or_create(
                        question_text=question_text,
                        defaults={
                            "option_a": option_a,
                            "option_b": option_b,
                            "option_c": option_c,
                            "option_d": option_d,
                            "correct_answer": correct_answer,
                            "skill": skill,
                            "roadmap": roadmap,
                            "difficulty": difficulty,
                            "explanation": explanation,
                        },
                    )
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "       QUESTION IMPORT COMPLETED"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            f"Created : {created}"
        )

        self.stdout.write(
            f"Updated : {updated}"
        )

        self.stdout.write(
            f"Skipped : {skipped}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )