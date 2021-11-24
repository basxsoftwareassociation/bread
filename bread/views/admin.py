import htmlgenerator as hg
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from bread import layout
from bread.layout import admin
from bread.layout.components.datatable import DataTableColumn
from bread.utils.urls import aslayout
from bread.views import BrowseView

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


class TaskResultBrowseView(BrowseView):
    columns = [
        DataTableColumn(
            layout.ObjectFieldLabel("task_id", TaskResult),
            hg.DIV(
                hg.C("row.task_id"),
            ),
            "task_id",
        ),
        DataTableColumn(
            layout.ObjectFieldLabel("task_name", TaskResult),
            hg.DIV(
                hg.C("row.task_name"),
            ),
            "task_name",
        ),
        DataTableColumn(
            _("Date Created"),
            hg.DIV(
                hg.C("row.date_created"),
            ),
            "date_created",
        ),
        DataTableColumn(
            _("Date Completed"),
            hg.DIV(
                hg.C("row.date_done"),
            ),
            "date_done",
        ),
        "status",
        "worker",
        "content_type",
        DataTableColumn(
            _("Metadata"),
            hg.DIV(
                hg.C("row.meta"),
            ),
        ),
    ]
    rowclickaction = BrowseView.gen_rowclickaction("read")
    title = "Background Jobs"
