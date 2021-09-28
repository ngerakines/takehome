#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = []

test_requirements = [
    "pytest>=3",
]

setup(
    author="Nick Gerakines",
    author_email="nick.gerakines@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    description="A take-home test.",
    entry_points={
        "console_scripts": [
            "takehome=takehome.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="takehome",
    name="takehome",
    packages=find_packages(include=["takehome", "takehome.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ngerakines/takehome",
    version="0.1.0",
    zip_safe=False,
)
