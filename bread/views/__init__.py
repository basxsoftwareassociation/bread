from django.utils.translation import gettext_lazy as _

from ..menu import Link
from ..utils.urls import registermodelurl, registerurl
from .add import AddView
from .browse import BrowseView
from .delete import DeleteView
from .edit import EditView, generate_copyview
from .read import ReadView
from .system import BreadLoginView, BreadLogoutView, DataModel

registerurl("login", check_function=lambda u: True)(BreadLoginView.as_view())
registerurl("logout", check_function=lambda u: u.is_authenticated)(
    BreadLogoutView.as_view()
)
registerurl("datamodel")(DataModel.as_view())


def register_default_modelviews(
    model,
    browseview=BrowseView,
    readview=ReadView,
    editview=EditView,
    addview=AddView,
    deleteview=DeleteView,
    copyview=True,
):
    if browseview is not None:
        registermodelurl(
            model,
            "browse",
            browseview,
            object_actions=browseview.object_actions
            or [
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
    if copyview is not None:
        if copyview is True:
            copyview = generate_copyview(model)
        registermodelurl(model, "copy", copyview)
