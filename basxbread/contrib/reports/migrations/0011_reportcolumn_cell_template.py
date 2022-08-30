# Generated by Django 4.0.5 on 2022-08-24 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_alter_reportcolumn_sortingname'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportcolumn',
            name='cell_template',
            field=models.TextField(blank=True, help_text="Jinja template with 'value' in context", verbose_name='Cell template'),
        ),
    ]