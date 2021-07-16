from celery import shared_task
from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    name = "bread.contrib.workflows"

    def ready(self):
        from django.utils import timezone
        from django_celery_beat.models import MINUTES, IntervalSchedule, PeriodicTask

        interval, _ = IntervalSchedule.objects.get_or_create(every=1, period=MINUTES)
        if not PeriodicTask.objects.filter(
            task="bread.contrib.workflows.apps.update_workflows"
        ).exists():
            PeriodicTask.objects.create(
                name="bread.contrib.workflows.apps.update_workflows",
                task="bread.contrib.workflows.apps.update_workflows",
                interval=interval,
                start_time=timezone.now(),
            )


@shared_task
def update_workflows():
    from .models import WorkflowBase

    for cls in WorkflowBase.__subclasses__():
        for workflow in cls.objects.filter(
            cancelled__isnull=True, completed__isnull=True
        ):
            workflow.save()
