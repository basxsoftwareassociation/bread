from django.utils.translation import gettext_lazy as _
from dynamic_preferences.preferences import Section
from dynamic_preferences.types import StringPreference
from dynamic_preferences.users.registries import user_preferences_registry

general = Section("general", _("General"))


@user_preferences_registry.register
class PreferredLanguage(StringPreference):
    section = general
    name = "preferred_language"
    default = ""
    verbose_name = _("Preferred Language")


@user_preferences_registry.register
class Timezone(StringPreference):
    section = general
    name = "timezone"
    default = ""
    verbose_name = _("Timezone")
