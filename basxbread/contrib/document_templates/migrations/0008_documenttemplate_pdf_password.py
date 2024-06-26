# Generated by Django 4.1.7 on 2024-06-26 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("document_templates", "0007_alter_documenttemplatevariable_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="documenttemplate",
            name="pdf_password",
            field=models.CharField(
                blank=True,
                help_text="An optional password that will be set on generated PDFs",
                max_length=2048,
                verbose_name="PDF-Password",
            ),
        ),
    ]
