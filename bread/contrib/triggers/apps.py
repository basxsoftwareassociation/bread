import datetime

import dateparser
import htmlgenerator as hg
from django.apps import AppConfig
from django.utils import timezone

TRIGGER_PERIOD = datetime.timedelta(hours=1)


class TriggersConfig(AppConfig):
    name = "bread.contrib.triggers"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):

        from bread.utils.celery import RepeatedTask
        from celery import shared_task
        from django.db.models.signals import post_delete, post_save

        post_save.connect(save_handler, dispatch_uid="trigger_save")
        post_delete.connect(delete_handler, dispatch_uid="trigger_delete")

        shared_task(base=RepeatedTask, run_every=TRIGGER_PERIOD)(periodic_trigger)


def save_handler(sender, instance, created, **kwargs):
    datachange_trigger(sender, instance, "added" if created else "changed")


def delete_handler(sender, instance, **kwargs):
    datachange_trigger(sender, instance, "deleted")


def datachange_trigger(model, instance, type):
    from bread.utils import get_concrete_instance
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
        for object in trigger.filter.queryset.all():
            datefield_value = hg.resolve_lookup(object, trigger.field)
            if isinstance(datefield_value, (datetime.datetime, datetime.date)):
                if isinstance(datefield_value, datetime.date):
                    datefield_value = datetime.datetime.combine(
                        datefield_value, datetime.time()
                    )
                triggerdate = dateparser.parse(
                    trigger.offset, settings={"RELATIVE_BASE": datefield_value}
                )
                if timezone.now() <= triggerdate < timezone.now() + TRIGGER_PERIOD:
                    trigger.action(object)
