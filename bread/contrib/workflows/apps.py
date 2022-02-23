from celery import shared_task
from django.apps import AppConfig

from bread.utils.celery import RepeatedTask

from . import settings


class WorkflowsConfig(AppConfig):
    name = "bread.contrib.workflows"

    def ready(self):
        shared_task(base=RepeatedTask, run_every=settings.WORKFLOW_BEAT)(
            update_workflows
        )


def update_workflows():
    from .models import WorkflowBase

    for cls in WorkflowBase.__subclasses__():
        for workflow in cls.objects.filter(
            cancelled__isnull=True, completed__isnull=True
        ):
            print(f"Running workflow '{workflow}'")
            workflow.save()
