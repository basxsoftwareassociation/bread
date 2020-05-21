from collections import namedtuple

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpResponse
from django.urls import include, path, reverse_lazy
from django.views.generic import DeleteView, DetailView, RedirectView, UpdateView
from django_countries.fields import CountryField

from . import menu
from . import views as bread_views
from .formatters import format_value
from .utils import has_permission

Action = namedtuple("Action", ["url", "label", "icon"])


class BreadAdmin:
    """
    The BreadAdmin class must be inherited and the model-class attribute must be set in
    the child class. This will create a default admin interface to handle objects of the
    according model. The interface can be further customized by overwriting attributes
    and methods in child admin class.
    The admin class will by default generate views for the follwing actions:
    - browse
    - read
    - edit
    - add
    - delete
    In order to define which fields should be displayed on a given view, the follwing attributes
    can be set to iterables of fieldnames:
    - browsefields: Fields to display in the browse page (i. e. which the columns the table will have)
    - filterfields: Fields which should be displayed in the filter-form of the browse page (supports relationships via __)
    - readfields: Fields to display on the detail page
    - editfields: Fields to display on the edit form
    - addfields: Fields to display on the add form
    """

    model = None
    browsefields = None
    filterfields = None
    readfields = None
    editfields = None
    addfields = None
    indexview = None
    browseview = None
    readview = None
    editview = None
    addview = None
    deleteview = None

    views = None

    def __init__(self):
        assert self.model is not None
        self.indexview = self.indexview or "browse"
        self.browsefields = self.browsefields or ["__all__"]
        self.filterfields = self.filterfields or self.browsefields
        self.readfields = self.readfields or ["__all__"]
        self.editfields = self.editfields or ["__all__"]
        self.addfields = self.addfields or ["__all__"]
        self.browseview = self.browseview or bread_views.BrowseView
        self.readview = self.readview or bread_views.ReadView
        self.editview = self.editview or bread_views.EditView
        self.addview = self.addview or bread_views.AddView
        self.deleteview = self.deleteview or bread_views.DeleteView
        self.views = self.views or ["browse", "read", "edit", "add", "delete"]

    def get_views_kwargs(self):
        """Takes the name of a view and returns keyword arguments for the view"""
        return {view: {} for view in self.views}

    def get_views(self):
        """Returns a dictionary with view names as keys and view instances as values
        The default views are browse, read, edit, add and delete. If the view has an
        attribute "admin" it will be set to this admin instance. Keyword arguments for
        a view can be given by returning them from the method get_views_kwargs
        """
        ret = {}
        for viewname in self.views:
            kwargs = {"model": self.model}
            viewclass = getattr(self, f"{viewname}view")
            if hasattr(viewclass, "admin"):
                kwargs["admin"] = self
            kwargs.update(self.get_views_kwargs()[viewname])
            ret[viewname] = viewclass.as_view(**kwargs)

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
        if hasattr(self, fieldname):
            value = getattr(self, fieldname)(object)
        else:
            if hasattr(object, f"get_{fieldname}_display") and not isinstance(
                fieldtype, CountryField
            ):
                value = getattr(object, f"get_{fieldname}_display")()
            else:
                value = getattr(object, fieldname, None)
        return format_value(value, fieldtype)

    def render_field_aggregation(self, queryset, fieldname):
        DEFAULT_AGGREGATORS = {models.DurationField: models.Sum(fieldname)}
        modelfield = None
        try:
            modelfield = self.model._meta.get_field(fieldname)
            if isinstance(modelfield, GenericForeignKey):
                modelfield = None
        except FieldDoesNotExist:
            pass
        # check if there are aggrations defined on the breadadmin or on the model field
        aggregation_func = getattr(self, f"{fieldname}_aggregation", None)
        if aggregation_func is None:
            aggregation_func = getattr(
                getattr(self.model, fieldname, None), "aggregation", None
            )
        # if there is no custom aggregation defined but the field is a database fields, we just count distinct
        if aggregation_func is None:
            if modelfield is None:
                return ""
            aggregation = DEFAULT_AGGREGATORS.get(
                type(modelfield), models.Count(fieldname, distinct=True)
            )
            # we use the count aggregator and therefore have an integer
            if type(modelfield) not in DEFAULT_AGGREGATORS:
                modelfield = models.IntegerField()
        else:
            aggregation = aggregation_func(queryset)

        if isinstance(aggregation, models.Aggregate):
            return format_value(
                queryset.aggregate(value=aggregation)["value"], modelfield
            )
        return format_value(aggregation, modelfield)

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
            if modeladmin.model == model._meta.model:
                return modeladmin
        return None

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
            path(
                "", bread_views.Overview.as_view(adminsite=self), name="bread_overview",
            ),
            path("datamodel", bread_views.DataModel.as_view(), name="datamodel",),
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
