import json

import htmlgenerator as hg
from django.core import checks
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from djangoql.schema import DjangoQLSchema
from djangoql.serializers import DjangoQLSchemaSerializer

from bread.layout.components.forms import widgets


class DjangoQLSearch(hg.DIV):
    django_widget = None

    def __init__(
        self,
        size="xl",
        placeholder=None,
        widgetattributes=None,
        backend=None,
        resultcontainerid=None,
        show_result_container=True,
        resultcontainer_onload_js=None,
        disabled=False,
        **kwargs,
    ):

        if backend:
            if resultcontainerid is None:
                resultcontainerid = f"search-result-{hg.html_id((self, backend.url))}"
            widgetattributes["hx_get"] = backend.url
            widgetattributes["hx_trigger"] = "changed, click, keyup changed delay:500ms"
            widgetattributes["hx_target"] = hg.format("#{}", resultcontainerid)
            widgetattributes["hx_indicator"] = hg.format(
                "#{}-indicator", resultcontainerid
            )
            widgetattributes["name"] = backend.query_parameter

        def introspections(context):
            return json.dumps(
                DjangoQLSchemaSerializer().serialize(
                    DjangoQLSchema(
                        hg.resolve_lazy(boundfield, context).value().queryset.model
                    )
                )
            )

        if boundfield:
            self.append(
                hg.SCRIPT(
                    hg.format(
                        """
                        document.addEventListener("DOMContentLoaded", () => DjangoQL.DOMReady(function () {{
                            new DjangoQL({{
                            introspections: {},
                            selector: 'textarea[name={}]',
                            syntaxHelp: '{}',
                            autoResize: false
                            }});
                        }}));
                    """,
                        hg.F(introspections),
                        inputelement_attrs.get("name"),
                        reverse("reporthelp"),
                        autoescape=False,
                    ),
                )
            )
