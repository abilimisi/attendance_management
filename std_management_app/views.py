from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
import json
from .models import Student, StudentLog, Subject,Teacher, Session
import csv
from django.http import HttpResponse


def home_view(request):
    student_count = Student.objects.count()
    teacher_count = Teacher.objects.count()
    context = {
        'student_count': student_count,
        'teacher_count' : teacher_count
    }
    return render(request, 'index.html', context)

@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        subjects = Subject.objects.filter(teacher=teacher)
        
        subjects_with_sessions = []
        for subject in subjects:
            sessions = Session.objects.filter(subject=subject).order_by('-start_time')
            
            subjects_with_sessions.append({
                'id': subject.id,
                'name': subject.name,
                'sessions': sessions,
                'active_session': sessions.filter(is_active=True).first()
            })
        
        context = {
            'subjects_with_sessions': subjects_with_sessions,
            'teacher_name': teacher.name,
        }
        return render(request, 'teacher_dashboard.html', context)
    except Teacher.DoesNotExist:
        return redirect('logout')

@login_required
def scanner_view(request, session_id):
    session = get_object_or_404(Session, id=session_id, subject__teacher__user=request.user)
    return render(request, 'scanner_view.html', {'subject': session.subject, 'session_id': session.id})

@csrf_exempt
def process_scan(request, session_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        reg_no = data.get('student_id')
        now = timezone.now()

        try:
            student = Student.objects.get(reg_no=reg_no)
            session = get_object_or_404(Session, id=session_id, subject__teacher__user=request.user)
            
            record = StudentLog.objects.filter(
                student=student, 
                session=session, 
                time_out__isnull=True
            ).first()

            MIN_CHECK_IN_TIME = timedelta(minutes=1)
            response_data = {}

            if record is None:
                StudentLog.objects.create(
                    student=student,
                    session=session,
                    time_in=now,
                    time_out=None
                )
                response_data = {'status': 'success', 'message': f'{student.name} checked IN successfully!'}

            elif (now - record.time_in) < MIN_CHECK_IN_TIME:
                response_data = {'status': 'info', 'message': f'{student.name}: Check-Out blocked! Must wait 2 minutes before checking out.'}
            
            else:
                record.time_out = now
                record.save()
                response_data = {'status': 'success', 'message': f'{student.name} checked OUT successfully!'}
            
    
            live_count = StudentLog.objects.filter(
                session=session,
                time_out__isnull=True
            ).count()
            
            response_data['live_count'] = live_count
            
            return JsonResponse(response_data)

        except (Student.DoesNotExist, Session.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invalid student or session.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required
def attendance_list_view(request, session_id):
    session = get_object_or_404(Session, id=session_id, subject__teacher__user=request.user)
    
    teacher_name = session.subject.teacher.name
    subject_name = session.subject.name
    
    all_students = Student.objects.all().order_by('reg_no')
    
 
    session_logs = StudentLog.objects.filter(session=session).order_by('time_in')

    all_logs_by_student = defaultdict(list)
    for log in session_logs:
        all_logs_by_student[log.student_id].append(log)

    student_list = []
    
    for student in all_students:
        logs = all_logs_by_student.get(student.id, [])
        
        current_status = 'Absent'
        
        if logs:
            last_log = logs[-1] 
            if last_log.time_in and not last_log.time_out:
                current_status = 'IN (Active)'
            elif last_log.time_in and last_log.time_out:
                current_status = 'OUT (Completed)'

        student_list.append({
            'name': student.name,
            'reg_no': student.reg_no,
            'current_status': current_status,
            'logs': logs, 
        })
    
    context = {
        'subject_name': subject_name,
        'session_date': session.start_time,
        'student_list': student_list,
        'teacher_name': teacher_name,
        'session_id': session_id,
        'present_count': StudentLog.objects.filter(session=session).count(), 
        'total_students': all_students.count(),
    }
    return render(request, 'attendance_list.html', context)
@login_required
def start_session(request, subject_id):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, id=subject_id, teacher__user=request.user)
        Session.objects.filter(subject=subject, is_active=True).update(is_active=False)
        new_session = Session.objects.create(subject=subject, is_active=True)
        return redirect('scanner_view', session_id=new_session.id)
    return redirect('teacher_dashboard')


@login_required
def end_session(request, session_id):
    session = get_object_or_404(Session, id=session_id, subject__teacher__user=request.user)
    
    if request.method == 'POST':
        session.is_active = False
        session.save()
        return redirect('teacher_dashboard') 
    
    return redirect('teacher_dashboard')

@login_required
def download_attendance(request, session_id):
    session = get_object_or_404(Session, id=session_id, subject__teacher__user=request.user)
 
    logs = StudentLog.objects.filter(session=session).order_by('student__name', 'time_in')

 
    response = HttpResponse(content_type='text/csv')
    file_name = f"Attendance_Report_{session.subject.name}_{session.start_time.strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    writer = csv.writer(response)
    
    writer.writerow([
        'Date', 
        'Subject Name', 
        'Teacher Name', 
        'Student Name', 
        'Registration No', 
        'Time IN', 
        'Time OUT', 
        'Duration'
    ])
    
    for log in logs:
        time_in_str = timezone.localtime(log.time_in).strftime("%H:%M:%S")
        time_out_str = timezone.localtime(log.time_out).strftime("%H:%M:%S") if log.time_out else 'N/A'
        
        writer.writerow([
            session.start_time.strftime("%Y-%m-%d"),
            session.subject.name,
            session.subject.teacher.name,
            log.student.name,
            log.student.reg_no,
            time_in_str,
            time_out_str,
            log.duration()
        ])

    return response

@login_required
def subject_history_view(request, subject_id):
  
    subject = get_object_or_404(Subject, id=subject_id, teacher__user=request.user)
    
    all_sessions = Session.objects.filter(
        subject=subject, 
        is_active=False 
    ).order_by('-start_time')

    active_session = Session.objects.filter(subject=subject, is_active=True).first()

    context = {
        'subject': subject,
        'all_sessions': all_sessions,
        'active_session': active_session,
    }
    return render(request, 'subject_history.html', context)