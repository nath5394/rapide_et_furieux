#!/usr/bin/env python3

from . import common
from ... import assets


class GuidedMissile(object):
    category = common.CATEGORY_GUIDED

    def __init__(self):
        self.image = assets.load_image(assets.MISSILE)

    def activate(self, race_track, car):
        # TODO
        return None

    def __str__(self):
        return "Missile"

    def __hash__(self):
        return hash("missile")

    def __eq__(self, o):
        return isinstance(o, GuidedMissile)
