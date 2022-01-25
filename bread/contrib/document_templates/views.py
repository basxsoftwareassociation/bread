import os

import htmlgenerator as hg
from django.conf import settings
from django.core.files import File
from django.http import HttpResponseRedirect
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
                F("model"),
                F("file"),
                layout.forms.helpers.Submit(),
            ),
            hg.H4("Rendered documents:"),
            hg.Iterator(
                hg.F(lambda c: c["object"].documents.all()),
                "document",
                hg.DIV(
                    hg.A(
                        hg.C("document").file,
                        href=hg.format(
                            "{}/{}", settings.MEDIA_URL, hg.C("document").file
                        ),
                    ),
                ),
            ),
        )
        return ret

    def get_success_url(self):
        return self.request.get_full_path()


def generate_document_view(request, template_id: int, object_id: int):
    document_template = DocumentTemplate.objects.get(id=template_id)
    object = document_template.model.model_class().objects.get(id=object_id)
    template_path = document_template.file.path
    template = DocxTemplate(template_path)
    variables = template.get_undeclared_template_variables()

    template.render(
        {
            variable: hg.resolve_lookup({"object": object}, variable)
            for variable in variables
        }
    )
    document_name = f"rendered_{os.path.basename(template_path).split('.')[0]}_object{object.id}.doc"

    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    tmp_document_path = f"tmp/{document_name}"
    template.save(tmp_document_path)
    with open(tmp_document_path, mode="rb") as f:
        document = document_template.documents.create(file=File(f, name=document_name))
    return HttpResponseRedirect(f"{settings.MEDIA_URL}{document.file.name}")
