import io
import os

import htmlgenerator as hg
from django.apps import apps
from django.http import HttpResponse
from docxtpl import DocxTemplate

from bread import layout, views
from bread.contrib.document_templates.models import DocumentTemplate


class DocumentTemplateEditView(views.EditView):
    def get_layout(self):

        F = layout.forms.FormField

        ret = hg.BaseElement(
            hg.H3(self.object),
            layout.forms.Form(
                hg.C("form"),
                F("name"),
                F("file"),
                layout.forms.helpers.Submit(),
            ),
        )
        return ret

    def get_success_url(self):
        return self.request.get_full_path()


def generate_document_view(request, pk: int, model_string: str, object_id: int):
    object = apps.get_model(model_string).objects.get(id=object_id)
    template_path = DocumentTemplate.objects.get(id=pk).file.path
    docxtpl_template = DocxTemplate(template_path)
    docxtpl_template.render(
        {
            variable: hg.resolve_lookup({"object": object}, variable)
            for variable in (docxtpl_template.get_undeclared_template_variables())
        }
    )

    buf = io.BytesIO()
    docxtpl_template.save(buf)
    buf.seek(0)

    response = HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response[
        "Content-Disposition"
    ] = f'attachment; filename="{os.path.basename(template_path).split(".")[0]}_object{object.id}.docx"'
    return response
