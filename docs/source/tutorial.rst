Tutorial
========

In order to get a better understand of how to start building 
web-based database applications with |project| we provide
a tutorial. The goal is to write a small multi-user todo-
application from scratch.

Requirements
------------

Required software:

- Python >= 3.6
- pip (should in most cases come with Python)

We will be using Python 3.9 in the tutorial but the choice does
not really matter. The best option is the standard version of your
operating system as long as it is Python 3.6 or higher.

Setup
-----

To get a fresh project up and running we run the following commands in a terminal:

::

    python3 -m venv .venv
    . .venv/bin/activate
    pip install basx-bread
    django-admin startproject --template .venv/lib/python3.9/site-packages/basxbread/resources/project_template todo .

In case you are not familiar with a standard Python or Django setup here are some explanations:

- ``python3 -m venv .venv`` will set up an isolated Python environment where all project dependencies
  will be installed to.
- ``. .venv/bin/activate`` activates the environment. This command should be run every time you work on the project.
- ``pip install basx-bread`` installes the |project| package
- ``django-admin startproject ...`` will setup a new django project with the name ``todo`` in the current directory.
  Note that we use the project template from |project| in order to get a quick default configuration. However, it is no
  problem to add |project| to any existing Django project.

Our project is still empty. In order to add models and pages we need to add a so called "app".
Apps are a Django concept to separate different functionality in different packages.
Since the name of the project is "todo" we need to choose a different name for the app itself.
This seems redundant for a small project like this but is important when projects grow and consist of many different parts.

We will call our app "mytodos" and set it up with the following command:

::

    ./manage.py startapp mytodos

This will an additional directory with the name of our app "mytodos".

Before we continue we need to manyally add our new app to the projects app list.
Open the file ``todo/settings/base.py`` and add the value ``"mytodods"`` to 
``INSTALLED_APPS``, just before the other entries (``"django.contrib.admin"`` 
should already be there).

The next step is to initiate the database and create a super user. For this simply run
the following two commands and fill in username and password when asked (email is not
required).

::
    
    ./manage.py migrate
    ./manage.py createsuperuser

In order to test the setup you can start the development server:

::
    
    ./manage.py runserver

Visit http://127.0.0.1:8000/ and login with the just created super user credentials.
If everything went well you should see a default page with system information.

So, this is the basic setup that needs to be done for any new |project| project.
We are now ready to develop our Todo application.
But before we move on to that we will take a quick look at the current project structure in the next chapter.


What are all these files doing here?
------------------------------------

If you followed the previous chapters step by step you should now have quite a few files in your directory by now.
We list them here with comments if you want a better understanding what the purpose each file is:

::

    ├── asgi.py               # configuration file for an asynchrounes web application server
    ├── db.sqlite3            # our newly created database
    ├── manage.py             # main script to manage a Django project
    |
    ├── mytodos               # content of our todo application
    │   ├── admin.py          # unused default file for Django projects, can be removed
    │   ├── apps.py           # configuration for the "mytodos" app
    │   ├── __init__.py       # empty, marks a python package
    │   ├── migrations        # auto-generated directory from Django, stores database migrations
    │   ├── models.py         # will contain all model definitions for the "mytodos" app
    │   ├── tests.py          # unused default file for Django projects, can be removed 
    │   └── views.py          # will contain all views for the "mytodos" app
    |
    ├── requirements.txt      # project dependencies, currently only one entry
    |
    ├── todo                  # project configuration and settings
    │   ├── celery.py         # configuration file for celery to run background tasks
    │   ├── __init__.py       # empty, marks a python package
    │   ├── settings          # 
    |   |   ├── base.py       # default django settings and configuration for the project
    |   |   ├── dev.py        # settings for local development
    |   |   ├── __init__.py   # empty, marks a python package
    |   |   └── production.py # settings for production deployment
    │   └── urls.py           # root URL configuration, all URLs which are handed by this 
    |                         # application must somehow be listed or included here
    |
    └── wsgi.py               # configuration file for an web application server like uWSGI

A short note for readers who are unfamiliar with Django concepts: *models* translate to database table definitions and *views* translate to HTML pages.

In case these seems like a daunting amount of files and configuration keep in mind: This setup is ready to be deployed directly 
to a production environment. It comes with all the necessary features and configuration which a real world enterprise-level database applications requires.


In the beginning there was the model
------------------------------------

For most database- or domain-driven projects we will want to think about the datamodel that is required to 
provide the desired functionality. The datamodel for our small Todo application is rather simple and fits
in a single model class. Edit the file ``mytodos/models.py`` to contain the following model definition:

::

    from django.db import models

    class ToDo(models.Model):
        what = models.CharField(max_length=255)
        due = models.DateTimeField(null=True, blank=True)
        done = models.DateTimeField(null=True, blank=True)
        creator = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="todos")
        created = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return self.what[:30]

        class Meta:
            verbose_name = "ToDo"
            verbose_name_plural = "ToDos"
            ordering = ["due"]

For the excat semantics of the model definition as well as the ``Meta`` configuration please refer to :py:mod:`django:django.db.models`

Now, in order to have the according database strucuture set up we need to create migrations and run them:

::

    ./manage.py makemigrations mytodos
    ./manage.py migrate

This is a typical cycle when developing Django models. In the next chapter we hook up our modle to make it visible in the front-end.

A minimal viable product
------------------------

In this step we will register the URLs and views and the initial version of the app up and running.
The most simple CRUD-views can easily be added by creating the file ``mytodos/urls.py`` and add the following shortcut:

::

    from basxbread.utils import quickregister
    from . import models

    urlpatterns = []
    quickregister(urlpatterns, models.ToDo)

Then we register our URLs in the main project URL-registry at ``todo/urls.py``.
This is done by making sure the following lines exist inside that file.
Make sure to replace the line with RedirectView in order to make the list of todos the landing page.

::

    ...
    from django.urls import path, include
    ...

    urlpatterns = [
        path("", RedirectView.as_view(pattern_name="mytodos.todo.browse")),
        ...
        path("", include("mytodos.urls"))
        ...
    ]

The website should now offer a simple interface to list, create, edit and delete to-do entries.

Tidy things up a bit
-----------------------

TODO

- Displayed columns
- Add and edit views
- Status labels

And action!
-----------

TODO

- Actions and bulk actions

Multiplayer
-----------

- Permissions, roles
- Per-object permissions

Reminders
---------

TODO

- Adding tasks

Getting real
------------

TODO

- production deployment
- nginx
- uwsgi
