# Generated by Django 4.1.2 on 2022-11-25 10:49

from django.db import migrations


class Migration(migrations.Migration):
    def update_cell_templates(apps, _):
        for column in apps.get_model("reports.ReportColumn").objects.all():
            if column.cell_template and "value.format" in column.cell_template:
                column.cell_template = column.cell_template.replace(
                    "value.format", "value|date"
                )
                column.save()

    dependencies = [
        ("reports", "0012_reportcolumn_allow_html_and_more"),
    ]

    operations = [
        migrations.RunPython(update_cell_templates, migrations.RunPython.noop)
    ]
