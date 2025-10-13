from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.files import File
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from django.contrib.auth.models import User

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Program(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=100)
    reg_no = models.CharField(max_length=20, unique=True, verbose_name="Registration Number")
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    year = models.IntegerField(default=2025)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.reg_no})"

@receiver(pre_save, sender=Student)
def generate_student_barcode(sender, instance, **kwargs):
    if not instance.pk:
        CODE128 = barcode.get_barcode_class('code128')
        ean = CODE128(instance.reg_no, writer=ImageWriter())
        buffer = BytesIO()
        ean.write(buffer)
        instance.barcode_image.save(f'{instance.reg_no}.png', File(buffer), save=False)

class Subject(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return f"{self.name} - ({self.teacher.name})"

class Session(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.subject.name} session on {self.start_time.date()}"

class StudentLog(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True) 
    
    def duration(self):
        if self.time_in and self.time_out:
            duration = self.time_out - self.time_in
            total_seconds = duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        elif self.time_in:
            return "Active"
        return "N/A"

    def __str__(self):
        return f"{self.student.name} - {self.session.subject.name} (IN: {self.time_in.date})"
