from django.urls import path
from django.utils.translation import gettext_lazy as _

from basxbread import menu, utils

from . import views

urlpatterns = [
    path("test", views.test, name="modeledit.test"),
]

menu.registeritem(
    menu.Item(
        utils.Link(
            utils.reverse("modeledit.test"),
            _("Modeledit"),
        ),
        _("Modeledit"),
    )
)
