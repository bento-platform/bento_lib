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

    python_requires=">=3.10.0",
    install_requires=[
        "aiohttp>=3.9.1,<4",
        "jsonschema>=4.20.0,<5",
        "psycopg2-binary>=2.9.9,<3.0",
        "pydantic>=2.5.2,<3",
        "pydantic_settings>=2.1.0,<3",
        "redis>=5.0.1,<6",
        "requests>=2.31.0,<3",
        "Werkzeug>=2.2.3,<4",
    ],
    extras_require={
        "asyncpg": ["asyncpg>=0.29.0,<0.30.0"],
        "flask": ["Flask>=2.2.5,<4"],
        "django": ["Django>=4.2.7,<5", "djangorestframework>=3.14.0,<3.15"],
        "fastapi": ["fastapi>=0.104,<0.106"],
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
