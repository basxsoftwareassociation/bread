import typing

import htmlgenerator as hg
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.module_loading import import_string
from dynamic_preferences import views as preferences_views
from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.registries import global_preferences_registry

from bread import layout as breadlayout
from bread import menu


class PreferencesView(SuccessMessageMixin, preferences_views.PreferenceFormView):

    layout: typing.Optional[hg.BaseElement] = None
    _layout_cached: typing.Optional[hg.BaseElement] = None
    page_layout: typing.Optional[
        typing.Callable[[menu.Menu, hg.BaseElement], hg.BaseElement]
    ] = None
    success_message = "Preferences updated"
    form_class = GlobalPreferenceForm
    registry = global_preferences_registry

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.page_layout = (
            kwargs.get("page_layout", getattr(self, "page_layout"))
            or settings.DEFAULT_PAGE_LAYOUT
        )
        if isinstance(self.page_layout, str):
            self.page_layout = import_string(self.page_layout)

    def get_page_layout(self, menu, content_layout):
        return self.page_layout(menu, content_layout)

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

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault("content_type", self.content_type)
        ret = self.get_layout()
        ret = self.get_page_layout(menu.main, ret)

        return breadlayout.render(self.request, ret, context, **response_kwargs)
