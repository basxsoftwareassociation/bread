import htmlgenerator as hg
from django.contrib.messages.views import SuccessMessageMixin
from dynamic_preferences import views as preferences_views
from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.registries import global_preferences_registry

from bread import layout as breadlayout
from bread.views import BreadView


class PreferencesView(
    SuccessMessageMixin, BreadView, preferences_views.PreferenceFormView
):
    success_message = "Preferences updated"
    form_class = GlobalPreferenceForm
    registry = global_preferences_registry

    def get_layout(self):
        section_fields = {}
        if self.section_name:
            section_names = [self.section_name]
        else:
            section_names = self.form_class.registry.section_objects.keys()
        for section in section_names:
            section_fields[section] = []
            for field in self.form_class.registry[section]:
                section_fields[section].append(f"{section}__{field}")

        return breadlayout.forms.Form(
            hg.C("form"),
            *[
                hg.BaseElement(
                    hg.H3(section.capitalize()),
                    *[
                        breadlayout.forms.FormField(f)
                        for f in section_fields.get(section)
                    ],
                )
                for section in section_fields.keys()
            ],
            breadlayout.forms.helpers.Submit(),
        )
