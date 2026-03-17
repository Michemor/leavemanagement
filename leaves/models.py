from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


class Leave(models.Model):
    leave_id = models.AutoField(primary_key=True)
    leave_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    supporting_document = models.FileField(upload_to='leave_documents/', blank=True, null=True)

class Employee(models.Model):
    """Model representing an employee in the leave management system.
    Each employee is associated with a Django User for authentication and has additional fields for department, position, email, and phone number.
    
    Fields:
        user: One-to-one relationship with Django's built-in User model for authentication.
        employee_id: Auto-incrementing primary key for the employee.
        employee_name: One-to-one relationship with User to store the employee's name.
        employee_department: CharField to store the department of the employee.
        employee_position: CharField to store the position of the employee.
        employee_email: EmailField to store the email address of the employee.
        employee_phone: CharField to store the phone number of the employee.
        """

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    employee_id = models.AutoField(primary_key=True)
    employee_name = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_department = models.CharField(max_length=100)
    employee_position = models.CharField(max_length=100)
    employee_email = models.EmailField(unique=True)
    employee_phone = models.CharField(max_length=20, blank=True)


    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_department} - {self.employee_position})"

