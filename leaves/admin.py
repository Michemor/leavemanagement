from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('leave_name', 'default_days', 'is_paid')
    search_fields = ('leave_name',)
    list_filter = ('is_paid',)

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'leave_type', 'remaining_days', 'year')
    search_fields = ('employee_name__username', 'leave_type__leave_name')
    list_filter = ('year',)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status')
    search_fields = ('user__username', 'leave_type__leave_name')
    list_filter = ('status', 'start_date', 'end_date')
