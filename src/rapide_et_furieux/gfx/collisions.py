#!/usr/bin/env python3

import itertools


class CollisionObject(object):
    def __init__(self, *args, **kwargs):
        self.pts = []  # array of (x, y)

        # following attributes aren't really used on static objects
        # they are just here so the algorithms stay the same
        # for everything
        self.radians = 0  # radians = 0 : object is turned to the right
        self.position = (0, 0)  # center

        # speed relative to the object, not the track !
        self.speed = (0, 0)

    def update_image(self):
        assert False, "subclass must implement update_image()"


class CollisionHandler(object):
    def __init__(self, racetrack, game_settings):
        self.game_settings = game_settings
        self.static = [racetrack.borders]
        self.moving = [racetrack.cars]

    def check(self, moving):
        """
        check() must be called before the next movement of the car.
        It will cancel/reverse part of its speed if required
        """
        for obstacle in itertools.chain.from_iterable(
                    [self.static, self.moving]
                ):
            pass
