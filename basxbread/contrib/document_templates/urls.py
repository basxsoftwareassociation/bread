import shutil

from django.utils.translation import gettext_lazy as _

from basxbread import menu, views
from basxbread.utils import Link, autopath, default_model_paths, model_urlname, urls
from basxbread.views.browse import delete
from basxbread.views.edit import bulkcopy, generate_copyview

from .models import DocumentTemplate
from .views import (
    DocumentTemplateEditView,
    generate_document_download,
    generate_document_download_pdf,
)

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
    autopath(
        generate_document_download, model_urlname(DocumentTemplate, "generate_document")
    ),
]
if shutil.which("libreoffice") is not None:
    urlpatterns.append(
        autopath(
            generate_document_download_pdf,
            model_urlname(DocumentTemplate, "generate_document_pdf"),
        )
    )

menu.registeritem(
    menu.Item(
        Link(
            href=urls.reverse_model(DocumentTemplate, "browse"),
            label=DocumentTemplate._meta.verbose_name_plural,
            iconname="document--blank",
            permissions=[
                f"{DocumentTemplate._meta.app_label}.view_{DocumentTemplate._meta.model_name}"
            ],
        ),
        menu.Group(
            DocumentTemplate._meta.verbose_name_plural, iconname="document--blank"
        ),
    )
)
