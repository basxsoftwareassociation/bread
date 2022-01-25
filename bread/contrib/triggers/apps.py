import datetime

from django.apps import AppConfig
from django.utils import timezone

from bread.utils import get_concrete_instance

TRIGGER_PERIOD = datetime.timedelta(hours=1)


class TriggersConfig(AppConfig):
    name = "bread.contrib.triggers"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):

        from celery import shared_task
        from django.db.models.signals import post_delete, post_save

        from bread.utils.celery import RepeatedTask

        post_save.connect(save_handler, dispatch_uid="trigger_save")
        post_delete.connect(delete_handler, dispatch_uid="trigger_delete")

        shared_task(base=RepeatedTask, run_every=TRIGGER_PERIOD)(periodic_trigger)


def save_handler(sender, instance, created, **kwargs):
    datachange_trigger(sender, instance, "added" if created else "changed")


def delete_handler(sender, instance, **kwargs):
    datachange_trigger(sender, instance, "deleted")


def datachange_trigger(model, instance, type):
    from django.contrib.contenttypes.models import ContentType

    from .models import DataChangeTrigger

    for trigger in DataChangeTrigger.objects.filter(
        model=ContentType.objects.get_for_model(model), type=type, enable=True
    ):
        if trigger.filter.queryset.filter(id=instance.id).exists():
            get_concrete_instance(trigger.action).run(instance)


def periodic_trigger():

    from .models import DateFieldTrigger

    for trigger in DateFieldTrigger.objects.filter(enable=True):
        for instance in trigger.filter.queryset.all():
            if (
                timezone.now()
                <= trigger.triggerdate(instance)
                < timezone.now() + TRIGGER_PERIOD
            ):
                get_concrete_instance(trigger.action).run(instance)
