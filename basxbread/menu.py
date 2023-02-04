import htmlgenerator as hg
from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.auth.models import User
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from . import utils
from .layout import DEVMODE_KEY


class Group:
    def __init__(
        self,
        label,
        iconname=None,
        permissions=[],
        order=None,
        sort_alphabetically=False,
        force_show=False,
    ):
        self.label = label
        self.iconname = iconname or "folder"
        self.permissions = permissions
        self._order = order
        self.items = []
        self.sort_alphabetically = sort_alphabetically
        self.force_show = force_show

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

    def active(self, request):
        return any(item.active(request) for item in self.items)


class Item:
    def __init__(self, link, group, order=None):
        if not isinstance(link, utils.Link):
            raise ValueError(
                f"argument 'link' must be of type {utils.Link} but is of type {type(link)}"
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

    def active(self, context):
        path = str(hg.resolve_lazy(self.link.href, context))
        return context["request"].path.startswith(path) and path != "/"


class Menu:
    def __init__(self):
        self._registry = {}

    def registeritem(self, menuitem):
        """
        If menuitem.group is None this will be a top-level menu item.
        Otherwise the group will be created (if a group with the same
        label does not exists yet) and the menuitem appended to the group
        """
        if menuitem.group is None:
            if menuitem.link.label in self._registry:
                raise ValueError(
                    f"Top-level menu item {menuitem} already exists in menu"
                )
            self._registry[menuitem.link.label] = menuitem
        else:
            group = menuitem.group
            if isinstance(group, (str, Promise)):
                group = Group(label=group)
                menuitem.group = group
            if group.label not in self._registry:
                self._registry[group.label] = group
            self._registry[group.label].items.append(menuitem)


class DevGroup(Group):
    def has_permission(self, request):
        return super().has_permission(request) and request.session.get(
            DEVMODE_KEY, False
        )


class SuperUserItem(Item):
    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser


def registeritem(item):
    main.registeritem(item)
    return item


# global main menu
main = Menu()

settingsgroup = Group(_("Settings"), iconname="settings", order=100)
usergroup = Group(_("Users"), iconname="user", order=101)

registeritem(
    Item(
        utils.Link(
            utils.reverse_model(User, "browse"),
            User._meta.verbose_name_plural,
            permissions=[utils.permissionname(User, "view")],
        ),
        usergroup,
    )
)
registeritem(
    Item(
        utils.Link(
            utils.reverse_model(DjangoGroup, "browse"),
            DjangoGroup._meta.verbose_name_plural,
            permissions=[utils.permissionname(DjangoGroup, "view")],
        ),
        usergroup,
    )
)
registeritem(
    Item(
        utils.Link(
            utils.reverse("preferences:global"),
            _("Global preferences"),
            permissions=[
                "dynamic_preferences.change_globalpreferencemodel",
                "dynamic_preferences.view_globalpreferencemodel",
            ],
        ),
        settingsgroup,
    )
)

# The Administration items are registered by default.
admingroup = DevGroup(_("Administration"), iconname="network--3--reference", order=500)
registeritem(
    Item(
        utils.Link(
            utils.reverse("django_celery_results.taskresult.browse"),
            _("Background Jobs"),
        ),
        admingroup,
    )
)

registeritem(
    SuperUserItem(
        utils.Link(utils.reverse("admin:index"), _("Django Admin")), admingroup
    )
)

registeritem(
    SuperUserItem(
        utils.Link(
            utils.reverse("basxbreadadmin.maintenance"),
            _("Maintenance"),
        ),
        admingroup,
    )
)

registeritem(
    Item(
        utils.Link(
            utils.reverse("systeminformation"),
            _("System Information"),
        ),
        admingroup,
    )
)
registeritem(
    Item(
        utils.Link(
            utils.reverse("basxbreadadmin.componentpreview"),
            _("Component Preview"),
        ),
        admingroup,
    )
)
