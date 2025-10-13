from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Student, StudentLog, Subject,Teacher, Program, Session

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'reg_no', 'program', 'year')
    search_fields = ('name', 'reg_no')
    list_filter = ('program', 'year')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher')
    list_filter = ('teacher',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'start_time', 'is_active')
    list_filter = ('subject', 'is_active')

@admin.register(StudentLog)
class StudentLogAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'session', 
        'time_in', 
        'time_out', 
        'duration',
    )
    list_filter = (
        'session__subject', 
        'session__subject__teacher',
        'time_in',
    )
    search_fields = (
        'student__name', 
        'student__reg_no', 
        'session__subject__name'
    )

