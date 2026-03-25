from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Initializes admin credentials if the database is empty'

    def handle(self, *args, **options):
        # Check if any users exist
        if not User.objects.exists():
            self.stdout.write("Database empty. Creating initial admin...")
            
            # Pull credentials from environment variables for safety
            email = os.environ.get("ADMIN_EMAIL", "admin@teamimpactuniversity.com")
            password = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")

            # Get or create a default institution for admin
            from leaves.models import Institution
            default_institution, _ = Institution.objects.get_or_create(
                name="System"
            )
            
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name='Admin',
                last_name='User',
                department='Administration',
                position='System Administrator',
                role='ADMIN',
                institution=default_institution
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created admin: {email}"))
        else:
            self.stdout.write("Users already exist. Skipping admin initialization.")