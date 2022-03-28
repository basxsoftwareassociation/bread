from bread import menu, views
from bread.contrib.document_templates.models import DocumentTemplate
from bread.contrib.document_templates.views import (
    DocumentTemplateEditView,
    generate_document,
)
from bread.utils import Link, autopath, default_model_paths, model_urlname, urls

urlpatterns = [
    *default_model_paths(
        DocumentTemplate,
        editview=DocumentTemplateEditView,
        readview=DocumentTemplateEditView,
        addview=views.AddView._with(fields=["name", "model", "file"]),
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
