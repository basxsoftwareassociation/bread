from django import forms
from dynamic_preferences.preferences import Section
from dynamic_preferences.types import BooleanPreference
from dynamic_preferences.users.registries import user_preferences_registry

ui = Section("user_interface")


@user_preferences_registry.register
class NavigationMenuExtended(BooleanPreference):
    section = ui
    name = "navigation_menu_extended"
    default = True
    # this setting should not be directly visibel to the user because we set it through ajax
    widget = forms.CheckboxInput(attrs={"style": "display: none"})
