# Generated by Django 3.2.6 on 2022-01-25 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('triggers', '0002_auto_20220125_0617'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datefieldtrigger',
            name='date_offset',
        ),
        migrations.AddField(
            model_name='datefieldtrigger',
            name='offset_amount',
            field=models.IntegerField(default=0, help_text='Can be negative (before) or positive (after)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datefieldtrigger',
            name='offset_type',
            field=models.CharField(choices=[('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], default='days', max_length=255),
            preserve_default=False,
        ),
    ]