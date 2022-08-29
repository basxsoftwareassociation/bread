import htmlgenerator as hg
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from jinja2.sandbox import SandboxedEnvironment

from basxbread import layout, views

from .models import DocumentTemplate


class DocumentTemplateEditView(views.EditView):
    def get_layout(self):
        modelclass = self.object.model.model_class()
        if modelclass is None:
            return layout.notification.InlineNotification(
                _("Error"),
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )
        column_helper = layout.modal.Modal(
            _("Field explorer"), layout.fieldexplorer.field_help(modelclass), size="lg"
        )

        only_template, only_definition = None, None
        warnings = hg.BaseElement()
        try:
            only_template, only_definition = self.object.missing_variables()
        except Exception as e:
            warnings.append(
                layout.notification.InlineNotification(
                    _("Error in template: "),
                    str(e),
                    kind="error",
                )
            )
        if only_template:
            warnings.append(
                layout.notification.InlineNotification(
                    _("Variables in document but not defined below: "),
                    f"{', '.join(only_template)}",
                    kind="warning",
                )
            )
        if only_definition:
            warnings.append(
                layout.notification.InlineNotification(
                    _("Variables defined below but not used in document: "),
                    f"{', '.join(only_definition)}",
                    kind="warning",
                )
            )

        F = layout.forms.FormField
        fieldstable = layout.forms.Formset.as_datatable(
            hg.C("form.variables.formset"),
            fieldname="variables",
            fields=[
                "name",
                "value",
                F(
                    "template",
                    no_wrapper=True,
                    no_label=True,
                    no_helptext=True,
                    inputelement_attrs={"rows": 1},
                ),
            ],
            formsetfield_kwargs={"extra": 1},
        )
        fieldstable[0][1].insert(
            0,
            layout.button.Button(
                _("Help"),
                buttontype="ghost",
                **column_helper.openerattributes,
            ),
        )

        ret = hg.BaseElement(
            views.header(),
            warnings,
            layout.forms.Form(
                hg.C("form"),
                F("name"),
                F("file"),
                F("filename_template"),
                fieldstable,
                column_helper,
                layout.forms.helpers.Submit(),
            ),
        )
        return ret

    def get_success_url(self):
        return self.request.get_full_path()


def generate_document(request, pk: int, object_pk: int):
    template = DocumentTemplate.objects.get(pk=pk)
    object = template.model.get_object_for_this_type(pk=object_pk)
    filename = f'{template.name}_{str(object).replace(" ", "-")}'

    if template.filename_template:
        value_env = SandboxedEnvironment()
        value_env.filters["map"] = lambda value, map: map.get(value, value)
        try:
            filename = value_env.from_string(template.filename_template).render(
                template.context(object)
            )
        except Exception:
            filename = "FILENAME_ERROR.docx"

    if not filename.endswith(".docx"):
        filename = filename + ".docx"

    response = HttpResponse(
        template.render_with(object),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
