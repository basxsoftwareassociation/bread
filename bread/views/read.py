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

    def layout(self, request):
        ret = super().layout(request)
        ret.wrap(
            lambda element, ancestors: isinstance(element, _layout.form.Form),
            _layout.FIELDSET(disabled="disabled"),
        )

        ret.delete(
            lambda element, ancestors: isinstance(element, _layout.BUTTON)
            and element.attributes["type"] == "submit"
        )
        return ret

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]
