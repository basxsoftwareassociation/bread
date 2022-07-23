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
            "action",
            "type",
            "filter",
            "enable",
        ]
    ),
    addview=AddView._with(fields=["description", "model", "type", "action"]),
)
quickregister(
    urlpatterns,
    DateFieldTrigger,
    editview=EditView._with(
        fields=[
            hg.H4(
                layout.ObjectFieldLabel("model"), ": ", layout.ObjectFieldValue("model")
            ),
            "action",
            "offset_type",
            "offset_amount",
            "field",
            "filter",
            "enable",
        ]
    ),
    addview=AddView._with(
        fields=[
            "description",
            "model",
            "action",
            "offset_type",
            "offset_amount",
            "field",
        ]
    ),
)
quickregister(urlpatterns, SendEmail)
