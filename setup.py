#!/usr/bin/env python

import configparser
import os
import setuptools

with open("README.md", "r") as rf:
    long_description = rf.read()

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bento_lib", "package.cfg"))

setuptools.setup(
    name=config["package"]["name"],
    version=config["package"]["version"],

    python_requires=">=3.8.1",
    install_requires=[
        "aiohttp>=3.8.4,<4",
        "jsonschema>=4.17.3,<5",
        "psycopg2-binary>=2.9.5,<3.0",
        "redis>=4.5.1,<5.0",
        "requests>=2.28.1,<3",
        "Werkzeug>=2.2.3,<3",
    ],
    extras_require={
        "flask": ["Flask>=2.2.3,<3"],
        "django": ["Django>=4.1.7,<5", "djangorestframework>=3.14.0,<3.15"],
        "quart": ["quart>=0.18.3,<0.19"],
    },

    author=config["package"]["authors"],
    author_email=config["package"]["author_emails"],

    description="A set of common utilities and helpers for Bento platform services.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_namespace_packages(),
    include_package_data=True,

    url="https://github.com/bento-platform/bento_lib",
    license="LGPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent"
    ]
)
