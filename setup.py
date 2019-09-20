#!/usr/bin/env python

import setuptools

from chord_lib import __version__

with open("README.md", "r") as rf:
    long_description = rf.read()

setuptools.setup(
    name="chord_lib",
    version=__version__,

    python_requires=">=3.6",
    install_requires=["Werkzeug>=0.16.0,<1.0"],

    author="David Lougheed",
    author_email="david.lougheed@mail.mcgill.ca",

    description="A set of common utilities and helpers for CHORD.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=["chord_lib"],
    include_package_data=True,

    url="TODO",
    license="LGPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
