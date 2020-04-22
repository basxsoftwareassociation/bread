from collections import namedtuple

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count
from django.http import HttpResponse
from django.url import include, path
from django.utils import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, RedirectView, UpdateView

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
        self.createmenu = self.createmenu or True
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
                    url=self.reverse(self.get_views()[self.indexview]),
                    permissions=[f"{self.model._meta.app_label}.view_{self.modelname}"],
                )
            )

    def get_views(self):
        return {
            "browse": views.BrowseView.as_view(self, model=self.model),
            "read": views.ReadView.as_view(self, model=self.model),
            "edit": views.EditView.as_view(self, model=self.model),
            "add": views.AddView.as_view(self, model=self.model),
            "delete": views.DeleteView.as_view(self, model=self.model),
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
        for viewname, view in self.get_views():
            viewpath = f"{self.modelname}/{viewname}"
            if (
                isinstance(view, UpdateView)
                or isinstance(DetailView)
                or isinstance(DeleteView)
            ):
                viewpath += (f"/<int:pk>",)
            urls[viewname] = path(viewpath, view, name=self.get_urlname(viewname),)
        urls["index"] = path(
            "",
            RedirectView.as_view(url=self.reverse(self.get_views()[self.indexview])),
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
            getattr(self.model, fieldname, getattr(self, fieldname)), fieldtype
        )

    def render_field_aggregation(self, queryset, fieldname):
        fieldtype = None
        try:
            fieldtype = self.model._meta.get_field(fieldname)
        except FieldDoesNotExist:
            pass
        aggregation = getattr(getattr(self, fieldname, None), "aggregation", None)
        if aggregation is None:
            aggregation = getattr(
                getattr(self.model, fieldname, None), "aggregation", None
            )
        if aggregation is None:
            aggregation = Count(fieldname)
            pass  # add default
        if fieldtype is not None:
            return format_value(
                queryset.aggregate(value=aggregation)["value"], fieldtype
            )
        return ""

    def object_actions(self, request, object):
        """
        Actions which will be available for an object
        returns: List of named tuples of type Action
        """
        urls = self.get_urls()
        actions = []
        if "read" in urls and has_permission(request.user, "view", object):
            actions.append(Action(urls["read"], "View", "search"))
        if "edit" in urls and has_permission(request.user, "change", object):
            actions.append(Action(urls["edit"], "Edit", "edit"))
        if "delete" in urls and has_permission(request.user, "delete", object):
            actions.append(Action(urls["delete"], "Delete", "delete_forever"))
        return actions

    def list_actions(self, request):
        urls = self.get_urls()
        actions = []
        if "browse" in urls:
            actions.append(Action(urls["browse"] + "?export=1", "Excel", "view_column"))
        if "add" in urls and has_permission(request.user, "add", self.model):
            actions.append(Action(urls["browse"] + "?export=1", "Add", "add"))
        return actions

    def get_modelname(self):
        """Machine-readable name for the model"""
        return self.model._meta.model_name

    @property
    def urls(self):
        """Urls for inclusion in django urls"""
        return include((self.get_urls().values(), self.app_namespace), self.namespace)

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
        self._registry[modeladmin.model] = modeladmin

    def get_urls(self):
        ret = [
            path("bread/", views.Overview.as_view(), name="bread_overview"),
            path(
                "preferences/",
                include("dynamic_preferences.urls", namespace="preferences"),
            ),
            path("accounts/", include("django.contrib.auth.urls")),
            path("ckeditor/", include("ckeditor_uploader.urls")),
            path("", RedirectView.as_view(url=reverse_lazy("bread_overview"))),
        ]

        for modeladmin in self._registry.values():
            ret.extend(modeladmin.urls)
        return ret


def register(modeladmin):
    site.register(modeladmin.model, modeladmin)
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
