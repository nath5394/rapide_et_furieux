#!/usr/bin/env python3

from ... import assets


class GuidedMissile(object):
    def __init__(self):
        self.image = assets.load_image(assets.MISSILE)

    def activate(self, race_track, car):
        # TODO
        assert()

    def __str__(self):
        return "Missile"

    def __hash__(self):
        return hash("missile")

    def __eq__(self, o):
        return isinstance(o, GuidedMissile)
