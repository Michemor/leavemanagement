from django.contrib import admin
from .models import Leave, Employee


@admin.action(description="Approve selected leave requests")
def approve_leaves(modeladmin, request, queryset):
    updated_count = queryset.update(status="APPROVED")
    modeladmin.message_user(request, f"{updated_count} leave requests approved.")

@admin.action(description="Reject selected leave requests")
def reject_leaves(modeladmin, request, queryset):
    updated_count = queryset.update(status="REJECTED")
    modeladmin.message_user(request, f"{updated_count} leave requests rejected.")


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('leave_type','start_date', 'end_date', 'reason', 'status', 'employee')
    search_fields = ('leave_type','reason')
    list_filter = ('start_date', 'end_date', 'leave_type')
    actions = [approve_leaves, reject_leaves]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    # This controls what columns show up in the table
    list_display = ("email", "employee_department", "employee_position", "employee_role")
    
    # 1. Register your custom actions here
    actions = ["make_hr", "make_staff", "make_manager"]

    # 2. Define the first action
    @admin.action(description="Update role to HR")
    def make_hr(self, request, queryset):
        queryset.update(employee_role="Human Resources")
        self.message_user(request, f"Successfully updated {queryset.count()} employee(s) to HR.")
    # 3. Define the second action
    @admin.action(description="Update role to Staff")
    def make_staff(self, request, queryset):
        updated_count = queryset.update(employee_role="STAFF")
        self.message_user(request, f"Successfully updated {updated_count} employee(s) to Staff.")
    # 4. Define the third action
    @admin.action(description="Update role to Manager")
    def make_manager(self, request, queryset):
        updated_count = queryset.update(employee_role="MANAGER")
        self.message_user(request, f"Successfully updated {updated_count} employee(s) to Manager.")
