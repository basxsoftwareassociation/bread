# Generated by Django 4.0.5 on 2022-09-13 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('triggers', '0004_datachangetrigger_field'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='datachangetrigger',
            options={'verbose_name': 'Change trigger', 'verbose_name_plural': 'Change triggers'},
        ),
        migrations.AlterModelOptions(
            name='datefieldtrigger',
            options={'verbose_name': 'Date trigger', 'verbose_name_plural': 'Date triggers'},
        ),
        migrations.AlterModelOptions(
            name='sendemail',
            options={'verbose_name': 'Send email action', 'verbose_name_plural': 'Send email actions'},
        ),
        migrations.AlterField(
            model_name='datachangetrigger',
            name='field',
            field=models.CharField(blank=True, help_text='Only trigger when a certain field has changed. Use comma to add multiple fields.', max_length=255, verbose_name='Field'),
        ),
    ]
