# Generated by Django 3.2.12 on 2022-04-09 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_auto_20220406_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportcolumn',
            name='sortingname',
            field=models.CharField(blank=True, help_text='Django sorting expression', max_length=255, verbose_name='Sortingname'),
        ),
    ]
