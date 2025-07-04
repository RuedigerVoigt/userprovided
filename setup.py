#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

from userprovided import _version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="userprovided",
    version=f"{_version.__version__}",
    author="Rüdiger Voigt",
    author_email="projects@ruediger-voigt.eu",
    description="A library to check user input for validity and / or plausibility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RuedigerVoigt/userprovided",
    package_data={"userprovided": ["py.typed"]},
    packages=setuptools.find_packages(),
    python_requires=">=3.9",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Utilities",
        "Topic :: Software Development :: Quality Assurance"
    ],
)
