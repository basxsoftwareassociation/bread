from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse, reverse_lazy


class Group:
    def __init__(self, label, permissions=[], order=None):
        self.label = label
        self.permissions = permissions
        self.order = order
        self.items = []

    def __lt__(self, other):
        if self.order is None:
            if other.order is None:
                return self.label.lower() < other.label.lower()
            return 0 < other.order
        if other.order is None:
            return self.order < 0
        return self.order < other.order

    def val(self):
        if self.order is None:
            return self.label
        return str(self.order) if self.order >= 0 else str(self.order)

    def has_permission(self, user):
        print(self.label, [user.has_perm(perm) for perm in self.permissions])
        return (
            all((user.has_perm(perm) for perm in self.permissions))
            and self.items
            and any((item.has_permission(user) for item in self.items))
        )

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
        if self.order is None:
            if other.order is None:
                return self.label.lower() < other.label.lower()
            return 0 < other.order
        if other.order is None:
            return self.order < 0
        return self.order < other.order

    def has_permission(self, user):
        return all([user.has_perm(perm) for perm in self.permissions])

    def get_url(self, request):
        # already reversed or raw url
        if self.url.startswith("/") or self.url.startswith("http"):
            return self.url
        return reverse(self.url)

    def active(self, request):
        return request.path.startswith(str(self.get_url(request)))


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
datamodel = Item(group="Admin", label="Datamodel", url=reverse_lazy("datamodel"),)
system_settings = Item(
    group="Admin", label="System Settings", url=reverse_lazy("admin:index"),
)
system_settings.has_permission = lambda user: user.is_superuser
datamodel.has_permission = lambda user: user.is_superuser
registeritem(datamodel)
registeritem(system_settings)
