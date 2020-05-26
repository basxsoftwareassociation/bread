from collections import namedtuple

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpResponse
from django.urls import include, path, reverse_lazy
from django.views.generic import CreateView, RedirectView
from django.views.generic.edit import SingleObjectMixin
from django_countries.fields import CountryField
from dynamic_preferences import views as preferences_views
from dynamic_preferences.forms import GlobalPreferenceForm
from dynamic_preferences.registries import global_preferences_registry

from . import menu
from . import views as bread_views
from .formatters import as_object_link, format_value
from .utils import has_permission

Action = namedtuple("Action", ["url", "label", "icon"])

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
    viewlink_field = None
    """Column with this name will be rendered as link to view the object in the browse page"""
    filterfields = None
    """List of fields which should appear in the filter-form of the browse-page. Defaults to ``["__all__"]``. Can span relationships."""
    readfields = None
    """List of fields to be displaye on the read-page. Defaults to ``["__all__"]``."""
    editfields = None
    """List of fields to be displaye on the edit-page. Defaults to ``["__all__"]``."""
    editlayout = None
    """django-crispy-form Layout object for the edit-form. See https://django-crispy-forms.readthedocs.io/en/latest/layouts.html"""
    addfields = None
    """List of fields to be displaye on the add-page. Defaults to ``["__all__"]``."""
    addlayout = None
    """django-crispy-form Layout object for the add-form. See https://django-crispy-forms.readthedocs.io/en/latest/layouts.html"""
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

    autoviews = None
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
            viewclass = getattr(self, f"{viewname}view")
            if hasattr(viewclass, "model"):
                kwargs["model"] = self.model
            if issubclass(viewclass, (tuple(DEFAULT_BREAD_VIEWS.values())),):
                kwargs["admin"] = self
            kwargs.update(self.get_views_kwargs().get(viewname, {}))
            ret[viewname] = viewclass.as_view(**kwargs)

        return ret

    def get_urls(self):
        """Generates a URL for each view returned by get_views.
        The url will start with the name of the view.
        If the view's class is a subclass of SingleObjectMixin but not a create view, the
        according pk url-path argument is added.
        Custom url-path arguments should be specified in the "urlparams" attribute of the
        view. "urlparams" must be a dict with url-path argument as key and type as value.
        If the view is purely function based, the function arguments are converted to url-path
        arguments, using python annotations to determine the argument type if available.
        A url with name "index" is added as redirect view to the view with the name of
        ``self.indexview`` ("browse" by default).
        """
        urls = {}
        for viewname, view in self.get_views().items():
            viewpath = viewname
            # handle class-based views
            if hasattr(view, "view_class"):
                if issubclass(view.view_class, SingleObjectMixin) and not issubclass(
                    view.view_class, CreateView
                ):
                    viewpath += f"/<int:{view.view_class.pk_url_kwarg}>"
                if "urlparams" in view.view_initkwargs:
                    for param, _type in view.view_initkwargs["urlparams"].items():
                        viewpath += f"/<{_type}:{param}>"
            # handle purely function based views
            # try to get the django-path type from the parameter anotation
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

    def menugroup(self):
        """Returns the name of the menu-group under which items for this admin class should appear"""
        return apps.get_app_config(self.model._meta.app_label).verbose_name.title()

    def menuitems(self):
        """Iterable of bread.menu.Item objects which should be added to the menu for this admin class"""
        return [
            menu.Item(
                label=self.verbose_modelname_plural,
                group=self.menugroup(),
                url=self.reverse("index"),
                permissions=[f"{self.model._meta.app_label}.view_{self.modelname}"],
            )
        ]

    def get_editlayout(self, request):
        return self.editlayout

    def get_addlayout(self, request):
        return self.addlayout

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
        if fieldname == self.viewlink_field:
            return as_object_link(object, format_value(value, fieldtype))
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
        Actions which will be available for an object.
        returns: List of named tuples of type Action
        """
        urls = self.get_urls()
        actions = []
        if (
            "read" in urls
            and has_permission(request.user, "view", object)
            and not self.viewlink_field
        ):
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
        """
        Actions which will be available for a model.
        returns: List of named tuples of type Action
        """
        urls = self.get_urls()
        actions = []
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

    def add_action(self, request):
        if "add" in self.get_urls() and has_permission(request.user, "add", self.model):
            return Action(self.reverse("add"), "Add", "add")
        return None

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
        # admin menu items
        menu.registergroup(menu.Group(label="Admin", order=999))
        menu.registeritem(
            menu.Item(
                group="Admin",
                label="Preferences",
                url=reverse_lazy("dynamic_preferences:global"),
                permissions=["dynamic_preferences:change_globalpreferencemodel"],
            )
        )
        datamodel = menu.Item(
            group="Admin", label="Datamodel", url=reverse_lazy("datamodel"),
        )
        system_settings = menu.Item(
            group="Admin", label="System Settings", url=reverse_lazy("admin:index"),
        )
        system_settings.has_permission = lambda user: user.is_superuser
        datamodel.has_permission = lambda user: user.is_superuser
        menu.registeritem(datamodel)
        menu.registeritem(system_settings)

        # app menu itmes
        for app, admins in self.get_apps().items():
            grouplabel = app.verbose_name.title()
            if not menu.main.hasgroup(grouplabel):
                menu.registergroup(menu.Group(label=grouplabel))
            for admin in admins:
                for menuitem in admin.menuitems():
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


class PreferencesForm(GlobalPreferenceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit("submit", "Save"))


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
