import logging
from datetime import date

from rest_framework import serializers

# Import LeavePolicy and the utility function we discussed
from .models import Leave, Employee, LeavePolicy
from .utils import calculate_working_days

logger = logging.getLogger(__name__)


class LeavePolicySerializer(serializers.ModelSerializer):
    """Serializer for Admin/HR to manage dynamic leave types."""

    class Meta:
        model = LeavePolicy
        fields = "__all__"


class EmployeeNestedSerializer(serializers.ModelSerializer):
    """Nested serializer for employee data in leave responses."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "email", "full_name", "employee_role", "employee_department"]

    def get_full_name(self, obj):
        """Return the full name of the employee."""
        return f"{obj.first_name} {obj.last_name}".strip()


class LeaveSerializer(serializers.ModelSerializer):
    employee = EmployeeNestedSerializer(read_only=True)

    class Meta:
        model = Leave
        fields = "__all__"
        # Ensure employee and status are set from the request context/HR, not the client
        read_only_fields = ["employee", "status"]

    list_display = ("leave_type", "start_date", "end_date", "reason", "status")
    search_fields = (
        "leave_type__name",
        "reason",
        "status",
    )  # Updated to search by policy name
    list_filter = ("start_date", "end_date", "leave_type", "status")

    def validate(self, data):
        """Custom validation to ensure valid dates, working days, and policy constraints."""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Because leave_type is a ForeignKey, DRF resolves this into a LeavePolicy object instance
        leave_policy = data.get("leave_type")

        logger.debug(
            "Validating leave for %(employee)s: %(start)s -> %(end)s (%(type)s)",
            {
                "employee": getattr(data.get("employee"), "id", None),
                "start": start_date,
                "end": end_date,
                "type": getattr(leave_policy, "name", None),
            },
        )

        # 1. Basic Date Logic
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": ["End date cannot be before start date."]}
            )

        if start_date and start_date < date.today():
            raise serializers.ValidationError(
                {"start_date": ["Start date cannot be in the past."]}
            )

        # 2. Dynamic Policy and Working Days Logic
        if start_date and end_date and leave_policy:
            requested_days = calculate_working_days(start_date, end_date)

            if requested_days == 0:
                raise serializers.ValidationError(
                    {
                        "date_range": "The selected date range only contains weekends or public holidays. No leave days are required."
                    }
                )

            if requested_days > leave_policy.max_days:
                raise serializers.ValidationError(
                    {
                        "date_range": f"You requested {requested_days} working days, but the maximum allowed for {leave_policy.name} is {leave_policy.max_days} days."
                    }
                )

        # 3. Document Requirement Logic
        document = data.get("supporting_document")
        if leave_policy:
            # Check if the dynamic policy name contains 'SICK' or 'STUDY' (case-insensitive)
            policy_name = leave_policy.name.upper()
            requires_document = "SICK" in policy_name or "STUDY" in policy_name

            if requires_document and not document:
                raise serializers.ValidationError(
                    {
                        "supporting_document": [
                            f"{leave_policy.name} requires a supporting document."
                        ]
                    }
                )

        logger.info(
            "Leave validation successful for type=%s start=%s end=%s",
            getattr(leave_policy, "name", None),
            start_date,
            end_date,
        )
        return data

    def validate_status(self, value):
        """Normalize status to uppercase to handle case-insensitive input."""
        if value:
            value = value.upper()
        return value

    def to_representation(self, instance):
        """Inject human-readable policy details into the JSON response."""
        representation = super().to_representation(instance)
        if instance.leave_type:
            representation["leave_type_name"] = instance.leave_type.name
            representation["leave_type_max_days"] = instance.leave_type.max_days
        return representation


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}, min_length=8
    )

    class Meta:
        model = Employee
        fields = [
            "first_name",
            "last_name",
            "email",
            "employee_department",
            "employee_position",
            "phone_number",
            "employee_role",
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "employee_role": {"read_only": True},
        }

    def create(self, validated_data):
        """Create a new employee instance with the provided validated data."""
        password = validated_data.pop("password")

        if "username" not in validated_data or not validated_data.get("username"):
            base_username = (validated_data.get("email") or "").split("@")[0] or "user"
            username = base_username
            suffix = 1
            while Employee.objects.filter(username=username).exists():
                username = f"{base_username}{suffix}"
                suffix += 1
            validated_data["username"] = username

        logger.info(
            "Creating employee account for email=%s department=%s position=%s role=%s",
            validated_data.get("email"),
            validated_data.get("employee_department"),
            validated_data.get("employee_position"),
            validated_data.get("employee_role"),
        )

        employee = Employee(**validated_data)
        employee.set_password(password)  # Hash the password before saving
        employee.save()
        logger.info(
            "Employee created with id=%s username=%s", employee.id, employee.username
        )
        return employee


class UpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}, min_length=8
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer used to request a password reset email."""

    email = serializers.EmailField()
    redirect_url = serializers.URLField(
        required=False,
        help_text="The URL of the frontend page where the user will reset their password. e.g., http://localhost:3000/reset-password",
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer used to confirm a password reset with a token."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}, min_length=8
    )


class InitializeSerializer(serializers.Serializer):
    """Simple serializer for the system initialization endpoint."""

    pass


class EmployeeLoginSerializer(serializers.ModelSerializer):
    """Serializer to return employee user data during login."""

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "employee_department",
            "employee_position",
            "phone_number",
            "employee_role",
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for listing all employees with their complete information."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "username",
            "full_name",
            "first_name",
            "last_name",
            "employee_department",
            "employee_position",
            "phone_number",
            "employee_role",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "username", "date_joined"]

    def get_full_name(self, obj):
        """Return the full name of the employee."""
        return f"{obj.first_name} {obj.last_name}".strip()


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Custom serializer for token response with user data included."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = EmployeeLoginSerializer()

    @classmethod
    def get_token(cls, user):
        """Generate tokens and include user data in response."""
        from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

        token_serializer = TokenObtainPairSerializer()
        token_serializer.fields["email"] = serializers.EmailField()
        token_serializer.fields["password"] = serializers.CharField()

        return token_serializer


class LeaveStatisticsSerializer(serializers.Serializer):
    """Serializer for leave statistics."""

    total_leaves = serializers.IntegerField()
    pending_leaves = serializers.IntegerField()
    approved_leaves = serializers.IntegerField()
    rejected_leaves = serializers.IntegerField()
    average_duration = serializers.FloatField()
    leave_types_breakdown = serializers.DictField()
    status_breakdown = serializers.DictField()
