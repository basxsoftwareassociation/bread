import os

import htmlgenerator as hg
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files import File
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from docxtpl import DocxTemplate

from bread import layout, views
from bread.contrib.document_templates.models import DocumentTemplate
from bread.contrib.reports.fields.queryfield import QuerysetFormWidget


class DocumentTemplateEditView(views.EditView):
    def get_layout(self):
        modelclass = self.object.model.model_class()
        if modelclass is None:
            return layout.notification.InlineNotification(
                "Error",
                f"Model '{self.object.model}' does no longer exist.",
                kind="error",
            )

        F = layout.forms.FormField

        ret = hg.BaseElement(
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=staticfiles_storage.url("djangoql/css/completion.css"),
            ),
            hg.SCRIPT(src=staticfiles_storage.url("djangoql/js/completion.js")),
            hg.H3(self.object),
            layout.forms.Form(
                hg.C("form"),
                hg.DIV(
                    _("Base model"),
                    ": ",
                    hg.C("object.model"),
                    style="margin: 2rem 0 2rem 0",
                ),
                F("name"),
                F("file"),
                F(
                    "filter",
                    widgetclass=QuerysetFormWidget,
                    inputelement_attrs={"rows": 1},
                    style="width: 100%",
                ),
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

    def form_valid(self, *args, **kwargs):
        ret = super().form_valid(*args, **kwargs)
        self.object.documents.all().delete()

        template_path = self.object.file.path
        template = DocxTemplate(template_path)
        variables = template.get_undeclared_template_variables()

        for object in self.object.filter.queryset:
            template.render(
                {
                    variable: hg.resolve_lookup({"object": object}, variable)
                    for variable in variables
                }
            )
            document_name = f"rendered_{os.path.basename(template_path).split('.')[0]}_object{object.id}.doc"

            if not os.path.exists("tmp"):
                os.makedirs("tmp")
            document_path = f"tmp/{document_name}"
            template.save(document_path)
            with open(document_path, mode="rb") as f:
                self.object.documents.create(file=File(f, name=document_name))
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
