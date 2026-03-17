from django.contrib import admin
from .models import Leave, Employee

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('leave_type','start_date', 'end_date', 'reason')
    search_fields = ('leave_type','reason')
    list_filter = ('start_date', 'end_date', 'leave_type')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'employee_department', 'employee_position', 'email', 'employee_role')
    search_fields = ('first_name', 'last_name', 'employee_department', 'employee_position', 'email', 'employee_role')
    list_filter = ('employee_department', 'employee_position', 'employee_role')
