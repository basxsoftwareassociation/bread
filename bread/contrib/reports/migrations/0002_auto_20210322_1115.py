# Generated by Django 3.1.7 on 2021-03-22 04:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="reportcolumn",
            options={"verbose_name": "Column", "verbose_name_plural": "Columns"},
        ),
        migrations.AlterOrderWithRespectTo(
            name="reportcolumn",
            order_with_respect_to="report",
        ),
    ]
