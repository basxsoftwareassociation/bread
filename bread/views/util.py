from django import forms

from ..forms.forms import breadmodelform_factory
from ..layout.components.form import FormField


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
            layout=self.layout,
            instance=self.object,
            baseformclass=form,
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        if self.request.method != "POST":
            for fieldelement in self.layout.filter(
                lambda element, ancestors: isinstance(element, FormField)
            ):
                if fieldelement.fieldname in self.request.GET:
                    form.fields[fieldelement.fieldname].widget = forms.HiddenInput(
                        attrs=form.fields[fieldelement.fieldname].widget.attrs
                    )
        return form
