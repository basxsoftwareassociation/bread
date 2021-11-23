from celery import Task


class RepeatedTask(Task):
    @classmethod
    def on_bound(cls, app):
        app.conf.beat_schedule[cls.name] = {
            "task": cls.name,
            "schedule": cls.run_every.total_seconds(),
            "args": (),
            "kwargs": {},
            "options": getattr(cls, "options", {}),
            "relative": getattr(cls, "relative", False),
        }
