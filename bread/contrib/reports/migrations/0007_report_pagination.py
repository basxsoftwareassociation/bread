# Generated by Django 3.2.12 on 2022-04-06 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_alter_report_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='pagination',
            field=models.PositiveIntegerField(default=0, help_text='How many items to display per page when viewing the report in the browser, 0 for everything on one page', verbose_name='Pagination'),
        ),
    ]
