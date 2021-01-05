from django import forms

from .. import layout as _layout  # prevent name clashing
from ..forms.forms import breadmodelform_factory
from ..layout.components.form import FormField
from ..utils import filter_fieldlist


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
            layout=self.layout(self.request),
            instance=self.object,
            baseformclass=form,
        )

    def formlayout(self, request):
        return _layout.BaseElement(
            *[
                _layout.form.FormField(field)
                for field in filter_fieldlist(self.model, self.fields, for_form=True)
            ]
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        if self.request.method != "POST":
            for fieldelement in self.layout(self.request).filter(
                lambda element, ancestors: isinstance(element, FormField)
            ):
                if fieldelement.fieldname in self.request.GET:
                    form.fields[fieldelement.fieldname].widget = forms.HiddenInput(
                        attrs=form.fields[fieldelement.fieldname].widget.attrs
                    )
        return form


class BreadView:
    """
    Enforces the definition of a layout method which is used to render the view
    Shortcut to create a subclass with the given attributes
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        assert hasattr(cls, "layout") and callable(
            cls.layout
        ), f"{cls} needs to implement a method 'layout(request)'"

    @classmethod
    def _with(cls, **kwargs):
        return type(f"Custom{cls.__name__}", (cls,), kwargs)
