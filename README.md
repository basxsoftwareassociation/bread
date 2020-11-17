TODO
=========================

- Finish this readme
- Documentation, partly prepared under docs, using the sphinx documentation system
- Quite some of the carbon-components still need to be implemented
- Add license (BSD 3 clause)
- Add index here: https://djangopackages.org/grids/
- Create pip-distribution
- Maybe: Add a workflow-subsystem, should maybe be in another repo as a separate app since it would contains models



BREAD Engine
------------

This package provides functionality to create django database applications in a quick and customizable way.


Example
-------

myapp/models.py

    from django.db import models

    class Book(models.Model):
        title = models.CharField(max_length=255)
        authors = models.ManyToManyField(Author)
        publisher = models.ForeignKey(Publisher)
        publication_date = models.DateField()
    
        der __str__(self):
            return self.title

    class Publisher(models.Model):
        name = models.CharField(max_length=255)


myapp/bread.py


    from bread.admin import BreadAdmin, register

    @register
    class Book(BreadAdmin):
        model = models.Book

    @register
    class Publisher(BreadAdmin):
        model = models.Publisher


Installation
------------

    python3 -m venv .venv
    . .venv/bin/activate
    pip install bread
    django-admin startproject --template .venv/lib/python3.7/site-packages/bread/resources/project_template.tar.gz myproject .
    ./manage.py migrate

Limitions
---------

Many...

Necessary tools for certain multimedia features (thumbnails etc)
----------------------------------------------------------------
- ffmpeg
- libreoffice
- inkscape
- poppler-utils

(install with apt and flag --no-install-recommends)
