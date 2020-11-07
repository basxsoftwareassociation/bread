from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required as login_required_func
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.http import HttpResponse
from django.urls import include, path, reverse_lazy
from django.utils.http import urlencode
from django.utils.text import format_lazy
from django.views.generic import RedirectView, View
from django.views.static import serve
from dynamic_preferences import views as preferences_views
from dynamic_preferences.forms import preference_form_builder
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.users import views as user_preferences_views
from dynamic_preferences.users.registries import user_preferences_registry

from . import menu
from . import views as bread_views
from .forms.forms import BreadAuthenticationForm, PreferencesForm, UserPreferencesForm
from .layout import ICONS
from .utils import generate_path_for_view, has_permission, title, try_call
from .utils.model_helpers import get_concrete_instance


class BreadAdmin:
    """
    The BreadAdmin class must be inherited and the model-class attribute must be set in
    the child class. This will create a default admin interface to handle objects of the
    according model. The interface can be further customized by overwriting attributes
    and methods in the child admin class.

    The admin class will by default automatically generate django views for the follwing pages:
    - browse: table which lists all objects and has a filter form
    - read: table which lists all fields of a certain object
    - edit: form to edit an object
    - add: form to add a new object
    - delete: confirmation with some additional information for deleting an object
    """

    model = None
    "The django model which will be managed in this class"

    indexview = None
    """Name of the view which servers as the index for this admin class. Defaults to "browse"."""

    login_required = True
    """If set to true will add the login_required decorator to all views of this admin"""

    def __init__(self):
        assert self.model is not None
        self.indexview = self.indexview or "browse"

        # default views
        self.browse_view = getattr(self, "browse_view", bread_views.BrowseView)
        self.read_view = getattr(self, "read_view", bread_views.ReadView)
        self.edit_view = getattr(self, "edit_view", bread_views.EditView)
        self.add_view = getattr(self, "add_view", bread_views.AddView)
        self.delete_view = getattr(self, "delete_view", bread_views.DeleteView)

    def get_views(self):
        """Returns a dictionary with view names as keys and view instances as values.
        All attributes named <viewname>_view are taken into account. <viewname> is the name
        of the view which is used when generating the url for it. If the assigned value is
        a subclass of ``django.views.generic.View`` it will be instantiated. An optional dict
        which will be passed <viewname>_view.as_view can be given through <viewname>_view.kwargs.
        If <viewname>_view is anything else, it needs to be callable, otherwise an exception is
        raised.
        """

        ret = {}
        for view, viewname in [
            (getattr(self, attr), attr[: -len("_view")])
            for attr in dir(self)
            if attr.endswith("_view")
        ]:
            if isinstance(view, type) and issubclass(view, View):
                kwargs = try_call(getattr(view, "kwargs", {}))
                if hasattr(view, "model"):
                    kwargs["model"] = self.model
                if hasattr(view, "admin"):
                    kwargs["admin"] = self
                view = view.as_view(**kwargs)
            elif not callable(view):
                raise RuntimeError(
                    f"View {viewname}_view ({self.__class__.__name__}.{viewname}_view) needs to be callable"
                )
            ret[viewname] = view
        if self.login_required:
            ret[viewname] = login_required_func(ret[viewname])
        return ret

    def get_urls(self):
        """Generates a django path-object for each view returned by get_views.
        A url with name "index" is added as redirect view to the view with the name of
        ``self.indexview`` ("browse" by default).
        """
        urls = {}
        for viewname, view in self.get_views().items():
            urls[viewname] = generate_path_for_view(view, viewname)
        if self.indexview:
            urls["index"] = path(
                "",
                RedirectView.as_view(url=self.reverse(self.indexview)),
                name="index",
            )
        return urls

    def get_custom_urls(self):
        """Return an iterable of path-objects. The paths will be available under site.public_urls
        in order to allow adding paths from the web-root. Examples are frontend-sites or special
        urls for external access."""
        return ()

    def menuitems(self):
        """Returns iterable of bread.menu.Item objects which should be added to the menu for this admin class"""
        return [
            menu.Item(
                menu.Link(
                    url=self.reverse("index"),
                    label=self.verbose_modelname_plural,
                    permissions=[f"{self.model._meta.app_label}.view_{self.modelname}"],
                ),
                group=title(self.model._meta.app_config.verbose_name),
            )
        ]

    def object_actions(self, request, object):
        """
        Actions which will be available for an object.
        Returns: List of named tuples of type Link, defaults are edit and delete
        """
        urls = self.get_urls()
        actions = []
        if "edit" in urls and has_permission(request.user, "change", object):
            # normally we will want to get the edit link to the most concrete instance of an object
            # therefore we check here if we need to get another link to the edit instance
            concrete = get_concrete_instance(object)
            concreteadmin = site.get_default_admin(concrete)
            url = (
                self.reverse(
                    "edit",
                    pk=object.pk,
                    query_arguments={"next": request.get_full_path()},
                ),
            )
            if concrete is not self and concreteadmin is not None:
                url = concreteadmin.reverse(
                    "edit",
                    pk=concrete.pk,
                    query_arguments={"next": request.get_full_path()},
                )
            actions.append(menu.Link(url, "Edit", ICONS["edit"],))
        if "delete" in urls and has_permission(request.user, "delete", object):
            actions.append(
                menu.Link(
                    self.reverse(
                        "delete",
                        pk=object.pk,
                        query_arguments={"next": str(self.reverse("browse"))},
                    ),
                    "Delete",
                    ICONS["delete"],
                )
            )
        return actions

    def list_actions(self, request):
        """
        Actions which will be available for a model.
        returns: List of named tuples of type Link
        """
        urls = self.get_urls()
        actions = []
        if "browse" in urls:
            # need to preserve filter and ordering from query parameters
            query_arguments = request.GET.copy()
            query_arguments["export"] = 1
            actions.append(
                menu.Link(
                    self.reverse("browse", query_arguments=query_arguments),
                    "Excel",
                    "file_download",
                )
            )
        return actions

    def add_action(self, request):
        """Returns a link to the "add" view of this admin"""
        if "add" in self.get_urls() and has_permission(request.user, "add", self.model):
            return menu.Link(
                self.reverse("add"), f"Add {self.verbose_modelname}", "add"
            )
        return None

    def reverse(self, viewname, *args, **kwargs):
        """Will do a lazy reverse on the view with the given name. If kwargs contains
        a key "query_arguments", it must be of instance dict and will be used to set
        query arguments.
        """

        if isinstance(self, BreadGenericAdmin):
            namespace = f"{self.app_label}:{self.modelname}"
        else:
            namespace = f"{self.model._meta.app_label}:{self.modelname}"
        if "query_arguments" in kwargs:
            querystring = urlencode(kwargs.pop("query_arguments"), doseq=True)
            url = reverse_lazy(
                f"{namespace}:{viewname}",
                args=args,
                kwargs=kwargs,
                current_app=namespace,
            )
            return format_lazy("{url}?{querystring}", url=url, querystring=querystring)

        return reverse_lazy(
            f"{namespace}:{viewname}", args=args, kwargs=kwargs, current_app=namespace
        )

    @property
    def urls(self):
        """Urls for inclusion in django urls"""
        urls = path(
            self.modelname + "/",
            include((list(self.get_urls().values()), self.modelname), self.modelname),
        )
        return urls

    @property
    def modelname(self):
        """Machine-readable name for the model"""
        return self.model._meta.model_name

    @property
    def verbose_modelname(self):
        """Shortcut to use in templates"""
        return title(self.model._meta.verbose_name)

    @property
    def verbose_modelname_plural(self):
        """Shortcut to use in templates"""
        return title(self.model._meta.verbose_name_plural)

    def __str__(self):
        return self.verbose_modelname + " Admin"


