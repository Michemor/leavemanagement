from rest_framework.permissions import BasePermission
from .models import Employee


class IsAdminRole(BasePermission):
    """Only employees with the ADMIN role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"


class IsAdminOrHR(BasePermission):
    """Employees with ADMIN or HR role."""

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        role = getattr(user, "role", None)

        return role in ["ADMIN", "HR", "MANAGER"]


class IsAdminOrHROfSameInstitutionAndDepartment(BasePermission):
    """
    Permission class to ensure that HR/Admin/Manager can only manage employees
    and leave requests from their own institution and department.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        return role in ["ADMIN", "HR", "MANAGER"]

    def has_object_permission(self, request, view, obj):
        """
        Check if the admin/HR/manager has access to the object based on institution and department.
        Works for both Employee and Leave objects.
        """
        # Get the institution and department of the requester
        requester_institution = request.user.institution
        requester_department = request.user.department

        # Handle Leave objects (need to check employee's institution/department)
        if hasattr(obj, "employee"):
            target_institution = obj.employee.institution
            target_department = obj.employee.department
        # Handle Employee objects directly
        else:
            target_institution = obj.institution
            target_department = obj.department

        # Check if requester's institution and department match target
        return (
            requester_institution == target_institution
            and requester_department == target_department
        )
