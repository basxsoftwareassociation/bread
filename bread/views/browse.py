from typing import Callable, List, NamedTuple, Optional

import htmlgenerator as hg
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from djangoql.queryset import apply_search
from guardian.mixins import PermissionListMixin

from bread.utils import expand_ALL_constant, filter_fieldlist

from .. import layout as _layout  # prevent name clashing
from ..utils import (
    Link,
    ModelHref,
    generate_excel,
    get_concrete_instance,
    link_with_urlparameters,
    pretty_modelname,
    xlsxresponse,
)
from .util import BreadView


class BulkAction(NamedTuple):
    name: str
    label: str
    action: Callable[[HttpRequest, models.query.QuerySet], Optional[HttpResponse]]
    iconname: str = "fade"
    permissions: List[str] = []

    def has_permission(self, request, obj=None):
        return all(
            [
                request.user.has_perm(perm, obj) or request.user.has_perm(perm)
                for perm in self.permissions
            ]
        )


class BrowseView(BreadView, LoginRequiredMixin, PermissionListMixin, ListView):
    """TODO: documentation"""

    orderingurlparameter = "ordering"
    objectids_urlparameter = "_selected"  # see bread/static/js/main.js:submitbulkaction and bread/layout/components/datatable.py
    bulkaction_urlparameter = "_bulkaction"
    items_per_page_options = None
    itemsperpage_urlparameter = "itemsperpage"
    columns = ["__all__"]
    search_backend = None
    rowclickaction: Optional[Link] = None
    # bulkactions: List[(Link, function(request, queryset))]
    # - link.js should be a slug and not a URL
    # - if the function returns a HttpResponse, the response is returned instead of the browse view result
    bulkactions = ()
    rowactions = ()  # list of links
    backurl = None
    primary_button = None

    def __init__(self, *args, **kwargs):
        self.orderingurlparameter = (
            kwargs.get("orderingurlparameter") or self.orderingurlparameter
        )
        self.itemsperpage_urlparameter = (
            kwargs.get("itemsperpage_urlparameter") or self.itemsperpage_urlparameter
        )
        self.objectids_urlparameter = (
            kwargs.get("objectids_urlparameter") or self.objectids_urlparameter
        )
        self.bulkaction_urlparameter = (
            kwargs.get("bulkaction_urlparameter") or self.bulkaction_urlparameter
        )
        self.items_per_page_options = (
            kwargs.get("items_per_page_options")
            or self.items_per_page_options
            or getattr(settings, "DEFAULT_PAGINATION_CHOICES", [25, 100, 500])
        )
        self.rowactions = kwargs.get("rowactions") or self.rowactions
        self.columns = expand_ALL_constant(
            kwargs["model"], kwargs.get("columns") or self.columns
        )
        self.search_backend = kwargs.get("search_backend") or self.search_backend
        self.rowclickaction = kwargs.get("rowclickaction") or self.rowclickaction
        self.backurl = kwargs.get("backurl") or self.backurl
        self.primary_button = kwargs.get("primary_button") or self.primary_button
        super().__init__(*args, **kwargs)
        # set some default bulkactions
        self.bulkactions = (
            kwargs.get("bulkactions")
            or self.bulkactions
            or (
                BulkAction(
                    "excel",
                    label=_("Excel"),
                    iconname="download",
                    action=lambda request, qs: export(qs, self.columns),
                ),
                BulkAction(
                    "delete", label=_("Delete"), iconname="trash-can", action=delete
                ),
            )
        )

    def get_layout(self):
        qs = self.get_queryset()
        # re-mapping the Links because the URL is not supposed to be a real URL but an identifier
        # for the bulk action
        # TODO: This is a bit ugly but we can reuse the Link type for icon, label and permissions
        bulkactions = [
            Link(
                link_with_urlparameters(
                    self.request, **{self.bulkaction_urlparameter: action.name}
                ),
                label=action.label,
                iconname=action.iconname,
            )
            for action in self.bulkactions
            if action.has_permission(self.request)
        ]
        return _layout.datatable.DataTable.from_model(
            self.model,
            hg.C("object_list"),
            columns=self.columns,
            bulkactions=bulkactions,
            rowactions=self.rowactions,
            rowactions_dropdown=len(self.rowactions)
            > 2,  # recommendation from carbon design
            search_backend=self.search_backend,
            rowclickaction=self.rowclickaction,
            pagination_config=_layout.pagination.PaginationConfig(
                items_per_page_options=self.items_per_page_options,
                page_urlparameter=self.page_kwarg,
                paginator=self.get_paginator(qs, self.get_paginate_by(qs)),
                itemsperpage_urlparameter=self.itemsperpage_urlparameter,
            ),
            checkbox_for_bulkaction_name=self.objectids_urlparameter,
            settingspanel=self.get_settingspanel(),
            backurl=self.backurl,
            primary_button=self.primary_button,
        )

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": self._get_layout_cached(),
            "pagetitle": pretty_modelname(self.model, plural=True),
        }

    def get_settingspanel(self):
        return None

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)
        if self.bulkaction_urlparameter in self.request.GET:
            bulkactions = {
                action.name: action.action
                for action in self.bulkactions
                if action.has_permission(self.request)
            }
            if self.request.GET[self.bulkaction_urlparameter] not in bulkactions:
                messages.error(
                    self.request,
                    _("Acton '%s' is not configured for this view")
                    % self.request.GET[self.bulkaction_urlparameter],
                )
            else:
                ret = bulkactions[self.request.GET[self.bulkaction_urlparameter]](
                    self.request, self.get_queryset()
                )
                params = self.request.GET.copy()
                del params[self.bulkaction_urlparameter]
                del params[self.objectids_urlparameter]
                if ret is None:
                    return redirect(self.request.path + "?" + params.urlencode())
                return ret
        return super().get(*args, **kwargs)

    def get_paginate_by(self, queryset):
        return self.request.GET.get(
            self.itemsperpage_urlparameter, self.items_per_page_options[0]
        )

    def get_queryset(self):
        """Prefetch related tables to speed up queries. Also order result by get-parameters."""
        qs = super().get_queryset()
        if (
            self.search_backend
            and self.search_backend.query_parameter in self.request.GET
        ):
            qs = apply_search(
                qs,
                "("
                + ") and (".join(
                    self.request.GET.getlist(self.search_backend.query_parameter)
                )
                + ")",
            )

        selectedobjects = self.request.GET.getlist(self.objectids_urlparameter)
        if selectedobjects and "all" not in selectedobjects:
            qs &= super().get_queryset().filter(pk__in=selectedobjects)

        order = self.request.GET.get(self.orderingurlparameter)
        if order:
            if order.endswith("__int"):
                order = order[: -len("__int")]
                qs = qs.order_by(
                    models.functions.Cast(order[1:], models.IntegerField()).desc()
                    if order.startswith("-")
                    else models.functions.Cast(order, models.IntegerField())
                )
            else:
                qs = qs.order_by(
                    models.functions.Lower(order[1:]).desc()
                    if order.startswith("-")
                    else models.functions.Lower(order)
                )
        return qs

    @staticmethod
    def gen_rowclickaction(modelaction):
        """
        Shortcut to get a Link to a model view.
        The default models views in bread are "read", "edit", "delete".
        :param modelaction: A model view whose name has been generated with ``bread.utils.urls.model_urlname``
        """
        return Link(
            label="",
            href=ModelHref(
                hg.F(lambda c: get_concrete_instance(c["row"])),
                modelaction,
                kwargs={"pk": hg.C("row.pk")},
            ),
            iconname=None,
        )


