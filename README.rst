BREAD Engine
------------

This package provides functionality to create extendable django database applications very quickly.

    from django.db import models

    class Book(models.Model):
        title = models.CharField(max_length=100)
        authors = models.ManyToManyField(Author)
        publisher = models.ForeignKey(Publisher)
        publication_date = models.DateField()
    
        der __str__(self):
            return self.title

Installation
------------

    python3 -m venv .venv
    . .venv/bin/activate
    pip install bread
    django-admin startproject --template .venv/lib/python3.7/site-packages/bread/resources/project_template.tar.gz myproject .
    ./manage.py migrate

Necessary tools for certain multimedia features (thumbnails etc)
----------------------------------------------------------------
- ffmpeg
- libreoffice
- inkscape
- poppler-utils

(install with apt and flag --no-install-recommends)
