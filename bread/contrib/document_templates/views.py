import htmlgenerator as hg
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from bread import layout, views
from bread.contrib.document_templates.models import DocumentTemplate


class DocumentTemplateEditView(views.EditView):
    def get_layout(self):
        modelclass = self.object.model.model_class()
        if modelclass is None:
            return layout.notification.InlineNotification(
                "Error",
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )
        column_helper = layout.get_attribute_description_modal(modelclass)

        F = layout.forms.FormField

        ret = hg.BaseElement(
            hg.H3(self.object),
            layout.forms.Form(
                hg.C("form"),
                F("name"),
                F("file"),
                layout.forms.FormsetField.as_datatable(
                    "variables",
                    ["name", "value"],
                    formsetfield_kwargs={"extra": 1},
                ),
                column_helper,
                layout.button.Button(
                    _("Help"),
                    buttontype="ghost",
                    style="margin-top: 1rem",
                    **column_helper.openerattributes,
                ),
                layout.forms.helpers.Submit(),
            ),
        )
        return ret
        # for variable in (docxtpl_template.get_undeclared_template_variables())

    def get_success_url(self):
        return self.request.get_full_path()


def generate_document(request, pk: int, object_pk: int):
    template = DocumentTemplate.objects.get(pk=pk)
    object = template.model.get_object_for_this_type(pk=object_pk)
    response = HttpResponse(
        template.render_with(object),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response[
        "Content-Disposition"
    ] = f'attachment; filename="{template.name}_{str(object).replace(" ", "-")}.docx"'
    return response
