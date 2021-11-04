from django.apps import AppConfig
from django.contrib.messages.constants import DEFAULT_TAGS
from django.utils.translation import gettext as _


class BreadConfig(AppConfig):

    name = "bread"
    verbose_name = "Bread Engine"

    def ready(self):
        # trigger translation of message tags
        [_(tag.capitalize()) for tag in DEFAULT_TAGS.values()]