class BreadGenericAdmin(BreadAdmin):
    """Admin class which works without model, for generic menu items and URLS"""

    class model(models.Model):
        """Stub model because this admin is not coupled to a model"""

        class Meta:
            managed = False

    app_label = None
    """app_label needs to be set because we cannot determine the app from the model"""

    def get_views(self):
        return {}

    def __init__(self):
        assert self.app_label
        assert self.app_label
        self.indexview = self.indexview
        self.browse_view = None
        self.read_view = None
        self.edit_view = None
        self.add_view = None
        self.delete_view = None

    @property
    def modelname(self):
        return self.app_label

    @property
    def verbose_modelname(self):
        return title(self.app_label)

    @property
    def verbose_modelname_plural(self):
        return title(self.app_label)

    def menuitems(self):
        return ()


class BreadAdminSite:
    _registry = None

    def __init__(self):
        self._registry = {}

    def register(self, modeladmin):
        self._registry[modeladmin] = modeladmin()

    def unregister(self, modeladmin):
        del self._registry[modeladmin]

    def get_default_admin(self, model):
        """model can be a model class or a model instance"""
        if model is None:
            return None
        for modeladmin in self._registry.values():
            if modeladmin.model in (model._meta.model, type(model)):
                return modeladmin
        return None

    def get_apps(self):
        applist = {}
        for breadadmin in self._registry.values():
            if isinstance(breadadmin, BreadGenericAdmin):
                app = apps.get_app_config(breadadmin.app_label)
            else:
                app = apps.get_app_config(breadadmin.model._meta.app_label)
            if app not in applist:
                applist[app] = []
            applist[app].append(breadadmin)
        return applist

    def register_menus(self):
        # admin menu items
        menu.registeritem(
            menu.Item(
                menu.Link(
                    label="Preferences",
                    url=reverse_lazy("dynamic_preferences:global"),
                    permissions=["dynamic_preferences:change_globalpreferencemodel"],
                ),
                group=menu.Group(label="Admin", order=999),
            )
        )
        datamodel = menu.Item(
            menu.Link(url=reverse_lazy("datamodel"), label="Datamodel"), group="Admin",
        )
        system_settings = menu.Item(
            menu.Link(url=reverse_lazy("admin:index"), label="System Settings"),
            group="Admin",
        )
        system_settings.has_permission = lambda request: request.user.is_superuser
        datamodel.has_permission = lambda request: request.user.is_superuser
        menu.registeritem(datamodel)
        menu.registeritem(system_settings)

        # app menu itmes
        for app, admins in self.get_apps().items():
            for breadadmin in admins:
                for menuitem in breadadmin.menuitems():
                    menu.registeritem(menuitem)

    def get_urls(self):
        def user_get_form_class(self, *args, **kwargs):
            section = self.kwargs.get("section", None)
            return preference_form_builder(
                UserPreferencesForm,
                instance=self.request.user,
                section=section,
                **kwargs,
            )

        # add success message to preferences view
        PreferencesView = type(
            "PreferencesView",
            (SuccessMessageMixin, preferences_views.PreferenceFormView),
            {"success_message": "Preferences updated"},
        )
        UserPreferencesView = type(
            "UserPreferencesView",
            (SuccessMessageMixin, user_preferences_views.UserPreferenceFormView),
            {
                "success_message": "Preferences updated",
                "get_form_class": user_get_form_class,
            },
        )

        preferences = [
            path(
                "global/",
                PreferencesView.as_view(
                    registry=global_preferences_registry, form_class=PreferencesForm,
                ),
                name="global",
            ),
            path(
                "global/<slug:section>",
                PreferencesView.as_view(
                    registry=global_preferences_registry, form_class=PreferencesForm,
                ),
                name="global.section",
            ),
            path(
                "user/",
                UserPreferencesView.as_view(registry=user_preferences_registry),
                name="user",
            ),
            path(
                "user/<slug:section>",
                UserPreferencesView.as_view(registry=user_preferences_registry),
                name="user.section",
            ),
        ]
        ret = [
            path(
                "preferences/",
                include((preferences, "dynamic_preferences"), namespace="preferences"),
            ),
            path(
                "accounts/login/",
                auth_views.LoginView.as_view(
                    authentication_form=BreadAuthenticationForm
                ),
                name="login",
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
                    include(
                        ([breadadmin.urls for breadadmin in admins], app.label),
                        app.label,
                    ),
                )
            )
        return ret

    def get_custom_urls(self):
        ret = [path("system/", admin.site.urls)]
        for app, admins in self.get_apps().items():
            for breadadmin in admins:
                ret.extend(breadadmin.get_custom_urls())
        return ret

    @property
    def urls(self):
        return include(self.get_urls())

    @property
    def custom_urls(self):
        return include(self.get_custom_urls())


def register(modeladmin):
    """BreadAdmin classes must use this function in order to active
    their class in the frontend. The function can also be used as
    a decorator on the class"""
    site.register(modeladmin)
    return modeladmin


site = BreadAdminSite()


def can_access_media(request, path):
    return request.user.is_staff or path.startswith(settings.BREAD_PUBLIC_FILES_PREFIX)


def protectedMedia(request, path):
    """
    Protect media files
    """
    if can_access_media(request, path):
        if settings.DEBUG:
            return serve(request, path, document_root=settings.MEDIA_ROOT)
        else:
            response = HttpResponse(status=200)
            del response["Content-Type"]
            response["X-Accel-Redirect"] = f"/protected/{path}"
            return response
    else:
        return HttpResponse(status=404)
