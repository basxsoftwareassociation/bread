from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print a workflow diagram in the dot language"

    def add_arguments(self, parser):
        parser.add_argument("workflow")

    def handle(self, *args, **options):
        Workflow = apps.get_model(options["workflow"])
        print(Workflow.as_dot())
