import urllib

import htmlgenerator as hg
from django import forms
from django.contrib import messages
from django.utils.html import mark_safe

from .. import layout as _layout  # prevent name clashing
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
            layout=self.get_layout(),
            instance=self.object,
            baseformclass=form,
        )

    def get_layout(self):
        formfields = filter_fieldlist(self.model, self.fields, for_form=True)
        ret = hg.BaseElement()
        for field in self.fields or formfields:
            if field in formfields:
                ret.append(_layout.form.FormField(field))
            else:
                ret.append(field)
        return hg.BaseElement(
            hg.H3(self.object),
            _layout.form.Form.wrap_with_form(hg.C("form"), ret),
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        if self.request.method != "POST":
            for fieldelement in self.get_layout().filter(
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
                            ]
                        )
                    ),
                )
        return form

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return reverse_model(self.model, "read", kwargs={"pk": self.object.pk})


class BreadView:
    """
    Shortcut to create a subclass with the given attributes
    """

    layout = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def _with(cls, **kwargs):
        return type(f"Custom{cls.__name__}", (cls,), kwargs)

    def get_layout(self):
        if self.layout is None:
            raise RuntimeError(f"'layout' of view {self} is None")
        return self.layout
