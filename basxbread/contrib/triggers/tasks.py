import celery

print(celery.__file__)
from celery import shared_task  # noqa

from basxbread.utils import get_concrete_instance  # noqa


@shared_task
def run_action(action_pk, modelname, instance_pk):
    from django.apps import apps

    from .models import Action

    get_concrete_instance(Action.objects.get(pk=action_pk)).run(
        apps.get_model(modelname).objects.get(pk=instance_pk)
    )