# helper function to export a queryset to excel
def export(queryset, columns):
    if "__all__" in columns:
        columns = filter_fieldlist(queryset.model, columns)
    columndefinitions = {}
    for column in columns:
        if not (
            isinstance(column, _layout.datatable.DataTableColumn)
            or isinstance(column, str)
        ):
            raise ValueError(
                f"Argument 'columns' needs to be of a list with items of type str or DataTableColumn, but found {column}"
            )
        if isinstance(column, str):
            column = _layout.datatable.DataTableColumn(
                _layout.ObjectFieldLabel(column, "model"),
                _layout.ObjectFieldValue(column, "row"),
            )

        columndefinitions[
            hg.render(hg.BaseElement(column.header), {"model": queryset.model})
        ] = lambda row, column=column: hg.render(
            hg.BaseElement(column.cell), {"row": row}
        )

    workbook = generate_excel(queryset, columndefinitions)
    workbook.title = pretty_modelname(queryset.model)
    return xlsxresponse(workbook, workbook.title)


def delete(request, queryset, softdeletefield=None, required_permissions=None):
    if required_permissions is None:
        required_permissions = [
            f"{queryset.model._meta.app_label}.delete_{queryset.model.__name__.lower()}"
        ]

    deleted = 0
    for instance in queryset:
        try:
            if not request.user.has_perm(required_permissions, instance):
                # we throw an exception here because the user not supposed to
                # see the option to delete an object anyway, if he does not have the permssions
                # the queryset should already be filtered
                raise Exception(
                    _("Your user has not the permissions to delete %s") % instance
                )
            if softdeletefield:
                if not getattr(instance, softdeletefield):
                    setattr(instance, softdeletefield, True)
                    instance.save()
                    deleted += 1
            else:
                instance.delete()
                deleted += 1
        except Exception as e:
            messages.error(
                request,
                _("%s could not be deleted: %s") % (object, e),
            )

    messages.success(
        request,
        _("Deleted %(count)s %(modelname)s")
        % {
            "count": deleted,
            "modelname": pretty_modelname(queryset.model, plural=deleted > 1),
        },
    )


def restore(request, queryset, softdeletefield, required_permissions=None):
    if required_permissions is None:
        required_permissions = [
            f"{queryset.model._meta.app_label}.change_{queryset.model.__name__.lower()}"
        ]

    restored = 0
    for instance in queryset:
        try:
            if not request.user.has_perm(required_permissions, instance):
                # we throw an exception here because the user not supposed to
                # see the option to restore an object anyway, if he does not have the permssions
                # the queryset should already be filtered
                raise Exception(
                    _("Your user has not the permissions to restore %s") % instance
                )
            if getattr(instance, softdeletefield, False):
                setattr(instance, softdeletefield, False)
                instance.save()
                restored += 1
        except Exception as e:
            messages.error(
                request,
                _("%s could not be restored: %s") % (object, e),
            )

    messages.success(
        request,
        _("Restored %(count)s %(modelname)s")
        % {
            "count": restored,
            "modelname": pretty_modelname(queryset.model, plural=restored > 1),
        },
    )
