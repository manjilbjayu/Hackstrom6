import pandas as pd
from django.contrib.auth.models import User
from .models import ExamResult, Student

def get_failed_students(subject, class_section):
    return Student.objects.filter(
        examresult__subject=subject,
        examresult__class_section=class_section,
        examresult__is_failed=True
    ).distinct()
def process_excel(file):
    df = pd.read_excel(file)

    for index, row in df.iterrows():
        username = row['username']
        marks = row['marks']
        total = row['total']

        percentage = (marks / total) * 100

        user = User.objects.get(username=username)

        ExamResult.objects.create(
            student=user,
            marks=marks,
            total=total,
            percentage=percentage
        )

        if percentage < 40:
            print("Needs remedial:", username)
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")

def generate_questions(syllabus, notes, past_questions):

    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    Based on the following syllabus, notes and past questions:
    
    Syllabus: {syllabus}
    Notes: {notes}
    Past Questions: {past_questions}
    
    Generate:
    - 10 MCQs with 4 options and correct answer
    - 5 very short questions with answers
    """

    response = model.generate_content(prompt)
    return response.text