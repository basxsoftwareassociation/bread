# Generated by Django 4.1.2 on 2022-11-25 10:57

from django.db import migrations


class Migration(migrations.Migration):
    def update_cell_templates(apps, _):
        for column in apps.get_model(
            "document_templates.DocumentTemplateVariable"
        ).objects.all():
            if column.template and "value.format" in column.template:
                column.template = column.template.replace("value.format", "value|date")
                column.save()

    dependencies = [
        ("document_templates", "0005_documenttemplate_filename_template"),
    ]

    operations = [
        migrations.RunPython(update_cell_templates, migrations.RunPython.noop)
    ]