import google.generativeai as genai
from django.conf import settings
from .models import StudyMaterial

# Configure API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')


import io
from docx import Document
from PyPDF2 import PdfReader

def read_file_content(file_field):
    if not file_field:
        return ""

    name = file_field.name.lower()
    content = ""

    file_field.open('rb')  # always open as binary
    if name.endswith(".txt"):
        content = file_field.read().decode('utf-8', errors='ignore')
    elif name.endswith(".docx"):
        doc = Document(file_field)
        content = "\n".join([p.text for p in doc.paragraphs])
    elif name.endswith(".pdf"):
        reader = PdfReader(file_field)
        content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        # fallback
        content = file_field.read().decode('utf-8', errors='ignore')

    file_field.close()
    return content
import time
from google.api_core.exceptions import ResourceExhausted

def generate_questions(syllabus_text="", notes_text="", past_questions_text=""):
    prompt = f"""
You are an AI exam generator.

Syllabus:
{syllabus_text}

Notes:
{notes_text}

Past Questions:
{past_questions_text}

Generate:
- 5 MCQs
- 5 Very Short Answer Questions
Format clearly with numbers and options.
"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except ResourceExhausted as e:
            if attempt < max_retries - 1:
                wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                time.sleep(wait_time)
            else:
                raise Exception(
                    "Gemini API quota exceeded. Please wait a minute and try again, "
                    "or upgrade your Google AI plan at https://ai.dev/rate-limit"
                ) from e
def analyze_performance(questions, student_answers):
    prompt = f"""
You are an AI academic evaluator.

Questions:
{questions}

Student Answers:
{student_answers}

Analyze and provide:
1. Weak Topics
2. Mistakes
3. Study Tips
4. Improvement Plan
"""
    response = model.generate(
        prompt=prompt,
        temperature=0.2,
        max_output_tokens=1024
    )
    return response.result

def generate_questions_for_subject(subject, class_section):
    materials = StudyMaterial.objects.filter(subject=subject, class_section=class_section)
    syllabus_text, notes_text, past_questions_text = "", "", ""
    print("hbd")
    for mat in materials:
        syllabus_text += read_file_content(mat.syllabus_file) + "\n"
        notes_text += read_file_content(mat.notes_file) + "\n"
        past_questions_text += read_file_content(mat.past_questions_file) + "\n"

    return generate_questions(syllabus_text, notes_text, past_questions_text)