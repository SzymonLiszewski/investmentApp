from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a demo test user for local/demo environments (idempotent).'

    def handle(self, *args, **options):
        username = 'demo'
        password = 'Demo123!'
        email = 'demo@example.com'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': False, 'is_active': True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created demo user: username="{username}", password="{password}"'
                )
            )
        else:
            # Ensure password is set in case DB was recreated without re-running migrate
            user.set_password(password)
            user.save()
            if options.get('verbosity', 1) >= 2:
                self.stdout.write(
                    self.style.WARNING(
                        f'Demo user "{username}" already exists; password reset to "{password}".'
                    )
                )
