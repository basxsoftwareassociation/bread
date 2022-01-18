from django.apps import AppConfig


class TriggersConfig(AppConfig):
    name = "bread.contrib.triggers"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        post_save.connect(save_handler, dispatch_uid="trigger_save")
        post_delete.connect(delete_handler, dispatch_uid="trigger_delete")


def save_handler(sender, **kwargs):
    print("saved", sender, kwargs)


def delete_handler(sender, **kwargs):
    print("saved", sender, kwargs)
