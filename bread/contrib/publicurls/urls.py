from urllib.parse import urlparse

import htmlgenerator as hg
from django.conf import settings
from django.core.signing import SignatureExpired, TimestampSigner
from django.http import HttpResponseRedirect
from django.http.request import QueryDict
from django.urls import path, resolve
from django.utils.translation import gettext as _
from guardian.utils import get_anonymous_user

from bread import layout, menu, views
from bread.utils import ModelHref, aslayout, default_model_paths

from . import models


@aslayout
def publicurlview(request, token):
    # unpack and verify token
    token, salt = token.rsplit(":", 1)
    signer = TimestampSigner(salt=salt)
    pk = int(signer.unsign(token))
    url = models.PublicURL.objects.get(pk=pk)
    if url.valid_for is not None:
        try:
            pk = int(signer.unsign(token, max_age=url.valid_for))
        except SignatureExpired:
            return hg.DIV(
                _("Link has expired"), style="margin: auto auto; text-align: center"
            )

    # call actual view
    match = resolve(url.url)
    request.resolver_match = match  # make sure view uses correct resolver_match
    request.user = get_anonymous_user()
    request.GET = QueryDict(urlparse(url.url).query, mutable=True)
    request.GET[settings.HIDEMENUS_URLPARAMETER] = True
    response = match.func(request, *match.args, **match.kwargs)  # call view function

    # check if a form has successfully been submited, if so return a thank you page
    if (
        request.method == "POST"
        and url.has_form
        and isinstance(response, HttpResponseRedirect)
    ):
        return hg.DIV(
            hg.H2(_("Data has been submitted")),
            hg.H4(url.thankyou_text),
            hg.A(_("Back"), href=request.get_full_path()),
            hg.SCRIPT(
                "if (window.history.replaceState)"
                "{window.history.replaceState(null, null, window.location.href);}"
            ),
            style="margin: auto auto; text-align: center",
        )
    return response


urlpatterns = [
    path("public/<str:token>", publicurlview, name="publicurl"),
    *default_model_paths(
        models.PublicURL,
        browseview=views.BrowseView._with(
            columns=[
                "name",
                "url",
                layout.datatable.DataTableColumn(
                    _("Public URL"),
                    hg.F(
                        lambda c: hg.SPAN(
                            c["row"].absolute_publicurl(c["request"]),
                            style="word-break: break-all",
                        )
                    ),
                ),
                layout.datatable.DataTableColumn(
                    "",
                    hg.F(
                        lambda c: layout.button.Button(
                            icon="copy",
                            buttontype="ghost",
                            small=True,
                            onclick=f"navigator.clipboard.writeText('{c['row'].absolute_publicurl(c['request'])}');",
                        )
                    ),
                ),
                "created",
                "valid_for",
            ],
            rowactions=(views.BrowseView.editlink(), views.BrowseView.deletelink()),
        ),
    ),
]

menu.registeritem(
    menu.Item(
        group=models.PublicURL._meta.verbose_name_plural,
        link=menu.Link(
            href=ModelHref(models.PublicURL, "browse"),
            label=models.PublicURL._meta.verbose_name_plural,
            iconname="link",
        ),
    )
)
