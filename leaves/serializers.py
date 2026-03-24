import logging
from datetime import date

from rest_framework import serializers

from .models import Leave, Employee


logger = logging.getLogger(__name__)


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
        # Ensure employee is set from the request context, not the client
        read_only_fields = ["employee"]

    list_display = ("leave_type", "start_date", "end_date", "reason", "status")
    search_fields = ("leave_type", "reason", "status")
    list_filter = ("start_date", "end_date", "leave_type", "status")

    def validate(self, data):
        """Custom validation to ensure that the end date is not before the start date and that the start date is not in the past."""
        # Only validate dates if they are present in the data (allows partial PATCH updates)
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        leave_type = data.get("leave_type")

        logger.debug(
            "Validating leave for %(employee)s: %(start)s -> %(end)s (%(type)s)",
            {
                "employee": getattr(data.get("employee"), "id", None),
                "start": start_date,
                "end": end_date,
                "type": leave_type,
            },
        )

        # Only compare dates if both are present
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")

        # Only check if start date is in the past if start_date is provided
        if start_date and start_date < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")

        document = data.get("supporting_document")
        leaves_requiring_document = ["SICK", "STUDY"]

        # Only validate document requirement if leave_type is provided
        if leave_type in leaves_requiring_document and not document:
            raise serializers.ValidationError(
                f"{leave_type} leave requires a supporting document."
            )
        logger.info(
            "Leave validation successful for type=%s start=%s end=%s",
            leave_type,
            start_date,
            end_date,
        )
        return data

    def validate_status(self, value):
        """Normalize status to uppercase to handle case-insensitive input."""
        if value:
            value = value.upper()
        return value


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
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        """Create a new employee instance with the provided validated data."""
        password = validated_data.pop("password")

        # Ensure a unique username is always set. Since the custom user model
        # still inherits from AbstractUser, the "username" field is required
        # and must be unique. If we don't populate it, multiple users will end
        # up with the default empty string and the database will raise a
        # UNIQUE constraint error (500 response) on the second registration.
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
