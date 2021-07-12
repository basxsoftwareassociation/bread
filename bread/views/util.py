import urllib

import htmlgenerator as hg
from django import forms
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import mark_safe

from .. import layout as breadlayout  # prevent name clashing
from ..forms.forms import breadmodelform_factory
from ..layout.components.form import FormField
from ..utils import filter_fieldlist, reverse_model


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

    def get_template_names(self):
        # TODO: use only htmlgenerator instead of django templates
        if self.ajax_urlparameter in self.request.GET:
            return "bread/base_ajax.html"
        return "bread/base.html"
