# demo_create_users.py
# Place this file in your Django app folder (e.g., core/) and run using `python manage.py shell`

from django.contrib.auth.models import User
from core.models import Teacher, Student, ClassSection

# -----------------------------
# --- CREATE ADMIN USER ---
# -----------------------------
if not User.objects.filter(username="admin").exists():
    admin_user = User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin123"
    )
    print("Admin created:", admin_user.username)

# -----------------------------
# --- CREATE TEACHER USER ---
# -----------------------------
if not User.objects.filter(username="teacher1").exists():
    teacher_user = User.objects.create_user(
        username="teacher1",
        email="teacher1@example.com",
        password="teacher123",
        is_staff=True  # Teacher can access admin panel
    )
    teacher_obj = Teacher.objects.create(
        user=teacher_user,
        department="Computer Science",
        designation="Class Teacher"
    )
    print("Teacher created:", teacher_user.username)

    # Create ClassSection for this teacher
    if not ClassSection.objects.filter(name="10th Grade - A", teacher=teacher_obj).exists():
        section = ClassSection.objects.create(
            name="10th Grade - A",
            semester=1,
            teacher=teacher_obj
        )
        print("ClassSection created:", section.name)

# -----------------------------
# --- CREATE STUDENT USER ---
# -----------------------------
if not User.objects.filter(username="student1").exists():
    student_user = User.objects.create_user(
        username="student1",
        email="student1@example.com",
        password="student123",
        is_staff=False
    )

    # Assign student to class section
    section = ClassSection.objects.filter(name="10th Grade - A").first()
    if section is None:
        raise Exception("ClassSection '10th Grade - A' not found. Please create it first.")

    student_obj = Student.objects.create(
        user=student_user,
        roll_number="CS101",
        class_name=section.name  # link student to class name
    )
    print("Student created:", student_user.username, "in section:", section.name)