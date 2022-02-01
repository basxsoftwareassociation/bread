import datetime

from celery import shared_task
from django.apps import AppConfig
from django.conf import settings
from django.utils import timezone

from bread.utils import get_concrete_instance

TRIGGER_PERIOD = getattr(settings, "TRIGGER_PERIOD", datetime.timedelta(hours=1))


class TriggersConfig(AppConfig):
    name = "bread.contrib.triggers"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):

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

    model = ContentType.objects.filter(
        app_label=model._meta.app_label, model=model._meta.model_name
    )
    if model.exists():
        for trigger in DataChangeTrigger.objects.filter(
            model=model.first(), type=type, enable=True
        ):
            if trigger.filter.queryset.filter(pk=instance.pk).exists():
                # delay execution a bit as the trigger may run immediately even though
                # the current request has not finished (and therefore not commited to DB yet)
                run_action.apply_async(
                    (trigger.action.pk, instance._meta.label, instance.pk), countdown=5
                )


@shared_task
def run_action(action_pk, modelname, instance_pk):
    from django.apps import apps

    from .models import Action

    get_concrete_instance(Action.objects.get(pk=action_pk)).run(
        apps.get_model(modelname).objects.get(pk=instance_pk)
    )


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
