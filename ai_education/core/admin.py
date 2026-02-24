from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(ClassSection)
admin.site.register(StudyMaterial)
admin.site.register(ExamResult)
admin.site.register(Quiz)
admin.site.register(QuizAssignment)