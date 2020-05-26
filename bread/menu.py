from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


class Group:
    def __init__(self, label, permissions=[], order=None):
        self.label = label
        self.permissions = permissions
        self.order = order
        self.items = []

    def __lt__(self, other):
        if self.order is None:
            if other.order is None:
                return False
            return 0 < other.order
        if other.order is None:
            return self.order < 0
        return self.order < other.order

    def val(self):
        if self.order is None:
            return self.label
        return str(self.order) if self.order >= 0 else str(self.order)

    def has_permission(self, user):
        return (
            all((user.has_perm(perm) for perm in self.permissions))
            and self.items
            and any((item.has_permission(user) for item in self.items))
        )

    def active_in_current_app(self, request):
        return request.resolver_match.app_names and (
            self.label
            == apps.get_app_config(
                request.resolver_match.app_names[0]
            ).verbose_name.title()
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
                return False
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
            self._registry[menuitem.group] = Group(menuitem.group)
        self._registry[menuitem.group].items.append(menuitem)


def registeritem(item):
    main.registeritem(item)
    return item


def registergroup(group):
    main.registergroup(group)
    return group


# global main menu
main = Menu()
