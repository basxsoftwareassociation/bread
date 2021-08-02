from celery import Task, shared_task
from django.apps import AppConfig

from . import settings


class WorkflowsConfig(AppConfig):
    name = "bread.contrib.workflows"

    def ready(self):
        shared_task(base=WorkflowUpdate, run_every=settings.WORKFLOW_BEAT)(
            update_workflows
        )


class WorkflowUpdate(Task):
    @classmethod
    def on_bound(cls, app):
        app.conf.beat_schedule[cls.name] = {
            "task": cls.name,
            "schedule": cls.run_every.total_seconds(),
            "args": (),
            "kwargs": {},
            "options": getattr(cls, "options", {}),
            "relative": getattr(cls, "relative", False),
        }


def update_workflows():
    from .models import WorkflowBase

    for cls in WorkflowBase.__subclasses__():
        for workflow in cls.objects.filter(
            cancelled__isnull=True, completed__isnull=True
        ):
            workflow.save()
