from django.utils.translation import gettext_lazy as _

from ..menu import Link
from ..utils.urls import registermodelurl, registerurl
from .add import AddView  # noqa
from .browse import BrowseView, TreeView  # noqa
from .delete import DeleteView  # noqa
from .edit import EditView  # noqa
from .read import ReadView  # noqa
from .system import BreadLoginView, DataModel  # noqa

registerurl("login", check_function=lambda u: True)(BreadLoginView.as_view())
registerurl("datamodel")(DataModel.as_view())


def register_default_modelviews(
    model,
    browseview=BrowseView,
    readview=ReadView,
    editview=EditView,
    addview=AddView,
    deleteview=DeleteView,
):
    if browseview is not None:
        registermodelurl(
            model,
            "browse",
            browseview,
            object_actions=[
                Link.from_objectaction("edit", _("Edit"), "edit"),
                Link.from_objectaction("delete", _("Delete"), "trash-can"),
            ],
        )
    if readview is not None:
        registermodelurl(model, "read", readview)
    if editview is not None:
        registermodelurl(model, "edit", editview)
    if addview is not None:
        registermodelurl(model, "add", addview)
    if deleteview is not None:
        registermodelurl(model, "delete", deleteview)
