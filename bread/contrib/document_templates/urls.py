from django.urls import path

from bread import menu, views
from bread.contrib.document_templates.models import DocumentTemplate
from bread.contrib.document_templates.views import (
    DocumentTemplateEditView,
    generate_document_view,
)
from bread.utils import Link, default_model_paths, urls

urlpatterns = [
    *default_model_paths(
        DocumentTemplate,
        editview=DocumentTemplateEditView,
        addview=views.AddView._with(
            fields=["name", "model"],
            get_success_url=lambda s: urls.reverse_model(
                DocumentTemplate, "edit", kwargs={"pk": s.object.pk}
            ),
        ),
        browseview=views.BrowseView._with(
            rowclickaction=views.BrowseView.gen_rowclickaction("edit"),
        ),
    ),
    path(
        "document-template/<int:template_id>/object/<int:object_id>",
        generate_document_view,
        name="generate-document",
    ),
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
