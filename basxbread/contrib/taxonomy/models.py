from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class VocabularyManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                termcount=models.Count(
                    "term", output_field=models.IntegerField(_("Terms"))
                )
            )
        )


class Vocabulary(models.Model):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        help_text=_("slug is human-readable, to make referencing easier"),
    )

    objects = VocabularyManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = _("Vocabulary")
        verbose_name_plural = _("Vocabularies")


class TermManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(disabled=False)

    def including_disabled(self):
        return super().get_queryset()


class Term(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, null=False, on_delete=models.CASCADE)
    vocabulary.verbose_name = _("Vocabulary")
    term = models.CharField(_("Term"), max_length=255)
    slug = models.CharField(_("Slug"), max_length=255, unique=True, blank=True)
    disabled = models.BooleanField(
        _("Disabled"),
        default=False,
        help_text=_("Do not allow this term to be selected"),
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.vocabulary.slug + "__" + slugify(self.term)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.term

    objects = TermManager()

    class Meta:
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")
        order_with_respect_to = "vocabulary"
