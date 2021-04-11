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

In the second part of the quickstart guide we will go through a the process
of setting up a fresh Django project, adding |project| and defining models and views.

Setup
*****

Setup up the basic project structure:

.. code-block:: shell

    mkdir library_demo && cd library_demo
    python3 -m venv .venv
    . .venv/bin/activate
    pip install Django git+https://github.com/basxsoftwareassociation/bread.git
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
    │   ├── asgi.py
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── manage.p


Model definition
****************

The next step is to define our data model. In case you are familiar with creating Django application this will be the same as you are familiar with.
If you are new to Django you might want to read :py:mod:`django:django.db.models` in addition to this guide.
Django modles are essentialy an abstraction over SQL tables and provide a very straight forward API as well as support for data model migrations.
When using |project| is is assumed that you know how to develop relational data models for your application.
This means additional effort for the application developer but prevents unnecessary restrictions on the modeling side.
Further it allows the framework to be used in all different kinds of project contexts.

So, let us get started with a small example model in order manage events and registrations::

    # library/models.py

    from django.db import models
    

    class Event(models.Model):
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True)
        date = models.DateField()
        time = models.TimeField(blank=True, blank=True)

    class Registration(models.Model):
        event = models.ForeignKey(Event, on_delete=models.CASCADE)
        attendee_name = models.CharField(max_length=255)
        attendee_phone = models.CharField(max_length=16)
        attendee_email = models.EmailField()



This is just a very basic example. There are many things which could be taken into consideration.
For this quickstart we will try to keep the complexity low.

Views
*****

.. note:: TODO

URLs
****

.. note:: TODO

Settings
********

.. note:: TODO


Running the application
***********************

The file we created contains the our model definition but we first need to tell Django to create migrations (which basically is Python code describing the required SQL commands)::

    ./manage.py makemigrations

In order to execute these migrations and create and populate the initial database we need to call::

    ./manage.py migrate

The initial super user needs to created via commandline::

    ./manage.py createsuperuser


Finally we can start the application in development mode and access the application at http://127.0.0.1:8000::

    ./manage.py runserver

