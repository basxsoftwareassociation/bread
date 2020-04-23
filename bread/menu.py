from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from django.urls import resolve, reverse, reverse_lazy


class Group:
    def __init__(self, label, permissions=[], order=None):
        self.label = label
        self.permissions = permissions
        self.order = order
        self.items = []

    def __lt__(self, other):
        return (self.order or 0) < (other.order or 0)

    def has_permission(self, user):
        return all([user.has_perm(perm) for perm in self.permissions])

    def active(self, request):
        return any((item.active(request) for item in self.items))


class Item:
    def __init__(self, label, group, url, permissions=[], order=None):
        self.label = label
        self.group = group
        self.url = url
        self.permissions = permissions
        self.order = order

    def __lt__(self, other):
        return (self.order or 0) < (other.order or 0)

    def has_permission(self, user):
        return all([user.has_perm(perm) for perm in self.permissions])

    def get_url(self):
        # already reversed or raw url
        if self.url.startswith("/") or self.url.startswith("http"):
            return self.url
        return reverse(self.url)

    def namespace(self):
        return resolve(urlparse(str(self.get_url())).path).namespace

    def active(self, request):
        return self.namespace() == request.resolver_match.namespace


class Menu:
    def __init__(self):
        self._registry = {}

    def registergroup(self, menugroup):
        if menugroup.label in self._registry:
            raise ImproperlyConfigured(f"Group {menugroup} has already been registered")
        self._registry[menugroup.label] = menugroup

    def hasgroup(self, groupname):
        return groupname in self._registry

    def unregistergroup(self, menugroup):
        if menugroup.label in self._registry:
            del self._registry[menugroup.label]

    def registeritem(self, menuitem):
        if menuitem.group not in self._registry:
            raise ImproperlyConfigured(
                f"Group {menuitem.group} is not a registered menu group"
            )
        self._registry[menuitem.group].items.append(menuitem)


main = Menu()


def registeritem(item):
    main.registeritem(item)
    return item


def registergroup(group):
    main.registergroup(group)
    return group


# default menu and default items
# there is only one main menu support right now

registergroup(Group(label="Admin", order=-1))
registeritem(
    Item(
        group="Admin",
        label="Preferences",
        url=reverse_lazy("dynamic_preferences:global"),
        permissions=["dynamic_preferences:change_globalpreferencemodel"],
    )
)
registeritem(Item(group="Admin", label="Datamodel", url=reverse_lazy("datamodel"),))
system_settings = Item(
    group="Admin", label="System Settings", url=reverse_lazy("admin:index"),
)
system_settings.has_permission = lambda user: user.is_superuser
registeritem(system_settings)
