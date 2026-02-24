from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import *
from django.contrib import messages
import pandas as pd
from django.shortcuts import render
from .ai_service import analyze_performance, generate_questions

# ---------------- HOME ----------------
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        if hasattr(request.user, 'teacher'):
            _ = request.user.teacher
            return redirect('teacher_dashboard')
    except ObjectDoesNotExist:
        pass

    try:
        if hasattr(request.user, 'student'):
            _ = request.user.student
            return redirect('student_dashboard')
    except ObjectDoesNotExist:
        pass

    return redirect('login')
from django.core.exceptions import ObjectDoesNotExist

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter both username and password")
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Check if Student
            try:
                _ = user.student
                return redirect('student_dashboard')
            except Student.DoesNotExist:
                pass

            # Check if Teacher
            try:
                _ = user.teacher
                return redirect('teacher_dashboard')
            except Teacher.DoesNotExist:
                pass

            messages.warning(request, "User role not assigned. Contact admin.")
            return redirect('login')

        else:
            messages.error(request, "Invalid Credentials")
            return render(request, 'login.html')

    return render(request, 'login.html')
# ---------------- LOGOUT ----------------
def user_logout(request):
    logout(request)
    return redirect('login')

# ===============================
# TEACHER DASHBOARD
# ===============================
@login_required
def teacher_dashboard(request):
    teacher = request.user.teacher
    quizzes = Quiz.objects.filter(teacher=teacher).order_by('-created_at')

    quiz_previews = []
    for quiz in quizzes:
        # Split questions by line (assuming each question is on a new line)
        questions_list = quiz.questions.split("\n") if quiz.questions else []
        quiz_previews.append({
            "quiz": quiz,
            "questions_list": questions_list
        })

    return render(request, "teacher/dashboard.html", {
        "quiz_previews": quiz_previews
    })
# ---------------- Add Marks via Excel ----------------

def upload_marks(request):
    if request.method == "POST":
        class_section_id = request.POST['class_section']
        file = request.FILES['file']

        # Read Excel
        df = pd.read_excel(file)
        # Normalize headers to avoid spaces/case issues
        df.columns = df.columns.str.strip().str.lower()

        required_columns = ['student_id', 'subject', 'marks', 'total']
        for col in required_columns:
            if col not in df.columns:
                messages.error(request, f"Excel file must contain '{col}' column.")
                return redirect('upload_marks')

        for _, row in df.iterrows():
            student_id = row['student_id']
            subject = row['subject']
            marks = row['marks']
            total = row['total']

            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                messages.warning(request, f"Student with ID {student_id} not found.")
                continue

            percentage = (marks / total) * 100
            is_failed = percentage < 40  # assuming passing marks = 40%

            # Save or update
            ExamResult.objects.update_or_create(
                student=student,
                class_section_id=class_section_id,
                subject=subject,
                defaults={
                    'marks': marks,
                    'total': total,
                    'percentage': percentage,
                    'is_failed': is_failed
                }
            )

        messages.success(request, "Marks uploaded successfully.")
        return redirect('upload_marks')

    else:
        sections = ClassSection.objects.all()
        return render(request, 'teacher/upload_marks.html', {'sections': sections})

# ---------------- Generate Remedial Quiz ----------------
@login_required
def generate_remedial_quiz(request):
    teacher = request.user.teacher
    class_sections = ClassSection.objects.filter(teacher=teacher)

    if request.method == "POST":
        subject = request.POST.get("subject")
        class_section_id = request.POST.get("class_section")

        syllabus_file = request.FILES.get('syllabus_file')
        notes_file = request.FILES.get('notes_file')
        past_questions_file = request.FILES.get('past_questions_file')

        class_section = get_object_or_404(
            ClassSection,
            id=class_section_id,
            teacher=teacher
        )

        syllabus_text = syllabus_file.read().decode('utf-8', errors='ignore') if syllabus_file else ""
        notes_text = notes_file.read().decode('utf-8', errors='ignore') if notes_file else ""
        past_questions_text = past_questions_file.read().decode('utf-8', errors='ignore') if past_questions_file else ""

        try:
            generated_content = generate_questions(
                syllabus_text,
                notes_text,
                past_questions_text
            )
        except Exception as e:
            messages.error(request, f"AI generation failed: {str(e)}")
            return redirect("generate_quiz") 

        quiz = Quiz.objects.create(
            teacher=teacher,
            class_section=class_section,
            subject=subject,
            questions=generated_content
        )

        # ✅ Correct student filtering
        students = Student.objects.filter(class_name=class_section)

        for student in students:
            QuizAssignment.objects.create(
                student=student,
                question=quiz
            )

        messages.success(request, "Quiz generated and assigned successfully!")
        return redirect("teacher_dashboard")

    return render(request, "teacher/generate_remedial_quiz.html", {
        "class_sections": class_sections
    })
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .pdf_utils import *

