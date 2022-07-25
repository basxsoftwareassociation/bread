from celery import shared_task
from django.apps import AppConfig

from basxbread.utils import get_all_subclasses
from basxbread.utils.celery import RepeatedTask

from . import settings


class WorkflowsConfig(AppConfig):
    name = "basxbread.contrib.workflows"

    def ready(self):
        shared_task(base=RepeatedTask, run_every=settings.WORKFLOW_BEAT)(
            update_workflows
        )


def update_workflows():
    from .models import WorkflowBase

    for cls in get_all_subclasses(WorkflowBase):
        for workflow in cls.objects.filter(
            cancelled__isnull=True, completed__isnull=True
        ):
            print(f"Running workflow '{workflow}'")
            workflow.save()
