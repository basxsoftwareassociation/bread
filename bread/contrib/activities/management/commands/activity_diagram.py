from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print an activity diagram in the dot language"

    def add_arguments(self, parser):
        parser.add_argument("activity")

    def handle(self, *args, **options):
        Activity = apps.get_model(options["activity"])
        print(Activity.as_svg())
