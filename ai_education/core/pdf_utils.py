# pdf_utils.py
from django.http import HttpResponse
from reportlab.pdfgen import canvas

def generate_quiz_pdf(quiz):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quiz_{quiz.id}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)

    p.drawString(100, 800, f"Quiz: {quiz.subject}")
    p.drawString(100, 780, f"Teacher: {quiz.teacher.user.username}")
    p.drawString(100, 760, "Questions:")
    
    y = 740
    for q in quiz.questions.split("\n"):
        p.drawString(120, y, q)
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()

    return response