@login_required
def view_quiz_pdf(request, quiz_id):
    teacher = request.user.teacher
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=teacher)
    return generate_quiz_pdf(quiz)
# Your AI function
@login_required
def assign_remedial_quiz(request):
    teacher = request.user.teacher
    sections = ClassSection.objects.filter(teacher=teacher)

    if request.method == "POST":
        quiz_subject = request.POST.get("subject")  # match your form field
        class_section_id = request.POST.get("class_section")
        selected_text_questions = request.POST.getlist("questions_text")  # text from dynamic questions

        class_section = get_object_or_404(ClassSection, id=class_section_id)

        # Convert selected text to ShortQuestion objects
        questions = [ShortQuestion(text=q_text) for q_text in selected_text_questions]

        # Create quiz (store questions as text)
        quiz = Quiz.objects.create(
            teacher=teacher,
            class_section=class_section,
            subject=quiz_subject,
            questions="\n".join([q.text for q in questions])
        )

        # Assign to students
        students = Student.objects.filter(class_name=class_section)
        for student in students:
            QuizAssignment.objects.create(
                question=quiz,
                student=student
            )

        messages.success(request, f"Quiz '{quiz_subject}' assigned successfully!")
        return redirect("teacher_dashboard")

    # GET: Generate AI questions dynamically
    raw_questions_text = generate_questions("syllabus text here", "notes text here")
    dynamic_questions = [ShortQuestion(text=q.strip()) for q in raw_questions_text.split("\n") if q.strip()]

    return render(request, "teacher/assign_remedial_quiz.html", {
        "class_sections": sections,  # <-- use 'class_sections' to match your template
        "questions": dynamic_questions
    })
@login_required
def student_performance_report(request):
    teacher = request.user.teacher
    sections = ClassSection.objects.filter(teacher=teacher)
    report = None
    predictions = None  # will store predicted results

    if request.method == "POST":
        # Selected class section
        section = ClassSection.objects.get(id=request.POST['class_section'])
        
        # Get all exam results for this section
        report = ExamResult.objects.filter(class_section=section)

        # Predict future result for each student
        predictions = []
        students = Student.objects.filter(examresult__class_section=section).distinct()
        for student in students:
            student_results = report.filter(student=student)

            if student_results.exists():
                # Calculate average percentage
                avg_percentage = student_results.aggregate(avg_perc=models.Avg('percentage'))['avg_perc']
                
                # Simple prediction: assume student maintains same performance
                predicted_percentage = avg_percentage
                
                # Predict pass/fail based on threshold (40%)
                predicted_status = "Failed" if predicted_percentage < 40 else "Passed"

                predictions.append({
                    "student": student,
                    "predicted_percentage": round(predicted_percentage, 2),
                    "predicted_status": predicted_status
                })
            else:
                # No previous result, cannot predict
                predictions.append({
                    "student": student,
                    "predicted_percentage": None,
                    "predicted_status": "No Data"
                })

    return render(request, "teacher/performance_report.html", {
        "sections": sections,
        "report": report,
        "predictions": predictions
    })
from .ai_service import generate_questions   # or from .utils import generate_questions

@login_required
def generate_question(request):
    teacher = request.user.teacher
    class_sections = ClassSection.objects.filter(teacher=teacher)

    if request.method == "POST":
        subject = request.POST.get("subject")
        class_section_id = request.POST.get("class_section")

        syllabus_file = request.FILES.get("syllabus_file")
        notes_file = request.FILES.get("notes_file")
        past_questions_file = request.FILES.get("past_questions_file")

        class_section = get_object_or_404(ClassSection, id=class_section_id, teacher=teacher)

        syllabus_text = syllabus_file.read().decode('utf-8', errors='ignore') if syllabus_file else ""
        notes_text = notes_file.read().decode('utf-8', errors='ignore') if notes_file else ""
        past_questions_text = past_questions_file.read().decode('utf-8', errors='ignore') if past_questions_file else ""

        # AI generates questions
        generated_content = generate_questions(notes_text, past_questions_text)

        # Split MCQs and short questions
        mcqs_text = ""
        short_questions_text = ""
        if "MCQs:" in generated_content and "Very Short Answer Questions:" in generated_content:
            mcqs_text = generated_content.split("Very Short Answer Questions:")[0].replace("MCQs:", "").strip()
            short_questions_text = generated_content.split("Very Short Answer Questions:")[1].strip()
        else:
            mcqs_text = generated_content

        # Convert MCQs & Short Questions to lists
        mcqs_list = [q.strip() for q in mcqs_text.split("\n") if q.strip()]
        short_questions_list = [q.strip() for q in short_questions_text.split("\n") if q.strip()]

        # Save MCQs Quiz
        mcq_quiz = Quiz.objects.create(
            teacher=teacher,
            class_section=class_section,
            subject=subject,
            questions="\n".join(mcqs_list)
        )

        # Save Short Questions Quiz (optional)
        short_quiz = None
        if short_questions_list:
            short_quiz = Quiz.objects.create(
                teacher=teacher,
                class_section=class_section,
                subject=subject,
                questions="\n".join(short_questions_list)
            )

        # Assign to students
        students = Student.objects.filter(class_name=class_section)
        for student in students:
            QuizAssignment.objects.create(student=student, question=mcq_quiz)
            if short_quiz:
                QuizAssignment.objects.create(student=student, question=short_quiz)

        messages.success(request, "AI questions (MCQs + Short Questions) generated and assigned successfully!")
        return redirect("teacher_dashboard")

    return render(request, "teacher/generate_question.html", {
        "class_sections": class_sections,
        "mcqs_list": [],
        "short_questions_list": []
    })
