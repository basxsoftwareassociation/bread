from django.utils.translation import gettext_lazy as _

from bread import menu, views
from bread.contrib.document_templates.models import DocumentTemplate
from bread.contrib.document_templates.views import (
    DocumentTemplateEditView,
    generate_document,
)
from bread.utils import Link, autopath, default_model_paths, model_urlname, urls
from bread.views.browse import delete
from bread.views.edit import bulkcopy, generate_copyview

urlpatterns = [
    *default_model_paths(
        DocumentTemplate,
        browseview=views.BrowseView._with(
            rowclickaction=views.BrowseView.gen_rowclickaction("edit"),
            bulkactions=[
                views.browse.BulkAction(
                    "delete", label=_("Delete"), iconname="trash-can", action=delete
                ),
                views.browse.BulkAction(
                    "copy",
                    label=_("Copy"),
                    iconname="copy",
                    action=lambda request, qs: bulkcopy(
                        request,
                        qs,
                        labelfield="name",
                        copy_related_fields=("variables",),
                    ),
                ),
            ],
        ),
        editview=DocumentTemplateEditView,
        readview=DocumentTemplateEditView,
        addview=views.AddView._with(fields=["name", "model", "file"]),
        copyview=generate_copyview(
            DocumentTemplate, labelfield="name", copy_related_fields=("variables",)
        ),
    ),
    autopath(generate_document, model_urlname(DocumentTemplate, "generate_document")),
]

menu.registeritem(
    menu.Item(
        Link(
            href=urls.reverse_model(DocumentTemplate, "browse"),
            label="Document Templates",
            iconname="document--blank",
        ),
        menu.Group("Document Templates", iconname="document--blank"),
    )
)
