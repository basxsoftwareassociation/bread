import htmlgenerator as hg
from django.http import HttpResponseNotAllowed

from .. import layout as _layout  # prevent name clashing
from ..forms.fields import FormsetField
from .edit import EditView


# Read view is the same as the edit view but form elements are disabled
class ReadView(EditView):
    """TODO: documentation"""

    template_name = "bread/base.html"
    accept_global_perms = True
    fields = None
    urlparams = (("pk", int),)

    def post(self, *args, **kwargs):
        return HttpResponseNotAllowed(["GET"])

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        for field in form.fields.values():
            field.disabled = True
            if isinstance(field, FormsetField):
                for subfield in field.formsetclass.form.base_fields.values():
                    subfield.disabled = True
        return form

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["layout"] = layoutasreadonly(context["layout"])
        return context

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]


def layoutasreadonly(layout):
    layout.wrap(
        lambda element, ancestors: isinstance(element, _layout.form.Form)
        and element.standalone,
        hg.FIELDSET(readonly="true"),
    )

    layout.delete(
        lambda element, ancestors: any(
            [isinstance(a, _layout.form.Form) for a in ancestors]
        )
        and (
            isinstance(
                element,
                hg.BUTTON,
            )
            or getattr(element, "attributes", {}).get("type") == "submit"
        )
    )
    for form in layout.filter(lambda element, ancestors: isinstance(element, hg.FORM)):
        form.attributes["onsubmit"] = "return false;"
    return layout
