from setuptools import find_packages, setup


def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="bread",
    version="0.1",
    description="basx Browse-Read-Edit-Add-Delete engine for django, reworked version",
    long_description=readme(),
    url="https://basx.dev",
    author="basx Software Development Co., Ltd.",
    author_email="info@basx.dev",
    license="Private",
    install_requires=[
        "Django",
        "django-filepreview",
        "django-ckeditor",
        "django-model-utils",
        "django-extensions",
        "django-filter",
        "django-guardian",
        "django-dynamic-preferences",
        "django-compressor",
        "django-libsass",
        "django-markdown2",
        "django-countries",
        "django-money[exchange]",
        "pygraphviz",
        "Pillow",
        "sorl-thumbnail",
        "openpyxl",
        "WeasyPrint",
        "ffmpeg-python",
    ],
    extras_require={"postgresql": ["psycopg2"]},
    setup_requires=["setuptools_scm"],
    use_scm_version={"write_to": "bread/version.py"},
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)
