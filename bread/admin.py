from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required as login_required_func
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.http import HttpResponse
from django.urls import include, path, reverse_lazy
from django.utils.http import urlencode
from django.utils.text import format_lazy
from django.views.generic import RedirectView
from dynamic_preferences import views as preferences_views
from dynamic_preferences.registries import global_preferences_registry

from . import menu
from . import views as bread_views
from .forms.forms import PreferencesForm
from .utils import generate_path_for_view, has_permission, title

DEFAULT_BREAD_VIEWS = {
    "browse": bread_views.BrowseView,
    "read": bread_views.ReadView,
    "edit": bread_views.EditView,
    "add": bread_views.AddView,
    "delete": bread_views.DeleteView,
}


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

    browsefields = None
    """List of fields to be listed in the table of the browse-page. Defaults to ``["__all__"]``."""

    filterfields = None
    """List of fields which should appear in the filter-form of the browse-page. Defaults to ``["__all__"]``. Can span relationships."""

    readfields = None
    """List of fields to be displaye on the read-page. Defaults to ``["__all__"]``."""

    sidebarfields = None
    """List of fields to be display on the right side of the read and edit pages. Defaults to ``[]``."""

    editfields = None
    """Defines which fields to display on the edit page.
    Can be:
    - List of field names
    - django-crispy-form Layout object (https://django-crispy-forms.readthedocs.io/en/latest/layouts.html)
    Defaults to ``["__all__"]``
    """

    addfields = None
    """Defines which fields to display on the add page.
    Can be:
    - List of field names
    - django-crispy-form Layout object (https://django-crispy-forms.readthedocs.io/en/latest/layouts.html)
    Defaults to whatever value ``editfields`` is set.
    """

    indexview = None
    """Name of the view which servers as the index for this admin class. Defaults to "browse"."""

    browseview = None
    """Class which will be used to create the browse-view. Defaults to ``bread.views.BrowseView``."""

    readview = None
    """Class which will be used to create the read-view. Defaults to ``bread.views.ReadView``."""

    editview = None
    """Class which will be used to create the edit-view. Defaults to ``bread.views.EditView``."""

    addview = None
    """Class which will be used to create the add-view. Defaults to ``bread.views.AddView``."""

    deleteview = None
    """Class which will be used to create the delete-view. Defaults to ``bread.views.DeleteView``."""

    autoviews = list(DEFAULT_BREAD_VIEWS.keys())
    """List of names for which views should automatically be generated.
    Defaults to ``["browse", "read", "edit", "add", "delete"]``.
    Can be used to remove certain actions entirely e.g. preventing to ever access the delete view.
    When adding custom views to this list an according attribute with name <viewname>view assigned to the view
    class should be set on the class instance.
    ``
    from . import models
    from . import views
    class InvoiceAdmin(BreadAdmin):
        model = models.Invoice
        autoviews = ["browse", "edit", "add", "mark_payed"]
        mark_payedview = views.MarkPayedConfirmation
    """

    login_required = True
    """If set to true will add the login_required decorator to all views of this admin"""

    def __init__(self):
        assert self.model is not None
        self.indexview = self.indexview or "browse"
        self.browsefields = (
            ["__all__"] if self.browsefields is None else self.browsefields
        )
        self.filterfields = self.filterfields or self.browsefields
        self.readfields = self.readfields or ["__all__"]
        self.editfields = self.editfields or ["__all__"]
        self.addfields = self.addfields or self.editfields
        self.sidebarfields = self.sidebarfields or []
        self.browseview = self.browseview or bread_views.BrowseView
        self.readview = self.readview or bread_views.ReadView
        self.editview = self.editview or bread_views.EditView
        self.addview = self.addview or bread_views.AddView
        self.deleteview = self.deleteview or bread_views.DeleteView
        self.autoviews = self.autoviews or list(DEFAULT_BREAD_VIEWS.keys())

    def get_views_kwargs(self):
        """Returns a dict with the name of a view as key and a dict as value
        The dict from the value contains additional kwargs for construction the view.
        This can be used if a custom view needs additional parameters in the as_view call
        """
        return {}

    def get_views(self):
        """Returns a dictionary with view names as keys and view instances as values.
        The default views are browse, read, edit, add and delete.
        If the view has model attribute it will be set to this admin classe's model.
        If the viewclass is one of the default bread admin views (see DEFAULT_BREAD_VIEWS) or a subclass of one of them,
        the attribute "admin" it will be set to this admin instance.
        On creating the instance of the view the values from get_views_kwargs will be passed to the as_view call.
        """
        ret = {}
        for viewname in self.autoviews:
            kwargs = {}
            view = getattr(self, f"{viewname}view")

            # class passed, must be a class-based view
            if isinstance(view, type):
                if hasattr(view, "model"):
                    kwargs["model"] = self.model
                if issubclass(view, (tuple(DEFAULT_BREAD_VIEWS.values())),):
                    kwargs["admin"] = self
                kwargs.update(self.get_views_kwargs().get(viewname, {}))

                ret[viewname] = view.as_view(**kwargs)
            else:
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
                f"",
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
            actions.append(
                menu.Link(
                    self.reverse(
                        "edit",
                        pk=object.pk,
                        query_arguments={"next": request.get_full_path()},
                    ),
                    "Edit",
                    "edit",
                )
            )
        if "delete" in urls and has_permission(request.user, "delete", object):
            actions.append(
                menu.Link(
                    self.reverse(
                        "delete",
                        pk=object.pk,
                        query_arguments={"next": str(self.reverse("browse"))},
                    ),
                    "Delete",
                    "delete_forever",
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
            return menu.Link(self.reverse("add"), "Add", "add")
        return None

    def reverse(self, viewname, *args, **kwargs):
        """Will do a lazay reverse on the view with the given name. If kwargs contains
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

    def get_modelname(self):
        """Machine-readable name for the model"""
        return self.model._meta.model_name

    @property
    def modelname(self):
        """Machine-readable name for the model"""
        return self.get_modelname()

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

    def __init__(self):
        assert self.app_label
        assert self.app_label
        self.indexview = self.indexview
        self.browsefields = []
        self.filterfields = []
        self.readfields = []
        self.editfields = []
        self.addfields = []
        self.browseview = None
        self.readview = None
        self.editview = None
        self.addview = None
        self.deleteview = None
        self.autoviews = []

    def get_modelname(self):
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
        if model is None:
            return None
        for modeladmin in self._registry.values():
            if modeladmin.model == model._meta.model:
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
        # add success message to preferences view
        PreferencesView = type(
            "PreferencesView",
            (SuccessMessageMixin, preferences_views.PreferenceFormView),
            {"success_message": "Preferences updated"},
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
        ]
        ret = [
            path(
                "preferences/",
                include((preferences, "dynamic_preferences"), namespace="preferences"),
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


def protectedMedia(request, path):
    """
    Protect media files when using with nginx
    """
    if request.user.is_staff or path.startswith(settings.BREAD_PUBLIC_FILES_PREFIX):
        response = HttpResponse(status=200)
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/protected/{path}"
        return response
    else:
        return HttpResponse(status=404)
