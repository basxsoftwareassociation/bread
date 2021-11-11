import htmlgenerator as hg
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _

from bread import layout
from bread.layout import admin
from bread.utils.urls import aslayout

R = layout.grid.Row
C = layout.grid.Col

TR = layout.datatable.DataTable.row
TD = layout.datatable.DataTableColumn


@user_passes_test(lambda user: user.is_superuser)
@aslayout
def maintenancesettings(request):
    # Add the view's header
    ret = layout.grid.Grid(R(C(hg.H3(_("Maintenance")))), gutter=False)

    # Add the Package Information modal
    ret.append(
        R(
            C(
                hg.H4(_("Packages")),
                admin.maintainance_package_layout(request),
            ),
            C(
                hg.H4(_("Database Optimization")),
                admin.maintenance_database_optimization(request),
            ),
        )
    )

    return ret


@aslayout
def backgroundjobs(request):
    return hg.H3("Coming Soon")
