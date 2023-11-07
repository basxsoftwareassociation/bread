from itertools import chain

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField

try:
    from itertools import pairwise
except ImportError:
    # python<3.10 compatability
    from itertools import tee

    def pairwise(iterable):  # type: ignore
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)


import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .datatable import DataTable, DataTableColumn


def changes(model, c):
    old, new = c["row"]

    # marks the end of changes-chain
    if new is None:
        return ()

    return list(old.diff_against(new).changes)


def haschanges(old, new):
    if new is None:
        return False
    return len(old.diff_against(new).changes) > 0


def fieldname(c, model):
    try:
        return model._meta.get_field(c["change"].field).verbose_name
    except FieldDoesNotExist:
        return c["change"].field.replace("_", " ").capitalize()


def newfieldvalue(c, model):
    try:
        field = model._meta.get_field(c["change"].field)
        if isinstance(field, RelatedField):
            try:
                return field.related_model.objects.get(id=int(c["change"].new))
            except field.related_model.DoesNotExist:
                return hg.SPAN(_("<Value has been deleted>"), style="color: red")
    except FieldDoesNotExist:
        pass
    return c["change"].new


def oldfieldvalue(c, model):
    try:
        field = model._meta.get_field(c["change"].field)
        if isinstance(field, RelatedField):
            ret = field.related_model.objects.filter(id=int(c["change"].old)).first()
            return ret or hg.SPAN(_("<Value has been deleted>"), style="color: red")
    except FieldDoesNotExist:
        pass
    return c["change"].old


def diff_table(model, historylist):
    from ...layout import localize, localtime

    def historyentries(c):
        entries = historylist(c)
        if len(entries) == 0:
            return ()
        return (
            (i, j)
            for i, j in pairwise(chain(entries, [type(entries.first())()]))
            if haschanges(i, j)
        )

    return DataTable(
        row_iterator=hg.F(historyentries),
        columns=[
            DataTableColumn(
                _("Date"),
                hg.BaseElement(
                    localize(localtime(hg.C("row")[0].history_date).date()),
                    hg.If(
                        hg.F(lambda c: c["row"][1].history_date is None),
                        hg.BaseElement(" (", _("Created"), ")"),
                    ),
                ),
            ),
            DataTableColumn(
                _("Time"),
                localize(localtime(hg.C("row")[0].history_date).time()),
            ),
            DataTableColumn(
                _("User"),
                hg.C("row")[0].history_user,
            ),
            DataTableColumn(
                _("Changes"),
                hg.UL(
                    hg.Iterator(
                        hg.F(lambda c: changes(model(c), c)),
                        "change",
                        hg.LI(
                            hg.SPAN(
                                hg.F(lambda c: fieldname(c, model(c))),
                                style="font-weight: 600",
                            ),
                            ": ",
                            hg.SPAN(
                                hg.If(
                                    hg.C("change").old,
                                    hg.BaseElement(
                                        hg.F(lambda c: oldfieldvalue(c, model(c))),
                                        " -> ",
                                    ),
                                ),
                                style="text-decoration: line-through;",
                            ),
                            hg.SPAN(
                                hg.If(
                                    hg.C("change").new,
                                    hg.F(lambda c: newfieldvalue(c, model(c))),
                                    settings.HTML_NONE,
                                )
                            ),
                        ),
                    ),
                ),
            ),
        ],
    )
