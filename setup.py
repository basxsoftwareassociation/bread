from setuptools import find_packages, setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="bread",
    version="0.1",
    description="basx Browse-Read-Edit-Add-Delete engine for django",
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
        "pygraphviz",
        "Pillow",
        "easy_thumbnails",
        "django-image-cropping",
        "openpyxl",
        "WeasyPrint",
        "ffmpeg-python",
        "celery <5.0,>=4.4",
        "django-celery-results",
        "django-celery-beat",
        "Arpeggio",
        "htmlgenerator",
    ],
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
    ],
)
