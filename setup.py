#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="userprovided",
    version="0.7.4",
    author="Rüdiger Voigt",
    author_email="projects@ruediger-voigt.eu",
    description="A library to check user input for validity and / or plausibility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RuedigerVoigt/userprovided",
    package_data={"userprovided": ["py.typed"]},
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Utilities",
        "Topic :: Software Development :: Quality Assurance"
    ],
)
