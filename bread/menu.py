import collections
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, resolve, reverse, reverse_lazy

from .utils import listurl


class MenuGroup:
    label = None
    permissions = None
    order = None
    items = None

    def __init__(self):
        self.items = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global main
        main.register_group(cls())

    def __lt__(self, other):
        return (self.order or 0) < (other.order or 0)

    def has_permission(self, user):
        if self.permissions:
            return all([user.has_perm(perm) for perm in self.permissions])
        return any([item.has_permission(user) for item in self.items])

    def active(self, request):
        return any((item.active(request) for item in self.items))


class MenuItem:
    label = None
    permissions = None
    order = None
    group = None
    url = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global main
        main.register_item(cls())

    def __lt__(self, other):
        return (self.order or 0) < (other.order or 0)

    def has_permission(self, user):
        if self.permissions:
            return all([user.has_perm(perm) for perm in self.permissions])
        return True

    def get_url(self):
        # already reversed or raw url
        if self.url.startswith("/"):
            return self.url
        try:
            # urlpattern name
            return reverse(self.url)
        except NoReverseMatch:
            # external url?
            return self.url

    def namespace(self):
        return resolve(urlparse(str(self.get_url())).path).namespace

    def active(self, request):
        return self.namespace() == request.resolver_match.namespace


class MenuRegistry:
    def __init__(self):
        self.registry = collections.OrderedDict()

    def register_group(self, menugroup):
        if menugroup.label in self.registry:
            raise ImproperlyConfigured(
                f"MenuGroup {menugroup} has already been registered"
            )
        self.registry[menugroup.label] = menugroup

    def unregister_group(self, menugroup):
        if menugroup.label in self.registry:
            del self.registry[menugroup.label]

    def register_item(self, menuitem):
        if menuitem.group not in self.registry:
            raise ImproperlyConfigured(
                f"MenuGroup {menuitem.group} is not a registered menu group"
            )
        self.registry[menuitem.group].items.append(menuitem)


def generate_for_app(app, models=None):
    class AppGroup(MenuGroup):
        label = app.verbose_name.title()

    if models is None:
        models = [m._meta.model_name for m in app.get_models()]
    for i, modelname in enumerate(models, 1):
        try:
            model = app.get_model(modelname)
            listurl(model)

            class ModelItem(MenuItem):
                group = app.verbose_name
                label = model._meta.verbose_name_plural.title()
                url = listurl(model)
                order = i
                permissions = [f"{app.label}.view_{modelname}"]

        except NoReverseMatch:
            pass


def generate_item(group, label, url, order=None):
    _group = group
    _label = label
    _url = url
    _order = order

    class QuickItem(MenuItem):
        group = _group
        label = _label
        url = _url
        order = _order


# default menu and default items
# there is only one main menu support right now

main = MenuRegistry()


class AdminMenu(MenuGroup):
    label = "Admin"
    order = -1


class PreferencesItem(MenuItem):
    group = "Admin"
    label = "Preferences"
    url = reverse_lazy("dynamic_preferences:global")
    permissions = ["dynamic_preferences:change_globalpreferencemodel"]


class OldPreferencesItem(MenuItem):
    group = "Admin"
    label = "Preferences (old)"
    url = "dynamic_preferences:global"
    permissions = ["dynamic_preferences:change_globalpreferencemodel"]


class SystemSettingsItem(MenuItem):
    group = "Admin"
    label = "System Settings"
    url = "admin:index"

    def has_permission(self, user):
        return user.is_superuser
