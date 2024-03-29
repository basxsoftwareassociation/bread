# Generated by Django 4.0.5 on 2022-09-07 03:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0011_reportcolumn_cell_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportcolumn',
            name='allow_html',
            field=models.BooleanField(default=False, help_text='Do render HTML code inside the cell template instead of escaping it.', verbose_name='Allow HTML'),
        ),
        migrations.AlterField(
            model_name='reportcolumn',
            name='cell_template',
            field=models.TextField(blank=True, help_text="Optional Jinja template with 'value' in context.<br/>Use e.g. {{ value }} to simply display the value.", verbose_name='Cell template'),
        ),
    ]
