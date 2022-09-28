import typing

import htmlgenerator as hg
from django.urls import path

from basxbread import layout
from basxbread.utils import quickregister
from basxbread.views import AddView, EditView

from .models import DataChangeTrigger, DateFieldTrigger, SendEmail

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
            "field",
            "enable",
        ]
    ),
    addview=AddView._with(fields=["description", "model"]),
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
            "field",
            "filter",
            "enable",
        ]
    ),
    addview=AddView._with(fields=["description", "model"]),
)
quickregister(
    urlpatterns,
    SendEmail,
    editview=EditView._with(
        fields=[
            hg.H4(
                layout.ObjectFieldLabel("model"), ": ", layout.ObjectFieldValue("model")
            ),
            "description",
            "email",
            "subject",
            "message",
        ]
    ),
    addview=AddView._with(fields=["description", "model"]),
)
