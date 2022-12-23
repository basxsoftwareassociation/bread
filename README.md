[![CI](https://github.com/basxsoftwareassociation/bread/actions/workflows/main.yml/badge.svg)](https://github.com/basxsoftwareassociation/bread/actions/workflows/main.yml)
[![Documentation Status](https://readthedocs.org/projects/basx-bread/badge/?version=latest)](https://basx-bread.readthedocs.io/en/latest/?badge=latest)
[![Translation status](https://hosted.weblate.org/widgets/basxconnect/-/bread/svg-badge.svg)](https://hosted.weblate.org/engage/basxconnect/)


Documentation
-------------

Documentation is hosted at [readthedocs.io](https://basx-bread.readthedocs.io/en/latest/)


BasxBread Engine
------------

This package provides functionality to create Django-based database
applications in a quick and customizable way. Similar concepts are CRUD
(create-read-update-delete) frameworks or RAD (rapid application development)
tools.

BasxBread relies in many regards on the Django web framework. Familiarity with
Django is highly recommended and assumed for readers of the documentation.

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
    django-admin startproject --template $( pip show basx-bread | grep '^Location: ' | cut -c 11- )/basxbread/resources/project_template/ myproject . # template-project for basxbread

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
    from basxbread.utils import quickregister
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


Notes on maintenance
--------------------

Most of the code that is being written for BasxBread is developed while doing
payed work. That way the development and maintenance of the framework can be
done in a sustainable manner.

Future plans
------------

BasxBread is currently running on a range of custom database applications that
are used in production. Most parts of the framework are now on a level that we
consider production ready. However, there are some additions and improvments
that we still would like to work on. Those are listed here.

Refactorings:

(Maybe move this stuff into Github issues)

- [ ] We should really go over our documentation...
- [ ] Change implementation of some things where not the HTML/REST-paradigm is
  used but a custom javascript hack. This might reduce some of the "asthetical"
  behaviour, like clickable table rows. However, for customization and
  composition of different UI elements it is always preferable to use standard
  HTML behaviour and features where possibel.
- [ ] Current-menu-item-selection. Right now the currently active menu item is
  only detected via prefix-matching of the current URL. This can lead sometimes
  to incorrect behaviour, if two menu items have a similar prefix. There should
  be an unambigous way to determine the currently active menu item, maybe even
  for pages that are deeper in the navigation hierarchy
- [ ] Pre-defined querysets with direct links for BrowseViews. BrowseViews
  would benefit of a short-cut system, where frequently used filters can be
  defined in the code and are displayed as links in the datatable header.
- [ ] Improve definition of URL patterns and navigation hierarchy. No idea what
  would be a good, generic approach, maybe take some stuff from DRF.

New features

- [ ] Data analytics with graphs [analytics]: In order to allow producing nice
  graphs, exploring all the data and getting statistical insights a data
  analytics-tool would be really nice to have.
- [ ] Editing models via the web UI [modeledit]: This is a feature which
  almost all of the bigger database frameworks and CRM support. But BasxBread
  main goal is to empower the developer and end-user accessible model
  definitions increase developer friction substantialy. However, there are
  many cases where a project would benefit if certain changes can be done
  without having to update code and make a new deployment. Therefore we are
  experimenting with a feature that would allow users to add and modify
  certain models via the web-interface. The implementation would still rely on
  code-defined models. The web-UI would translate the desired changes into an
  automated version of what the developer would normally do, i.e. updating the
  model definition in the source code, creating migrations, running migrations
  and restart the application server.
- [ ] Customizable menu [custommenu]: Currently the navigation menu must be
  defined via code. Allowing the configuration of the menu via database would
  be an advantage for users. Two things to keep in mind for this are: It must
  still be easy for developers to quickly add menus to test models and custom
  pages. And also, the current feature set (e.g. icons and permissions)
  for menu items should be supported in a database implementation.
- [ ] More/better customization of custom forms.
- [ ] Add feature do define custom layouts.
