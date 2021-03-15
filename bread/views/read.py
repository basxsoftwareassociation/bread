import htmlgenerator as hg
from django.http import HttpResponseNotAllowed

from .. import layout as _layout  # prevent name clashing
from .edit import EditView


# Read view is the same as the edit view but form elements are disabled
class ReadView(EditView):
    template_name = "bread/layout.html"
    accept_global_perms = True
    fields = None
    urlparams = (("pk", int),)

    def post(self, *args, **kwargs):
        return HttpResponseNotAllowed()

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        for field in form.fields.values():
            field.disabled = True
        return form

    def layout(self, request):
        return layoutasreadonly(super().layout(request))

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]


def layoutasreadonly(layout):
    layout.wrap(
        lambda element, ancestors: isinstance(element, _layout.form.Form),
        hg.FIELDSET(disabled="disabled"),
    )

    layout.delete(
        lambda element, ancestors: any(
            [isinstance(a, _layout.form.Form) for a in ancestors]
        )
        and isinstance(element, hg.BUTTON)
    )
    return layout
