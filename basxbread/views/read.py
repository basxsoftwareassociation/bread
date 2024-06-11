import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView as DjangoReadView
from guardian.mixins import PermissionRequiredMixin

from .. import layout as _layout  # prevent name clashing
from ..formatters import format_value
from ..utils import ModelHref, expand_ALL_constant
from .util import BaseView, header


class ReadView(
    BaseView,
    PermissionRequiredMixin,
    DjangoReadView,
):
    accept_global_perms = True
    fields = ["__all__"]
    urlparams = (("pk", int),)

    def __init__(self, *args, **kwargs):
        self.fields = expand_ALL_constant(
            kwargs.get("model", getattr(self, "model")),
            kwargs.get("fields") or self.fields,
        )
        super().__init__(*args, **kwargs)

    def get_layout(self):
        def get_helptext(f):
            try:
                return self.model._meta.get_field(f).help_text
            except Exception:
                return ""

        return hg.DIV(
            header(),
            _layout.tile.Tile(
                _layout.datatable.DataTable(
                    columns=[
                        _layout.datatable.DataTableColumn(
                            header=_("Field"), cell=hg.C("row.0")
                        ),
                        _layout.datatable.DataTableColumn(
                            header=_("Value"), cell=hg.C("row.1")
                        ),
                    ],
                    row_iterator=(
                        (
                            field
                            if isinstance(field, tuple)
                            else (
                                hg.BaseElement(
                                    hg.DIV(
                                        _layout.ObjectFieldLabel(field),
                                        _layout.forms.helpers.HelpText(
                                            get_helptext(field)
                                        ),
                                    ),
                                ),
                                _layout.ObjectFieldValue(field, formatter=format_value),
                            )
                        )
                        for field in self.fields
                    ),
                    style="width: auto",
                ),
                _layout.button.Button(_("Edit"), style="margin-top: 2rem").as_href(
                    ModelHref(self.object, "edit")
                ),
            ),
        )

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "pagetitle": str(self.object),
        }

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]
