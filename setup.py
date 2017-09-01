#!/usr/bin/env python3

from setuptools import find_packages
from setuptools import setup


setup(
    name="rapide-et-furieux",
    # if you change the version, don't forget to:
    # * update the ChangeLog file
    # * update AUTHORS
    # * update src/rapide_et_furieux/util.py:VERSION
    version="0.1",
    description="Nasty 2D car racing game",
    long_description="2D car racing game with weapons",
    keywords="game",
    license="GPLv3+",
    author="Jerome Flesch",
    author_email="jflesch@kwain.net",
    install_requires=[
        "pygame",
    ],
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={
        '': 'src',
    },
    package_data={
    },
    entry_points={
        'gui_scripts': [
            'ref-editor = rapide_et_furieux.editor:main',
            'ref-game = rapide_et_furieux.game:main',
        ],
    }
)
