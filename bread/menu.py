from django.apps import apps
from django.core.exceptions import ImproperlyConfigured


class Group:
    def __init__(self, label, permissions=[], order=None):
        self.label = label
        self.permissions = permissions
        self._order = order
        self.items = []

    def __lt__(self, other):
        if self._order is None:
            if other._order is None:
                return False
            return 0 < other._order
        if other._order is None:
            return self._order < 0
        return self._order < other._order

    def val(self):
        if self._order is None:
            return self.label
        return str(self._order) if self._order >= 0 else str(self._order)

    def has_permission(self, request):
        return (
            all((request.user.has_perm(perm) for perm in self.permissions))
            and self.items
            and any((item.has_permission(request) for item in self.items))
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


class Link:
    """Represents a user-clickable link
    url, label, icon and permissions can be str, lazy string or a callable function.
    The function takes the current request as the only argument.
    """

    def __init__(self, url, label="", materialicon=None, permissions=[]):
        self._url = url
        self._label = label
        self._icon = materialicon
        self._permissions = permissions

    def url(self, request):
        return _try_call(self._url, request)

    def label(self, request):
        return _try_call(self._label, request)

    def icon(self, request):
        return _try_call(self._icon, request)

    def has_permission(self, request, obj=None):
        return all(
            [
                request.user.has_perm(perm, obj) or request.user.has_perm(perm)
                for perm in _try_call(self._permissions, request)
            ]
        )


class Item:
    def __init__(self, link, group, order=None):
        self.link = link
        self.group = group
        self._order = order

    def __lt__(self, other):
        if self._order is None:
            if other._order is None:
                return False
            return 0 < other._order
        if other._order is None:
            return self._order < 0
        return self._order < other._order

    def has_permission(self, request):
        return self.link.has_permission(request)

    def get_url(self, request):
        return self.link.url(request)

    def active(self, request):
        path = str(self.link.url(request))
        return request.path.startswith(path) and path != "/"


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


def _try_call(var, *args, **kwargs):
    return var(*args, **kwargs) if callable(var) else var
