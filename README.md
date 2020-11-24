Important
=========

This repo is in alpha-stage and highly experimental. We will not keep any backwards-compatability during the next few months. We work on improving stability as well as adding documentation and tests.

TODO before going to beta
-------------------------

- Finish this readme
- Documentation, partly prepared under docs, using the sphinx documentation system
- Create readthedocs deployment
- Some of the carbon-components still need to be implemented
- Add index here: https://djangopackages.org/grids/
- Create pip-distribution
- Review test-system, make test-runner
- Enforce python standards: black, isort, flake8, bandit (https://github.com/psf/black/blob/master/docs/compatible_configs.md, for black-flake8)


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
