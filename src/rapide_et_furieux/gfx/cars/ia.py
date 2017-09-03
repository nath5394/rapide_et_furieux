#!/usr/bin/env

from . import Car


class IACar(Car):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
