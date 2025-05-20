#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup  # pylint: disable=import-error
from setuptools import find_packages

setup(name="shiny-pancake",
		version="0.0.1",
		description="",
		packages=find_packages(),
		install_requires=[
            "beautifulsoup4>=4.13.3,<4.14.0",
            "PyYaml >= 6.0, < 7.0",
            "tkcalendar >= 1.6.1, < 2.0.0",
            "sqlalchemy >= 2.0.41, < 3.0.0",
            "alembic >= 1.15.2, < 2.0.0",
		],
		entry_points={
		},
		classifiers=[
				"Development Status :: 3 - Alpha",
				"Intended Audience :: Developers",
				"Operating System :: POSIX",
				"Programming Language :: Python :: 3.12.3",
		],
		)

# vim: tabstop=4 shiftwidth=4
