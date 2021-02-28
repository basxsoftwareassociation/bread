import htmlgenerator as hg
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from bread import layout

from .fields.modelfieldlookup import ModelFieldLookup
from .fields.queryfield import QuerysetField


class Report(models.Model):
    created = models.DateField(_("Created"), auto_now_add=True)
    model = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    filter = QuerysetField(_("Filter"), modelfieldname="model")

    @property
    def preview(self):
        return hg.BaseElement(
            hg.H3(_("Preview")),
            layout.datatable.DataTable.from_queryset(self.filter.queryset, wrap=False),
        )

    def __str__(self):
        return f"{self.model.model_class()._meta.verbose_name_plural} {self._meta.verbose_name} #{self.id}"

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")


class ReportColumn(models.Model):
    AGGREGATIONS = {
        "count": "",
        "sum": "",
    }
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    column = ModelFieldLookup(_("Column"))
    aggregation = models.CharField(
        _("Aggregation"), max_length=64, choices=tuple(AGGREGATIONS.items()), blank=True
    )
