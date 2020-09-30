from django.apps import apps

from .utils import try_call


class Group:
    def __init__(
        self, label, icon=None, permissions=[], order=None, sort_alphabetically=False
    ):
        self.label = label
        self.icon = icon
        self.permissions = permissions
        self._order = order
        self.items = []
        self.sort_alphabetically = sort_alphabetically

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

    def __init__(self, url, label="", icon=None, permissions=[]):
        self._url = url
        self.label = label
        self.icon = icon
        self._permissions = permissions

    def url(self, request):
        return try_call(self._url, request)

    def has_permission(self, request, obj=None):
        return all(
            [
                request.user.has_perm(perm, obj) or request.user.has_perm(perm)
                for perm in try_call(self._permissions, request)
            ]
        )


class Item:
    def __init__(self, link, group, order=None):
        self.link = link
        self.group = group
        self._order = order

    def __lt__(self, other):
        if self.group and self.group.sort_alphabetically:
            return self.link.label.lower() < other.link.label.lower()
        if self._order is None:
            if other._order is None:
                return False
            return 0 < other._order
        if other._order is None:
            return self._order < 0
        return self._order < other._order

    def has_permission(self, request):
        return self.link.has_permission(request)

    def active(self, request):
        path = str(self.link.url(request))
        return request.path.startswith(path) and path != "/"


class Menu:
    def __init__(self):
        self._registry = {}

    def registeritem(self, menuitem):
        group = menuitem.group
        if not isinstance(group, Group):
            group = Group(label=group)
            menuitem.group = group
        if group.label not in self._registry:
            self._registry[group.label] = group
        self._registry[group.label].items.append(menuitem)


def registeritem(item):
    main.registeritem(item)
    return item


# global main menu
main = Menu()
