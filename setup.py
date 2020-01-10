#!/usr/bin/env python

import setuptools

with open("README.md", "r") as rf:
    long_description = rf.read()

setuptools.setup(
    name="chord_lib",
    version="0.1.0",

    python_requires=">=3.6",
    install_requires=["jsonschema>=3.1.1,<4", "psycopg2-binary>=2.7,<3.0", "redis>=3.3,<4.0", "Werkzeug>=0.16.0,<1.0"],
    extras_require={
        "flask": ["Flask>=1.1,<2.0"],
        "django": ["Django>=2.2,<3.0", "djangorestframework>=3.10,<3.11"]
    },

    author="David Lougheed",
    author_email="david.lougheed@mail.mcgill.ca",

    description="A set of common utilities and helpers for CHORD.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),
    include_package_data=True,

    url="TODO",
    license="LGPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
