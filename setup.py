#!/usr/bin/env python

import configparser
import os
import setuptools

with open("README.md", "r") as rf:
    long_description = rf.read()

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), "chord_lib", "package.cfg"))

setuptools.setup(
    name=config["package"]["name"],
    version=config["package"]["version"],

    python_requires=">=3.6",
    install_requires=[
        "jsonschema>=3.2.0,<4",
        "psycopg2-binary>=2.8.5,<3.0",
        "redis>=3.5.1,<4.0",
        "Werkzeug>=1.0.1,<2.0",
    ],
    extras_require={
        "flask": ["Flask>=1.1.2,<2.0"],
        "django": ["Django>=2.2.12,<3.0", "djangorestframework>=3.11,<3.12"]
    },

    author=config["package"]["authors"],
    author_email=config["package"]["author_emails"],

    description="A set of common utilities and helpers for CHORD.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),
    include_package_data=True,

    url="https://github.com/c3g/chord_lib",
    license="LGPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent"
    ]
)
