import datetime

from celery import shared_task
from django.apps import AppConfig
from django.conf import settings
from django.utils import timezone

from .tasks import run_action

TRIGGER_PERIOD = getattr(settings, "TRIGGER_PERIOD", datetime.timedelta(hours=1))


class TriggersConfig(AppConfig):
    name = "basxbread.contrib.triggers"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):

        from django.db.models.signals import post_delete, post_save, pre_save

        from basxbread.utils.celery import RepeatedTask

        pre_save.connect(get_old_object)
        post_save.connect(save_handler)
        post_delete.connect(delete_handler, dispatch_uid="trigger_delete")

        shared_task(base=RepeatedTask, run_every=TRIGGER_PERIOD)(periodic_trigger)


# make sure we have access to the old value so we can change for field changes
def get_old_object(sender, instance, **kwargs):
    instance._old = None
    if instance.pk:
        try:
            instance._old = type(instance).objects.get(pk=instance.pk)
        except type(instance).DoesNotExist:
            pass


def save_handler(sender, instance, created, **kwargs):
    datachange_trigger(sender, instance, "added" if created else "changed")


def delete_handler(sender, instance, **kwargs):
    datachange_trigger(sender, instance, "deleted")


def datachange_trigger(model, instance, type):
    from django.contrib.contenttypes.models import ContentType

    from .models import DataChangeTrigger

    contenttypes = ContentType.objects.filter(
        app_label=model._meta.app_label, model=model._meta.model_name
    )
    for contenttype in contenttypes:
        for trigger in DataChangeTrigger.objects.filter(
            model=contenttype, type=type, enable=True
        ):
            if type == "changed" and trigger.field and instance._old is not None:
                if getattr(instance, trigger.field) == getattr(
                    instance._old, trigger.field
                ):
                    continue
            if trigger.filter.queryset.filter(pk=instance.pk).exists():
                # delay execution a bit as the trigger may run immediately even though
                # the current request has not finished (and therefore not commited to DB yet)
                run_action.apply_async(
                    (trigger.action.pk, instance._meta.label, instance.pk), countdown=5
                )
    instance._old = None


def periodic_trigger():

    from .models import DateFieldTrigger

    for trigger in DateFieldTrigger.objects.filter(enable=True):
        for instance in trigger.filter.queryset.all():
            td = trigger.triggerdate(instance)
            if (
                td is not None
                and timezone.now() <= td < timezone.now() + TRIGGER_PERIOD
            ):
                run_action.apply_async(
                    (trigger.action.pk, instance._meta.label, instance.pk)
                )
