"""
URL configuration for ai_education project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from core import views
from django.contrib import admin

urlpatterns = [

    path('admin/', admin.site.urls),
    path('', views.home, name='home'),

    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/upload_marks/', views.upload_marks, name='upload_marks'),
    path('teacher/generate_quiz/', views.generate_remedial_quiz, name='generate_quiz'),
    path('teacher/performance_report/', views.student_performance_report, name='performance_report'),
    path('teacher/assign-remedial-quiz/', views.assign_remedial_quiz, name='assign_remedial_quiz'),
    path('teacher/quiz/<int:quiz_id>/pdf/', views.view_quiz_pdf, name='view_quiz_pdf'),
    
    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/quiz/', views.student_assigned_quizzes, name='assigned_quizes'),
    path('student/quiz/<int:assignment_id>/attempt/', views.attempt_quiz, name='attempt_quiz'),
    path('student/submit/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),
    path('student/analysis',views.submit_exam, name='analysis'),
    path('student/ai-question/<int:assignment_id>/attempt/', views.attempt_ai_question, name='attempt_ai_question'),
    # urls.py
    path('student/questions/', views.student_assigned_questions, name='student_assigned_questions'),
    path('student/question/<int:assignment_id>/attempt/', views.attempt_question, name='attempt_question'),
    path('teacher/question/create/', views.generate_question, name='generate_question'),
    # Auth
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
