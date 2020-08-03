from django.core.management.base import BaseCommand

from bread.signals import post_deployment


class Command(BaseCommand):
    help = "Run to execute all post_deployment hooks"

    def handle(self, *args, **options):
        post_deployment.send(sender=self.__class__)
