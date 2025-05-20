#!/usr/bin/env python3
"""
Meet2Notes setup script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="meet2notes",
    version="0.1.0",
    author="Meet2Notes Team",
    description="Convert meeting recordings to transcripts and summarized notes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MartinMcCurley/meet2notes",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "meet2notes=src.run:main",
        ],
    },
) 