import typing
import urllib

import htmlgenerator as hg
from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.urls import NoReverseMatch
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from .. import layout, menu
from ..forms.forms import modelform_factory
from ..layout.skeleton import default_page_layout
from ..utils import ModelHref, filter_fieldlist, reverse_model

R = layout.grid.Row
C = layout.grid.Col


def header():
    editbutton = layout.button.Button(
        _("Edit"),
        buttontype="ghost",
        icon="edit",
        notext=True,
    ).as_href(ModelHref.from_object(hg.C("object"), "edit"))
    readbutton = layout.button.Button(
        _("Read"),
        buttontype="ghost",
        icon="view",
        notext=True,
    ).as_href(ModelHref.from_object(hg.C("object"), "read"))

    deletebutton = layout.button.Button(
        _("Delete"),
        buttontype="tertiary",
        icon="trash-can",
        notext=True,
        style="border-color: red; background-color: inherit",
    ).as_submit(
        ModelHref.from_object(hg.C("object"), "delete"),
        confirm_text=hg.format(
            _("Are you sure you want to delete {}?"), hg.EM(hg.C("object"))
        ),
    )
    deletebutton[0][3].attributes = hg.merge_html_attrs(
        deletebutton[0][3].attributes, {"style": "fill: red; color: red;"}
    )

    copybutton = layout.button.Button(
        _("Copy"),
        buttontype="ghost",
        icon="copy",
        notext=True,
    ).as_submit(
        ModelHref.from_object(hg.C("object"), "copy"),
        confirm_text=hg.format(
            _("Are you sure you want to copy {}?"), hg.EM(hg.C("object"))
        ),
    )

    return hg.DIV(
        hg.H3(
            hg.If(
                hg.C("object"),
                hg.BaseElement(
                    hg.SPAN(hg.C("object")),
                    hg.If(
                        hg.C(f"request.GET.{settings.HIDEMENUS_URLPARAMETER}"),
                        None,
                        hg.SPAN(
                            hg.If(
                                hg.C("request").resolver_match.url_name.endswith(
                                    ".read"
                                ),
                                editbutton,
                                readbutton,
                            ),
                            copybutton,
                            layout.button.PrintPageButton(buttontype="ghost"),
                            deletebutton,
                            _class="no-print",
                            style="margin-bottom: 1rem; margin-left: 1rem",
                            width=3,
                        ),
                    ),
                ),
                hg.SPAN(hg.format(_("Add {}"), hg.C("view").model._meta.verbose_name)),
            ),
        ),
        style="padding-top: 1rem",
    )