# ===============================
# STUDENT SIDE
# ===============================

@login_required
def student_dashboard(request):
    student = Student.objects.get(user=request.user)

    quiz_assignments = QuizAssignment.objects.filter(student=student)\
        .select_related('question', 'question__teacher')\
        .prefetch_related('question').order_by('-question__created_at')

    context = {
        'quiz_assignments': quiz_assignments,
    }
    return render(request, 'student/dashboard.html', context)
@login_required
def student_assigned_questions(request):
    student = request.user.student
    assignments = QuizAssignment.objects.filter(student=student, is_submitted=False)
    return render(request, "student/assigned_questions.html", {
        "question_assignments": assignments
    })

@login_required
def attempt_question(request, assignment_id):
    assignment = get_object_or_404(QuizAssignment, id=assignment_id, student=request.user.student)

    if request.method == "POST":
        answer = request.POST.get('answer')
        assignment.student_answer = answer
        assignment.is_submitted = True

        # Optional: simple scoring
        if assignment.question.correct_answer:
            assignment.score = 1 if answer.strip().lower() == assignment.question.correct_answer.strip().lower() else 0
        assignment.save()
        messages.success(request, "Answer submitted!")
        return redirect('student_assigned_questions')

    return render(request, "student/attempt_question.html", {"assignment": assignment})

@login_required
def view_quiz(request):
    assignment = QuizAssignment.objects.filter(
        student=request.user.student
    ).last()

    return render(request, "student/view_quiz.html", {
        "quiz": assignment.question if assignment else None
    })
@login_required
def student_assigned_quizzes(request):
    assignments = QuizAssignment.objects.filter(student=request.user.student)
    return render(request, "student/assigned_quizzes.html", {"assignments": assignments})


@login_required
def attempt_quiz(request, assignment_id):
    assignment = get_object_or_404(
        QuizAssignment,
        id=assignment_id,
        student=request.user.student
    )

    if request.method == "POST":
        answers = request.POST.get("answers")

        feedback = analyze_performance(
            assignment.question.questions,
            answers
        )

        assignment.student_answer = answers
        assignment.feedback = feedback
        assignment.score = 50  # Temporary scoring
        assignment.is_submitted = True
        assignment.save()

        messages.success(request, "Quiz submitted successfully!")
        return redirect("student_dashboard")

    return render(request, "student/attempt_quiz.html", {
        "assignment": assignment
    })
@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        answers = request.POST['answers']

        feedback = analyze_performance(
            quiz.questions,
            answers
        )

        quiz.feedback = feedback
        quiz.score = 50  # temporary scoring logic
        quiz.save()

        return redirect('student_dashboard')


@login_required
def submit_exam(request):
    if request.method == "POST":
        questions = request.POST.get("questions", [])
        answers = request.POST.get("answers", [])

        # Call your performance analysis function
        analysis = analyze_performance(questions, answers)

        # Render analysis page after submission
        return render(request, "student/analysis.html", {"analysis": analysis})
    
    else:
        # Handle GET request - maybe show a message or redirect
        # You cannot leave this empty
        return render(request, "student/analysis.html", {"analysis": None})
@login_required
def attempt_ai_question(request, assignment_id):
    assignment = get_object_or_404(QuizAssignment, id=assignment_id, student=request.user.student)

    if request.method == "POST":
        answer = request.POST.get("answer")
        assignment.student_answer = answer

        # Auto-check answer for MCQs
        correct_answer = assignment.question.correct_answer
        if correct_answer:
            assignment.score = 1 if answer.strip().lower() == correct_answer.strip().lower() else 0

        assignment.is_submitted = True
        assignment.save()
        messages.success(request, "Answer submitted!")
        return redirect("student_assigned_questions")

    return render(request, "student/attempt_ai_question.html", {"assignment": assignment})