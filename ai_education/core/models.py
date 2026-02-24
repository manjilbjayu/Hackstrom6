# Create your models here.
from django.contrib.auth.models import User
from django.db import models

# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username
# models.py (User helper)
from django.contrib.auth.models import User

def get_user_role(user):
    try:
        if hasattr(user, 'student'):
            user.student
            return 'student'
    except Student.DoesNotExist:
        pass
    try:
        if hasattr(user, 'teacher'):
            user.teacher
            return 'teacher'
    except Teacher.DoesNotExist:
        pass
    return 'unknown'

# Student Model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20)
    class_name = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username

class ClassSection(models.Model): 
    name = models.CharField(max_length=50) # e.g., "10th Grade - A" 
    semester = models.IntegerField() 
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE) 
    def __str__(self):
        return f"{self.name} (Section {self.semester})"
class StudyMaterial(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    syllabus_file = models.FileField(upload_to='syllabus_files/')
    notes_file = models.FileField(upload_to='notes_files/')
    past_questions_file = models.FileField(upload_to='past_questions_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ExamResult(models.Model): 
    student = models.ForeignKey(Student, on_delete=models.CASCADE) 
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE) 
    subject = models.CharField(max_length=100)
    marks = models.FloatField() 
    total = models.FloatField() 
    percentage = models.FloatField() 
    is_failed = models.BooleanField(default=False) 
class Quiz(models.Model): 
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE) 
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100) 
    questions = models.TextField() 
    correct_answer = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True) 
class QuizAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student_answer = models.TextField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    is_submitted = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.question.subject} Question"
class ShortQuestion:
    """
    Represents a short question generated dynamically.
    Not stored in the database.
    """
    def __init__(self, text, correct_answer=None, marks=1):
        self.text = text                  # The question text
        self.correct_answer = correct_answer  # Optional correct answer
        self.marks = marks                # Marks for this question

    def __str__(self):
        return self.text
class MCQQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='mcqs')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])

    def __str__(self):
        return self.question_text