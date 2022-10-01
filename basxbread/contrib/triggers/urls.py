import typing

import htmlgenerator as hg
from django.urls import path
from django.utils.translation import gettext_lazy as _

from basxbread import layout
from basxbread.utils import quickregister, reverse_model
from basxbread.views import AddView, EditView

from .models import DataChangeTrigger, DateFieldTrigger, SendEmail


def help_button(context):
    column_helper = layout.modal.Modal(
        _("Field explorer"),
        layout.fieldexplorer.field_help(context["object"].model.model_class()),
        size="lg",
    )
    return hg.BaseElement(
        layout.button.Button(
            _("Help"), buttontype="ghost", **column_helper.openerattributes
        ),
        column_helper,
    )


def field_help_button(context):
    column_helper = layout.modal.Modal(
        _("Available fields"),
        layout.fieldexplorer.field_help(context["object"].model.model_class(), 0),
        size="sm",
    )
    return hg.BaseElement(
        layout.button.Button(
            _("Show available fields"),
            buttontype="ghost",
            **column_helper.openerattributes
        ),
        column_helper,
    )


urlpatterns: typing.List[path] = []
quickregister(
    urlpatterns,
    DataChangeTrigger,
    editview=EditView._with(
        fields=[
            hg.H4(
                layout.ObjectFieldLabel("model"), ": ", layout.ObjectFieldValue("model")
            ),
            "description",
            "action",
            "type",
            "filter",
            hg.F(field_help_button),
            "field",
            "enable",
        ],
    ),
    addview=AddView._with(
        fields=["description", "model"],
        get_success_url=lambda s: reverse_model(
            s.model, "edit", kwargs={"pk": s.object.pk}
        ),
    ),
)
quickregister(
    urlpatterns,
    DateFieldTrigger,
    editview=EditView._with(
        fields=[
            hg.H4(
                layout.ObjectFieldLabel("model"), ": ", layout.ObjectFieldValue("model")
            ),
            "description",
            "action",
            "offset_type",
            "offset_amount",
            hg.F(help_button),
            "field",
            "filter",
            "enable",
        ]
    ),
    addview=AddView._with(
        fields=["description", "model"],
        get_success_url=lambda s: reverse_model(
            s.model, "edit", kwargs={"pk": s.object.pk}
        ),
    ),
)


quickregister(
    urlpatterns,
    SendEmail,
    editview=EditView._with(
        fields=[
            hg.H4(
                layout.ObjectFieldLabel("model"), ": ", layout.ObjectFieldValue("model")
            ),
            hg.F(help_button),
            "description",
            "email",
            "subject",
            "message",
        ]
    ),
    addview=AddView._with(
        fields=["description", "model"],
        get_success_url=lambda s: reverse_model(
            s.model, "edit", kwargs={"pk": s.object.pk}
        ),
    ),
)
