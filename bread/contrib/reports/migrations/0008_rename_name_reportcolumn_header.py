# Generated by Django 3.2.12 on 2022-04-06 10:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_report_pagination'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reportcolumn',
            old_name='name',
            new_name='header',
        ),
    ]
