[![CI](https://github.com/basxsoftwareassociation/bread/actions/workflows/main.yml/badge.svg)](https://github.com/basxsoftwareassociation/bread/actions/workflows/main.yml)
[![Documentation Status](https://readthedocs.org/projects/basx-bread/badge/?version=latest)](https://basx-bread.readthedocs.io/en/latest/?badge=latest)
[![Translation status](https://hosted.weblate.org/widgets/basxconnect/-/bread/svg-badge.svg)](https://hosted.weblate.org/engage/basxconnect/)


Documentation
-------------

Documentation is hosted at [readthedocs.io](https://basx-bread.readthedocs.io/en/latest/)


BREAD Engine
------------

This package provides functionality to create django database applications in a quick and customizable way. Similar concept are CRUD (create-read-update-delete) frameworks or RAD (rapid application development) tools.
BREAD is also partly a replacement of the django-admin interface, however, there is no API compatability to it.

Installation
------------

```bash
pip install basx-bread
```

Quickstart
----------

The following are the required step to get a new project quickly up and running.
For seasoned Django users there should be nothing new for the most parts.
In that case only the section *Registering the UI* might be worth reading.


### Setup

```bash
    python3 -m venv .venv
    . .venv/bin/activate # this is for bash, for windows use the script .venv/bin/Activate.ps1, there are also scripts for csh and fish
    pip install basx-bread # should run without problems, but users reported problems in some Mac setups due to native libraries missing
    django-admin startproject --template $( pip show basx-bread | grep '^Location: ' | cut -c 11- )/bread/resources/project_template/ myproject . # template-project for bread

    # adding a Django "app", Django projects consist of different apps with different models, pretty standard
    # can also be achieved with "python manage.py startapp mymodels" but it would create a few unnecessary files
    mkdir mymodels mymodels/migrations
    touch mymodels/__init__.py mymodels/migrations/__init__.py
    echo -e 'from django.apps import AppConfig\n\n\nclass Mymodels(AppConfig):\n    name = "mymodels"' > mymodels/apps.py
```

After this the file ```mymodels/models.py``` needs to be created and filled with your database models. Then add ```"mymodels"``` to the list of ```INSTALLED_APPS``` inside ```myproject/settings/base.py```.

### Registering the UI

In order to get started with the UI quickly the following code can be put into ```mymodels/urls.py```.
The code below assumes there exists a single model inside ```mymodels/models.py``` called ```MyModel```.

```python
    from bread.utils import quickregister
    from . import models

    urlpatterns = []
    quickregister(urlpatterns, models.MyModel)
```

The root URL list in ```myproject/urls.py``` needs to be extended with an item ```path("myapp", include("mymodels.urls"))```.


### Running the application

Finally run the following commands to initialize the database and start the development server.

```bash
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
```

The application can now be accessed via http://127.0.0.1:8000.

