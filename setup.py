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
        # custom code in other packages
        "htmlgenerator",  # replacement for django templates
        # core dependencies
        "Django",
        "python-dateutil",
        "django-compressor",  # compress html assets
        "django-libsass",  # serve *.scss files with compressor
        "django-crispy-forms",  # TODO: remove this dependency
        "django-extensions",  # bunch of usefull management commands and functions
        "django-filter",  # url-based filtering, filter-forms
        "django-guardian",  # object level permissions
        # other dependencies, TODO: remove unnecessary ones
        "django-ckeditor",
        "django-model-utils",
        "django-dynamic-preferences",  # easy handling of preferences
        "django-dynamic-fixture",
        "django-markdown2",
        "django-countries",
        "django-money[exchange]",
        "Arpeggio",  # used to create strong parsers
        "django-simple-history",
        "django-clone",
        # Required for multimedia
        "Pillow",  # image processing
        "easy_thumbnails",  # thumbnails
        "django-image-cropping",  # cropping images, only usefull in admin backend
        "openpyxl",  # working with excel files
        "WeasyPrint",  # creating PDFs
        # required for task scheduling
        "celery <5.0,>=4.4",
        "django-celery-results",
        "django-celery-beat",
        # required for search engine
        "django-haystack",
        "whoosh",
        "celery-haystack",
    ],
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
