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
    name="bread",
    version=version,
    description="Engine to create database applications based on Django and the IBM Carbon Design System",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/basxsoftwareassociation/bread",
    author="basx Software Association",
    author_email="sam@basx.dev",
    license="New BSD License",
    install_requires=[
        "Django",
        "python-dateutil",
        "django-crispy-forms",
        "django-filepreview @ hg+https://hg.basx.dev/pythonpackages/django-filepreview",
        "django-ckeditor",
        "django-model-utils",
        "django-extensions",
        "django-filter",
        "django-guardian",
        "django-dynamic-preferences",
        "django-dynamic-fixture",
        "django-compressor",
        "django-libsass",
        "django-markdown2",
        "django-countries",
        "django-money[exchange]",
        "Arpeggio",
        "htmlgenerator",
        # Required for multimedia
        "pygraphviz",  # graphviz/dot graphs
        "Pillow",  # image processing
        "easy_thumbnails",  # thumbnails
        "django-image-cropping",  # cropping
        "openpyxl",  # working with excel files
        "WeasyPrint",  # creating PDFs
        "ffmpeg-python",  # working with ffmpeg for video and audio
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
