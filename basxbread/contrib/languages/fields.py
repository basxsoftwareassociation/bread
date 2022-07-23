from django.db.models.fields import CharField


class LanguageField(CharField):
    """
    A language field for Django models.
    """

    def __init__(self, *args, **kwargs):
        # Local import so the languages aren't loaded unless they are needed.
        from .languages import LANGUAGES

        kwargs.setdefault("max_length", 3)
        kwargs.setdefault("choices", LANGUAGES)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["choices"]
        return name, path, args, kwargs
