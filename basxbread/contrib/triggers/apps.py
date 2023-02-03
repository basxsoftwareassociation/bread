import datetime

from celery import shared_task
from django.apps import AppConfig
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from kombu.utils.uuid import uuid

from .tasks import run_action

TRIGGER_PERIOD = getattr(settings, "TRIGGER_PERIOD", datetime.timedelta(hours=1))


class TriggersConfig(AppConfig):
    name = "basxbread.contrib.triggers"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django.db.models.signals import post_save, pre_delete, pre_save

        from basxbread.utils.celery import RepeatedTask

        pre_save.connect(get_old_object)
        post_save.connect(save_handler)
        pre_delete.connect(delete_handler, dispatch_uid="trigger_delete")

        shared_task(
            base=RepeatedTask,
            run_every=TRIGGER_PERIOD,
            name="basxbread.contrib.triggers.apps.periodic_trigger",
        )(periodic_trigger)


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
                fields = [i.strip() for i in trigger.field.split(",")]
                if all(  # if none of the fields has changed, skip this trigger
                    getattr(instance, field) == getattr(instance._old, field)
                    for field in fields
                ):
                    continue
            if trigger.action and (
                trigger.filter.queryset.filter(pk=instance.pk).exists()
                or type == "added"
            ):
                name = f"Trigger '{trigger}': Action '{trigger.action}'"
                if type == "deleted":
                    # if we want to still have access to the database object
                    # while the action is performed, we need to execute the action
                    # immediately and cannot do it in the background with celery
                    run_action(trigger.action.pk, instance._meta.label, instance.pk)
                else:
                    transaction.on_commit(
                        lambda action_pk=trigger.action.pk: run_action.apply_async(
                            (action_pk, instance._meta.label, instance.pk),
                            shadow=name,
                            task_id=f"{name}-{uuid()}",
                        )
                    )
    instance._old = None


def periodic_trigger():
    from .models import DateFieldTrigger

    print(
        f"Running trigger in range: {timezone.now()} - {timezone.now() + TRIGGER_PERIOD}"
    )
    for trigger in DateFieldTrigger.objects.filter(enable=True):
        for instance in trigger.filter.queryset.all():
            for td in trigger.triggerdates(instance):
                if (
                    td is not None
                    and timezone.now() <= td < timezone.now() + TRIGGER_PERIOD
                ) and trigger.action:
                    name = f"Trigger '{trigger}': Action '{trigger.action}'"
                    run_action.apply_async(
                        (trigger.action.pk, instance._meta.label, instance.pk),
                        shadow=name,
                        task_id=f"{name}-{uuid()}",
                    )
