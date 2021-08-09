from django.apps import apps

from .utils.links import Link


class Group:
    def __init__(
        self,
        label,
        iconname=None,
        permissions=[],
        order=None,
        sort_alphabetically=False,
    ):
        self.label = label
        self.iconname = iconname or "folder"
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
        return any(item.active(request) for item in self.items)


def try_call(var, *args, **kwargs):
    return var(*args, **kwargs) if callable(var) else var


class Action:
    """Represents a user-clickable action
    js, label, icon and permissions can be str, lazy string or a callable function.
    The function takes the current request as the only argument.
    """

    def __init__(self, js, label="", iconname=None, permissions=[]):
        self.js = js
        self.label = label
        self.iconname = iconname
        self._permissions = permissions

    def has_permission(self, request, obj=None):
        return all(
            [
                request.user.has_perm(perm, obj) or request.user.has_perm(perm)
                for perm in try_call(self._permissions, request)
            ]
        )


class Item:
    def __init__(self, link, group, order=None):
        if not isinstance(link, Link):
            raise ValueError(
                f"argument 'link' must be of type {Link} but is of type {type(link)}"
            )
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
        path = str(self.link.href)
        return request.path.startswith(path) and path != "/"


class Menu:
    def __init__(self):
        self._registry = {}

    def registeritem(self, menuitem):
        """
        If menuitem.group is None this will be a top-level menu item.
        Otherwise the group will be created (if a group with the same label does not exists yet) and the menuitem appended to the group
        """
        if menuitem.group is None:
            if menuitem.link.label in self._registry:
                raise ValueError(
                    f"Top-level menu item {menuitem} already exists in menu"
                )
            self._registry[menuitem.link.label] = menuitem
        else:
            group = menuitem.group
            if isinstance(group, str):
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
