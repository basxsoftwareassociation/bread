# Generated by Django 4.1.2 on 2022-10-11 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("triggers", "0008_alter_datefieldtrigger_offset_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sendemail",
            name="email",
            field=models.CharField(
                help_text="\nSyntax:\n- Email: example@example.com\n- User/Group: @username\n- From object: object.manager.email\n\nMultiple values van be separated by comma , e.g.\nboss@example.com, @adminuser, @reviewteam, primary_email_address.email\n",
                max_length=255,
                verbose_name="Email",
            ),
        ),
    ]