class CustomFormMixin:
    """This mixin takes care of the following things:
    - Allows to pass initial values for form fields via the GET query
    - Converts n-to-many fields into inline forms
    - Set GenericForeignKey fields before saving (not supported by default in django)
    - If "next" is in the GET query redirect to that location on success
    - If default_success_page
    """

    def get_initial(self, *args, **kwargs):
        ret = super().get_initial(*args, **kwargs)
        ret.update(self.request.GET.dict())
        return ret

    def get_form_class(self, form=forms.models.ModelForm):
        return modelform_factory(
            request=self.request,
            model=self.model,
            layout=self._get_layout_cached(),
            instance=self.object,
            baseformclass=form,
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        # if self.request.method != "POST":
        for fieldelement in self._get_layout_cached().filter(
            lambda element, ancestors: isinstance(
                element, layout.forms.fields.FormFieldMarker
            )
        ):
            if (
                fieldelement.fieldname in self.request.GET
                and fieldelement.fieldname + "_nohide" not in self.request.GET
            ):
                form.fields[fieldelement.fieldname].widget = forms.HiddenInput(
                    attrs=form.fields[fieldelement.fieldname].widget.attrs
                )
        if self.request.method == "POST":
            if form.errors and self.ajax_urlparameter not in self.request.GET:
                messages.error(
                    self.request,
                    mark_safe(
                        "<br/>".join(
                            [
                                f"<em>{form.fields[field].label}</em>: "
                                f"{', '.join(msg if isinstance(msg, list) else [msg])}"
                                for field, msg in form.errors.items()
                                if field != "__all__"
                            ]
                        )
                    ),
                )
        return form

    def get_layout(self):
        if hasattr(self, "layout") and self.layout is not None:
            ret = self.layout
        else:
            direct_model_formfields = filter_fieldlist(
                self.model,
                [f for f in self.fields if isinstance(f, str)]
                if (self.fields is not None)
                else None,
                for_form=True,
            )
            declared_formfields = self.fields or direct_model_formfields
            inlineforms = {}
            for i, field in enumerate(list(declared_formfields)):
                if isinstance(field, str) and "." in field:
                    declared_formfields.remove(field)
                    basefield, inlinefield = field.split(".", 1)
                    if basefield not in inlineforms:
                        inlineforms[basefield] = []
                        declared_formfields.insert(i, basefield)
                    inlineforms[basefield].append(inlinefield)

            ret = hg.BaseElement()
            for field in declared_formfields:
                if field in direct_model_formfields:
                    ret.append(layout.forms.FormField(field))
                elif isinstance(field, str) and field in inlineforms:
                    ret.append(
                        layout.forms.Formset.as_datatable(
                            hg.C(layout.forms.fields.DEFAULT_FORM_CONTEXTNAME)[
                                field
                            ].formset,
                            fieldname=field,
                            title=hg.C(layout.forms.fields.DEFAULT_FORM_CONTEXTNAME)[
                                field
                            ].label,
                            fields=inlineforms[field],
                            formsetfield_kwargs={
                                "extra": 1,
                            },
                        )
                    )
                else:
                    ret.append(field)

        if self.ajax_urlparameter in self.request.GET:
            return layout.forms.Form(hg.C("form"), ret)

        # wrap with form will add a submit button
        return hg.DIV(
            header(),
            layout.tile.Tile(
                layout.forms.Form(hg.C("form"), ret, layout.forms.helpers.Submit()),
            ),
        )

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

        success_url = getattr(self, "success_url", "")
        if success_url:
            return success_url

        try:
            ret = str(
                reverse_model(
                    self.model, self.default_success_page, kwargs={"pk": self.object.pk}
                )
            )

        except NoReverseMatch:
            ret = self.request.get_full_path()

        return ret


class BaseView:
    """
    Shortcut to create a subclass with the given attributes
    """

    layout: typing.Optional[hg.BaseElement] = None
    _layout_cached: typing.Optional[hg.BaseElement] = None
    ajax_urlparameter = settings.AJAX_URLPARAMETER
    hidemenus_urlparameter = settings.HIDEMENUS_URLPARAMETER
    page_layout: typing.Optional[
        typing.Callable[[menu.Menu, hg.BaseElement, bool], hg.BaseElement]
    ] = None
    urlparams: typing.Iterable[typing.Tuple[str, typing.Type]] = ()

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
        self.hidemenus_urlparameter = kwargs.get(
            "hidemenus_urlparameter", getattr(self, "hidemenus_urlparameter")
        )

        self.page_layout = (
            kwargs.get("page_layout", getattr(self, "page_layout"))
            or default_page_layout
        )

    def get_layout(self):
        """Returns the layout for this view, returns the ``layout`` attribute by default.
        Either set the ``layout`` attribute or override this method."""
        if self.layout is None:
            raise RuntimeError(f"'layout' of view {self} is None")
        return self.layout

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault("content_type", self.content_type)
        ret = self._get_layout_cached()
        if self.ajax_urlparameter not in self.request.GET:
            ret = self.page_layout(
                menu.main,
                ret,
                hidemenus=self.hidemenus_urlparameter in self.request.GET,
            )

        return layout.render(self.request, ret, context, **response_kwargs)

    def _get_layout_cached(self):
        """Used for caching layouts, only basxbread-internal"""
        if self._layout_cached is None:
            self._layout_cached = self.get_layout()
        return self._layout_cached
