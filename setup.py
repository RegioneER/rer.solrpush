# -*- coding: utf-8 -*-
"""Installer for the rer.solrpush package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="rer.solrpush",
    version="1.6.6.dev0",
    description="Prodotto per Regione Emilia-Romagna relativo all'indicizzazione dei contenuti con solr",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone",
    author="RedTurtle",
    author_email="sviluppoplone@redturtle.it",
    url="https://github.com/collective/rer.solrpush",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/rer.solrpush",
        "Source": "https://github.com/collective/rer.solrpush",
        "Tracker": "https://github.com/collective/rer.solrpush/issues",
        # 'Documentation': 'https://rer.solrpush.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["rer"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        "setuptools",
        "collective.z3cform.jsonwidget",
        "plone.api>=1.8.4",
        "pysolr",
        'ftfy==4.4.3;python_version<="2.7"',
        "plone.restapi>=8.13.0",
        "z3c.jbot",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing>=5.0.0",
            "plone.app.contenttypes",
            "plone.app.robotframework[debug]",
            "collective.MockMailHost",
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = rer.solrpush.locales.update:update_locale
    """,
)
