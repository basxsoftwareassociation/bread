from celery.decorators import periodic_task
from django.apps import AppConfig

from . import settings


class WorkflowsConfig(AppConfig):
    name = "bread.contrib.workflows"

    def ready(self):
        periodic_task(run_every=settings.WORKFLOW_BEAT)(update_workflows)


def update_workflows():
    from .models import WorkflowBase

    for cls in WorkflowBase.__subclasses__():
        for workflow in cls.objects.filter(
            cancelled__isnull=True, completed__isnull=True
        ):
            workflow.save()
