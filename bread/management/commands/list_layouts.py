from django.core.management.base import BaseCommand

from bread.signals import post_deployment


class Command(BaseCommand):
    help = "Show a list of all registered layouts"

    def handle(self, *args, **options):
        from bread.layout.registry import _registry

        for layoutname, layoutfunc in _registry.items():
            print(f"{layoutname}: {layoutfunc} => {layoutfunc()}")
        post_deployment.send(sender=self.__class__)
