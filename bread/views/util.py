import urllib

import htmlgenerator as hg
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, StreamingHttpResponse
from django.template.context import _builtin_context_processors
from django.utils.html import mark_safe, strip_tags
from django.utils.module_loading import import_string
from django.utils.translation import get_language

from .. import layout  # prevent name clashing
from .. import layout as breadlayout
from ..forms.forms import breadmodelform_factory
from ..layout.components.form import FormField
from ..utils import filter_fieldlist, reverse_model

CONTEXT_PROCESSORS = tuple(
    import_string(path)
    for path in _builtin_context_processors + tuple(settings.CONTEXT_PROCESSORS)
)


class CustomFormMixin:
    """This mixin takes care of the following things:
    - Allows to pass initial values for form fields via the GET query
    - Converts n-to-many fields into inline forms
    - Set GenericForeignKey fields before saving (not supported by default in django)
    - If "next" is in the GET query redirect to that location on success
    """

    def get_initial(self, *args, **kwargs):
        ret = super().get_initial(*args, **kwargs)
        ret.update(self.request.GET.dict())
        return ret

    def get_form_class(self, form=forms.models.ModelForm):
        return breadmodelform_factory(
            request=self.request,
            model=self.model,
            layout=self._get_layout_cached(),
            instance=self.object,
            baseformclass=form,
        )

    def get_layout(self):
        formfields = filter_fieldlist(self.model, self.fields, for_form=True)
        ret = hg.BaseElement()
        for field in self.fields or formfields:
            if field in formfields:
                ret.append(breadlayout.form.FormField(field))
            else:
                ret.append(field)
        return hg.BaseElement(
            hg.H3(self.object),
            breadlayout.form.Form.wrap_with_form(hg.C("form"), ret),
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        if self.request.method != "POST":
            for fieldelement in self._get_layout_cached().filter(
                lambda element, ancestors: isinstance(element, FormField)
            ):
                if (
                    fieldelement.fieldname in self.request.GET
                    and fieldelement.fieldname + "_nohide" not in self.request.GET
                ):
                    form.fields[fieldelement.fieldname].widget = forms.HiddenInput(
                        attrs=form.fields[fieldelement.fieldname].widget.attrs
                    )
        else:
            if form.errors:
                messages.error(
                    self.request,
                    mark_safe(
                        "<br/>".join(
                            [
                                f"<em>{form.fields[field].label}</em>: {', '.join(msg if isinstance(msg, list) else [msg])}"
                                for field, msg in form.errors.items()
                                if field != "__all__"
                            ]
                        )
                    ),
                )
        return form

    def form_valid(self, *args, **kwargs):
        ret = super().form_valid(*args, **kwargs)
        if self.ajax_urlparameter in self.request.GET:
            ret = HttpResponse("OK")
            # This header will be processed by htmx
            # in order to reload the whole page automatically
            # (instead of doing the redirect which is required for
            # normal POST submission responses
            ret["HX-Refresh"] = "true"
        return ret

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse_model(self.model, "read", kwargs={"pk": self.object.pk})


class BreadView:
    """
    Shortcut to create a subclass with the given attributes
    """

    layout = None
    _layout_cached = None
    ajax_urlparameter = "asajax"

    @classmethod
    def _with(cls, **kwargs):
        """
        Helper which allows to quickly create a parameterized view without needing to
        implement a new class in user code. E.g. BrowseView.with(fields=["name", "email"])
        """
        return type(f"Custom{cls.__name__}", (cls,), kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ajax_urlparameter = kwargs.get(
            "ajax_urlparameter", getattr(self, "ajax_urlparameter")
        )

    def _get_layout_cached(self):
        """Used for caching layouts, only bread-internal"""
        if self._layout_cached is None:
            self._layout_cached = self.get_layout()
        return self._layout_cached

    def get_layout(self):
        """Returns the layout for this view, returns the ``layout`` attribute by default"""
        if self.layout is None:
            raise RuntimeError(f"'layout' of view {self} is None")
        return self.layout

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault("content_type", self.content_type)

        context = dict(context)
        for processor in CONTEXT_PROCESSORS:
            context.update(processor(self.request))

        ret = self._get_layout_cached()
        if self.ajax_urlparameter not in self.request.GET:
            ret = default_ui_shell(ret)
        return HttpResponse(
            hg.render(ret, self.get_context_data(**context)), **response_kwargs
        )
        return StreamingHttpResponse(
            ret.render(self.get_context_data(**context)),
            **response_kwargs,
        )


def default_ui_shell(pagecontent):
    from bread import menu

    static = staticfiles_storage.url

    return hg.HTML(
        hg.HEAD(
            hg.META(charset="utf-8"),
            hg.META(name="viewport", content="width=device-width, initial-scale=1"),
            hg.TITLE(
                hg.F(
                    lambda c, e: strip_tags(c.get("pagetitle", c.get("PLATFORMNAME")))
                    + " | "
                    + strip_tags(c.get("PLATFORMNAME"))
                )
            ),
            hg.LINK(rel="shortcut icon", href=static("logo.png")),
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=static("css/bread-main.css"),
                media="all",
            ),
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=static("djangoql/css/completion.css"),
            ),
        ),
        hg.BODY(
            layout.shell_header.ShellHeader(
                hg.C("PLATFORMNAME"),
                hg.C("COMPANYNAME"),
            ),
            hg.If(
                hg.C("request.user.is_authenticated"),
                layout.sidenav.SideNav(menu.main),
            ),
            hg.DIV(
                hg.Iterator(
                    hg.C("messages"),
                    "message",
                    layout.notification.ToastNotification(
                        message=hg.C("message.tags.capitalize"),
                        details=hg.C("message.message"),
                        kind=hg.C("message.level_tag"),
                        hidetimestamp=True,
                        style=hg.BaseElement(
                            "opacity: 0; animation: ",
                            hg.F(lambda c, e: 4 + 3 * c["message_index"]),
                            "s ease-in-out notification",
                        ),
                        onload=hg.BaseElement(
                            "setTimeout(() => this.style.display = 'None', ",
                            hg.F(lambda c, e: (4 + 3 * c["message_index"]) * 1000),
                            ")",
                        ),
                    ),
                ),
                style="position: fixed; right: 0; z-index: 999",
            ),
            hg.DIV(pagecontent, _class="bx--content"),
            hg.SCRIPT(src=static("js/main.js")),
            hg.SCRIPT(src=static("js/bliss.min.js")),
            hg.SCRIPT(src=static("js/htmx.min.js")),
            hg.SCRIPT(src=static("design/carbon_design/js/carbon-components.js")),
            hg.SCRIPT(src=static("djangoql/js/completion.js")),
            hg.SCRIPT("CarbonComponents.watch(document);"),
        ),
        doctype=True,
        _class="no-js",
        lang=get_language(),
    )
