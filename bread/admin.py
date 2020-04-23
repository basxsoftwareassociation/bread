from collections import namedtuple

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count
from django.http import HttpResponse
from django.urls import include, path, reverse
from django.views.generic import DeleteView, DetailView, UpdateView

from . import menu, views
from .formatters import format_value
from .utils import has_permission

Action = namedtuple("Action", ["url", "label", "icon"])


class BreadAdmin:
    # for overwriting
    namespace = None
    model = None
    indexview = None
    browsefields = None
    filterfields = None
    readfields = None
    editfields = None
    addfields = None
    createmenu = None
    app_namespace = None  # should not be overriden in general I think

    def __init__(self):
        assert self.model is not None
        self.namespace = self.namespace or "bread"
        self.app_namespace = self.app_namespace or self.model._meta.app_label
        self.indexview = self.indexview or "browse"
        self.browsefields = self.browsefields or ["__all__"]
        self.filterfields = self.filterfields or self.browsefields
        self.readfields = self.readfields or ["__all__"]
        self.editfields = self.editfields or ["__all__"]
        self.addfields = self.addfields or ["__all__"]
        self.createmenu = self.createmenu is not False
        if self.createmenu:
            grouplabel = apps.get_app_config(
                self.model._meta.app_label
            ).verbose_name.title()
            if not menu.main.hasgroup(grouplabel):
                menu.registergroup(menu.Group(label=grouplabel))
            menu.registeritem(
                menu.Item(
                    label=self.verbose_modelname_plural,
                    group=grouplabel,
                    url=self.get_urlname("index"),
                    permissions=[f"{self.model._meta.app_label}.view_{self.modelname}"],
                )
            )

    def get_views(self):
        return {
            "browse": views.BrowseView.as_view(admin=self, model=self.model),
            "read": views.ReadView.as_view(admin=self, model=self.model),
            "edit": views.EditView.as_view(admin=self, model=self.model),
            "add": views.AddView.as_view(admin=self, model=self.model),
            "delete": views.DeleteView.as_view(admin=self, model=self.model),
        }

    def reverse(self, viewname, *args, **kwargs):
        return reverse(
            self.get_urlname(viewname),
            args=args,
            kwargs=kwargs,
            current_app=self.namespace,
        )

    def get_urlname(self, viewname):
        return f"{self.modelname}_{viewname}"

    def get_urls(self):
        urls = {}
        for viewname, view in self.get_views().items():
            viewpath = f"{self.modelname}/{viewname}"
            if (
                issubclass(view.view_class, UpdateView)
                or issubclass(view.view_class, DetailView)
                or issubclass(view.view_class, DeleteView)
            ):
                viewpath += f"/<int:pk>"
            urls[viewname] = path(viewpath, view, name=self.get_urlname(viewname),)
        urls["index"] = path(
            self.modelname,
            self.get_views()[self.indexview],
            name=self.get_urlname("index"),
        )
        return urls

    def render_field(self, object, fieldname):
        fieldtype = None
        try:
            fieldtype = self.model._meta.get_field(fieldname)
        except FieldDoesNotExist:
            pass
        return format_value(
            getattr(object, fieldname, None) or getattr(self, fieldname, None),
            fieldtype,
        )

    def render_field_aggregation(self, queryset, fieldname):
        fieldtype = None
        try:
            fieldtype = self.model._meta.get_field(fieldname)
            if isinstance(fieldtype, GenericForeignKey):
                fieldtype = None
        except FieldDoesNotExist:
            pass
        aggregation = getattr(getattr(self, fieldname, None), "aggregation", None)
        if aggregation is None:
            aggregation = getattr(
                getattr(self.model, fieldname, None), "aggregation", None
            )
        if aggregation is None:
            if fieldtype is None:
                return ""
            return format_value(
                queryset.aggregate(value=Count(fieldname))["value"], fieldtype
            )
        return format_value(
            queryset.aggregate(value=Count(fieldname))["value"], fieldtype
        )

    def object_actions(self, request, object):
        """
        Actions which will be available for an object
        returns: List of named tuples of type Action
        """
        urls = self.get_urls()
        actions = []
        if "read" in urls and has_permission(request.user, "view", object):
            actions.append(
                Action(
                    reverse(self.get_urlname("read"), args=[object.pk]),
                    "View",
                    "search",
                )
            )
        if "edit" in urls and has_permission(request.user, "change", object):
            actions.append(
                Action(
                    reverse(self.get_urlname("edit"), args=[object.pk]), "Edit", "edit"
                )
            )
        if "delete" in urls and has_permission(request.user, "delete", object):
            actions.append(
                Action(
                    reverse(self.get_urlname("delete"), args=[object.pk]),
                    "Delete",
                    "delete_forever",
                )
            )
        return actions

    def list_actions(self, request):
        urls = self.get_urls()
        actions = []
        if "add" in urls and has_permission(request.user, "add", self.model):
            actions.append(Action(reverse(self.get_urlname("add")), "Add", "add"))
        if "browse" in urls:
            actions.append(
                Action(
                    reverse(self.get_urlname("browse")) + "?export=1",
                    "Excel",
                    "file_download",
                )
            )
        return actions

    def get_modelname(self):
        """Machine-readable name for the model"""
        return self.model._meta.model_name

    @property
    def urls(self):
        """Urls for inclusion in django urls"""
        return list(self.get_urls().values())
        # return include((self.get_urls().values(), self.app_namespace), self.namespace)

    @property
    def modelname(self):
        """Machine-readable name for the model"""
        return self.get_modelname()

    @property
    def verbose_modelname(self):
        """Shortcut to use in templates"""
        return self.model._meta.verbose_name.title()

    @property
    def verbose_modelname_plural(self):
        """Shortcut to use in templates"""
        return self.model._meta.verbose_name_plural.title()

    def __str__(self):
        return self.verbose_modelname + " Admin"


class BreadAdminSite:
    _registry = None

    def __init__(self):
        self._registry = {}

    def register(self, modeladmin):
        self._registry[modeladmin.model] = modeladmin()

    def get_urls(self):
        ret = [
            path(
                "preferences/",
                include("dynamic_preferences.urls", namespace="preferences"),
            ),
            path("accounts/", include("django.contrib.auth.urls")),
            path("ckeditor/", include("ckeditor_uploader.urls")),
            path(
                "overview",
                views.Overview.as_view(adminsite=self),
                name="bread_overview",
            ),
            path("datamodel", views.DataModel.as_view(), name="datamodel",),
        ]

        for modeladmin in self._registry.values():
            ret.extend(modeladmin.urls)
        return ret

    @property
    def urls(self):
        return include(self.get_urls())


def register(modeladmin):
    site.register(modeladmin)
    return modeladmin


site = BreadAdminSite()


def protectedMedia(request, path):
    """
    Protect media files when using with nginx
    """
    if request.user.is_staff:
        response = HttpResponse(status=200)
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/protected/{path}"
        return response
    else:
        return HttpResponse(status=404)
