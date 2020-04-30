from collections import namedtuple

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count
from django.http import HttpResponse
from django.urls import include, path, reverse_lazy
from django.views.generic import DeleteView, DetailView, RedirectView, UpdateView

from . import menu, views
from .formatters import format_value
from .utils import has_permission

Action = namedtuple("Action", ["url", "label", "icon"])


class BreadAdmin:
    # for overwriting
    model = None
    indexview = None
    browsefields = None
    filterfields = None
    readfields = None
    editfields = None
    addfields = None
    createmenu = None
    browseview = None
    readview = None
    editview = None
    addview = None
    deleteview = None

    def __init__(self):
        assert self.model is not None
        self.indexview = self.indexview or "browse"
        self.browsefields = self.browsefields or ["__all__"]
        self.filterfields = self.filterfields or self.browsefields
        self.readfields = self.readfields or ["__all__"]
        self.editfields = self.editfields or ["__all__"]
        self.addfields = self.addfields or ["__all__"]
        self.createmenu = self.createmenu is not False
        self.browseview = self.browseview or views.BrowseView
        self.readview = self.readview or views.ReadView
        self.editview = self.editview or views.EditView
        self.addview = self.addview or views.AddView
        self.deleteview = self.deleteview or views.DeleteView

    def get_views(self):
        ret = {}
        for viewname in ["browse", "read", "edit", "add", "delete"]:
            ret[viewname] = getattr(self, f"{viewname}view").as_view(
                admin=self, model=self.model
            )

        return ret

    def get_urls(self):
        urls = {}
        for viewname, view in self.get_views().items():
            viewpath = viewname
            if hasattr(view, "view_class"):
                if (
                    issubclass(view.view_class, UpdateView)
                    or issubclass(view.view_class, DetailView)
                    or issubclass(view.view_class, DeleteView)
                ):
                    viewpath += f"/<int:pk>"
                if "urlparams" in view.view_initkwargs:
                    for param, _type in view.view_initkwargs["urlparams"].items():
                        viewpath += f"/<{_type}:{param}>"
            elif callable(view):
                params = view.__code__.co_varnames[1 : view.__code__.co_argcount]
                annotations = view.__annotations__
                for param in params:
                    viewpath += (
                        f"/<{annotations[param]}:{param}>"
                        if param in annotations
                        else f"/<{param}>"
                    )
            urls[viewname] = path(viewpath, view, name=viewname)
        urls["index"] = path(
            f"", RedirectView.as_view(url=self.reverse(self.indexview)), name="index",
        )
        return urls

    def get_menuitems(self):
        grouplabel = apps.get_app_config(
            self.model._meta.app_label
        ).verbose_name.title()
        return [
            menu.Item(
                label=self.verbose_modelname_plural,
                group=grouplabel,
                url=self.reverse("index"),
                permissions=[f"{self.model._meta.app_label}.view_{self.modelname}"],
            )
        ]

    def render_field(self, object, fieldname):
        fieldtype = None
        try:
            fieldtype = self.model._meta.get_field(fieldname)
        except FieldDoesNotExist:
            pass
        return format_value(
            getattr(self, fieldname, None) or getattr(object, fieldname, None),
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
                Action(self.reverse("read", pk=object.pk), "View", "search",)
            )
        if "edit" in urls and has_permission(request.user, "change", object):
            actions.append(Action(self.reverse("edit", pk=object.pk), "Edit", "edit",))
        if "delete" in urls and has_permission(request.user, "delete", object):
            actions.append(
                Action(
                    self.reverse("delete", pk=object.pk), "Delete", "delete_forever",
                )
            )
        return actions

    def list_actions(self, request):
        urls = self.get_urls()
        actions = []
        if "add" in urls and has_permission(request.user, "add", self.model):
            actions.append(Action(self.reverse("add"), "Add", "add"))
        if "browse" in urls:
            # need to preserve filter and ordering from query parameters
            actions.append(
                Action(
                    self.reverse("browse")
                    + "?"
                    + request.GET.urlencode()
                    + "&export=1",
                    "Excel",
                    "file_download",
                )
            )
        return actions

    def get_modelname(self):
        """Machine-readable name for the model"""
        return self.model._meta.model_name

    def reverse(self, viewname, *args, **kwargs):
        namespace = f"{self.model._meta.app_label}:{self.modelname}"
        return reverse_lazy(
            f"{namespace}:{viewname}", args=args, kwargs=kwargs, current_app=namespace
        )

    @property
    def urls(self):
        """Urls for inclusion in django urls"""
        urls = path(
            self.modelname + "/",
            include((self.get_urls().values(), self.modelname), self.modelname),
        )
        return urls

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
        self._registry[modeladmin] = modeladmin()

    def unregister(self, modeladmin):
        del self._registry[modeladmin]

    def get_default_admin(self, model):
        for modeladmin in self._registry.values():
            if modeladmin.model == model:
                return modeladmin

    def get_apps(self):
        applist = {}
        for admin in self._registry.values():
            app = apps.get_app_config(admin.model._meta.app_label)
            if app not in applist:
                applist[app] = []
            applist[app].append(admin)
        return applist

    def register_menus(self):
        for app, admins in self.get_apps().items():
            grouplabel = app.verbose_name.title()
            if not menu.main.hasgroup(grouplabel):
                menu.registergroup(menu.Group(label=grouplabel))
            for admin in admins:
                for menuitem in admin.get_menuitems():
                    menu.registeritem(menuitem)

    def get_urls(self):
        ret = [
            path(
                "preferences/",
                include("dynamic_preferences.urls", namespace="preferences"),
            ),
            path("accounts/", include("django.contrib.auth.urls")),
            path("ckeditor/", include("ckeditor_uploader.urls")),
            path("", views.Overview.as_view(adminsite=self), name="bread_overview",),
            path("datamodel", views.DataModel.as_view(), name="datamodel",),
        ]

        for app, admins in self.get_apps().items():
            ret.append(
                path(
                    f"{app.label}/",
                    include(([admin.urls for admin in admins], app.label), app.label),
                )
            )
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
