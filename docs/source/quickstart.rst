Quickstart ...
==============

Required tools (assumed to be run on a linux system):

* git
* make
* python3 (with venv, python development files and a build environment)

... with example project (CRM)
------------------------------

A fully functional implementation of a CRM is available through the 
`basxconnect <https://github.com/basxsoftwareassociation/basxconnect>`_
project. In the first part of the quickstart guide we will use this project
to get a customizable CRM up and running very quickly.


.. code-block:: shell

    git clone https://github.com/basxsoftwareassociation/basxconnect_demo.git
    cd basxconnect_demo
    make quickstart_debian
    # alternatively: make quickstart_fedora
    # for other systems follow the instructions inside the Makefile
    . .venv/bin/activate
    ./manage.py runserver

After running the lines above the CRM is available at http://127.0.0.1:8000
and login with the username `demo` and the password `connectdemo`.

... from scratch (Event management)
-------------------------------------

In the second part of the quickstart guide we will go through the process
of setting up a fresh Django project, adding |project| and defining models and views.

Setup
*****

Setup up the basic project structure by running the following commands in a terminal:

.. code-block:: shell

    mkdir eventdemo && cd eventdemo
    python3 -m venv .venv
    . .venv/bin/activate
    pip install Django git+https://github.com/basxsoftwareassociation/htmlgenerator.git git+https://github.com/basxsoftwareassociation/bread.git
    django-admin startproject eventmanagement .
    django-admin startapp events

This will generate the following directory structure::

    .
    ├── events
    │   ├── admin.py
    │   ├── apps.py
    │   ├── __init__.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models.py
    │   ├── tests.py
    │   └── views.py
    ├── eventmanagement
    │   ├── asgi.py # only interesting for production deployments
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py # only interesting for production deployments
    └── manage.p

This is a default django project structure and not all files are actually needed.
We will focus on the files ``events/models.py``, ``eventmanagement/settings.py`` and ``eventmanagement/urls.py``

Model definition
****************

The next step is to define our data model.
In case you are familiar with creating Django applications this will be the same as always.
If you are new to Django you might want to read :py:mod:`django:django.db.models` in addition to this guide.
Django models are essentialy an abstraction over SQL tables and provide a very straight forward database API as well as support for data model migrations.
When using |project| it is assumed that you know how to develop relational data models for your application.
This means additional effort for the application developer but prevents unnecessary restrictions on the modeling side.
Further it allows the framework to be used in many different kinds of scenarios.

Let us get started with a small example model for managing events and registrations::

    # events/models.py

    from django.db import models
    

    class Event(models.Model):
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True)
        date = models.DateField()
        time = models.TimeField(null=True, blank=True)

        def __str__(self):
            return self.name

    class Registration(models.Model):
        event = models.ForeignKey(Event, on_delete=models.CASCADE)
        attendee_name = models.CharField(max_length=255)
        attendee_phone = models.CharField(max_length=16)
        attendee_email = models.EmailField()



This is just a very basic example.
There are many things which could be taken into consideration.
However, for this quickstart we will try to keep the complexity low.

URLs
****

Creating the |project| user interface for the application is done by registering the default views with the shortcut :py:func:`basxbread.utils.urls.default_model_paths`::

    # eventmanagement/urls.py

    from basxbread import views, menu
    from django.views.generic import RedirectView
    from basxbread.utils.urls import default_model_paths, reverse_model
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.urls import include, path

    from events import models

    urlpatterns = (
        [
            path("", include("basxbread.urls")),
            path("", RedirectView.as_view(url="/accounts/login/")),
        ]
        + default_model_paths(
              models.Event, browseview=views.BrowseView._with(rowclickaction="edit")
          )

        + staticfiles_urlpatterns()
    )

    menu.registeritem(
        menu.Item(menu.Link(reverse_model(models.Event, "browse"), "Events"), "Events")
    )

The :py:func:`basxbread.utils.urls.default_model_paths` shortcut does only require a single argument, the desired model to generate URLs for.
We add here an optional argument ``browseview`` to parameterize the browse view. By setting ``rowclickaction`` to ``"edit"`` a click on an entry in the browse list will open the according edit-form of the clicked item.


Settings
********

In order to get |project| working correctly we need to make a few changes to the django settings file at ``eventmanagement/settings.py``.
There is a full list of recommended settings inside the module :py:mod:`basxbread.settings.required`.

::

    # eventmanagement/settings.py

    ...

    INSTALLED_APPS = [
        # our custom event app
        "events",
        # required 3rd party dependencies
        "basxbread",
        "djangoql",
        "guardian",
        "compressor",
        "dynamic_preferences",
        "dynamic_preferences.users.apps.UserPreferencesConfig",
        # default django apps
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]

    ...

    # Setup for django-compressor to compress and serve SCSS and other
    # static files
    STATIC_ROOT="static"

    from basxbread.settings.required import LIBSASS_ADDITIONAL_INCLUDE_PATHS
    COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
    STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "compressor.finders.CompressorFinder",
    ]

    # Django will redirect to /accounts/profile by default but we want to
    # access our events directly
    LOGIN_REDIRECT_URL = "/events/event/browse"


Running the application
***********************

In order to run the application we first need to create migration files which are used to create our event tables::

    ./manage.py makemigrations

Now we execute these migrations and create and populate the initial database::

    ./manage.py migrate

The initial super user needs also to be created via commandline::

    ./manage.py createsuperuser


Finally we can start the application in development mode and open the browser at http://127.0.0.1:8000::

    ./manage.py runserver

.. note:: Coming soon: Adding registrations to an event

.. note:: Coming soon: Precompile the css files for better loading times
