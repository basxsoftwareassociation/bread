from setuptools import find_packages, setup


def readme():
    with open("README.md") as f:
        return f.read()


with open("bread/__init__.py") as f:
    # magic n stuff
    version = (
        [i for i in f.readlines() if "__version__" in i][-1]
        .split("=", 1)[1]
        .strip()
        .strip('"')
    )

setup(
    name="basx-bread",
    version=version,
    description="Engine to create database applications based on Django and the IBM Carbon Design System",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/basxsoftwareassociation/bread",
    author="basx Software Association",
    author_email="sam@basx.dev",
    license="New BSD License",
    install_requires=[
        # core dependencies
        "Django",
        "python-dateutil",
        "htmlgenerator",  # replacement for django templates
        "django-extensions",  # bunch of usefull management commands and functions
        "django-guardian",  # object level permissions
        "django-dynamic-preferences",  # easy handling of preferences
        "django-countries",
        "django-money[exchange]",
        "django-simple-history",
        "openpyxl",  # working with excel files
        "djangoql",
        # required for task scheduling
        "celery",
        "django-celery-results",
        "django-celery-beat",
        # required for search engine
        "celery-haystack-ng",
        "whoosh",
        # TODO: review whether we can or should remove these
        "WeasyPrint",  # creating PDFs
        "django-ckeditor",
    ],
    extras_require={"testing": ["hypothesis[django]"]},
    packages=find_packages(),
    setup_requires=["setuptools_scm"],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
