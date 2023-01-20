import htmlgenerator as hg
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from dynamic_preferences import views as preferences_views
from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.registries import global_preferences_registry
from guardian.mixins import PermissionRequiredMixin

from .. import layout
from ..views import BaseView


class PreferencesView(
    BaseView,
    SuccessMessageMixin,
    PermissionRequiredMixin,
    preferences_views.PreferenceFormView,
):
    success_message = "Preferences updated"
    form_class = GlobalPreferenceForm
    registry = global_preferences_registry
    permission_required = [
        "dynamic_preferences.change_globalpreferencemodel",
        "dynamic_preferences.view_globalpreferencemodel",
    ]

    def get_layout(self):
        if self.section_name:
            section_names = [self.section_name]
        else:
            section_names = self.form_class.registry.section_objects.keys()
        section_fields = {}
        for section in section_names:
            section_fields[section] = []
            for field in self.form_class.registry[section]:
                section_fields[section].append(f"{section}__{field}")

        return layout.forms.Form(
            hg.C("form"),
            hg.H3(_("Global preferences")),
            layout.components.tabs.Tabs(
                *[
                    layout.components.tabs.Tab(
                        self.form_class.registry.section_objects[section].verbose_name,
                        hg.BaseElement(
                            *[
                                layout.forms.FormField(f)
                                for f in section_fields.get(section)
                            ]
                        ),
                    )
                    for section in section_fields.keys()
                ],
                tabpanel_attributes={"style": "padding-left:0;"},
            ),
            layout.forms.helpers.Submit(),
        )
