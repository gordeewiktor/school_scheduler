from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.infrastructure.database.models import School, SchoolMembership


class Command(BaseCommand):
    help = "Create a School and attach an existing user to it as a principal."

    def add_arguments(self, parser) -> None:
        parser.add_argument("name", help="Name of the school to create.")
        parser.add_argument(
            "--username",
            required=True,
            help="Username of the existing user to attach as a principal.",
        )

    def handle(self, *args, **options) -> None:
        name = options["name"]
        username = options["username"]

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"No user found with username '{username}'.") from exc

        with transaction.atomic():
            school, created = School.objects.get_or_create(name=name)
            membership, membership_created = SchoolMembership.objects.get_or_create(
                user=user,
                school=school,
                defaults={"role": SchoolMembership.Role.PRINCIPAL},
            )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created school '{school.name}'."))
        else:
            self.stdout.write(f"Using existing school '{school.name}'.")

        if membership_created:
            self.stdout.write(
                self.style.SUCCESS(f"Attached '{user.username}' to '{school.name}' as {membership.role}.")
            )
        else:
            self.stdout.write(f"'{user.username}' is already a member of '{school.name}'.")
