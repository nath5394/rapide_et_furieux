#!/usr/bin/env python3

import pygame

from .. import RelativeSprite
from ... import assets


class Laser(RelativeSprite):
    def __init__(self, color, position, angle):
        if color in assets.LASERS:
            laser = assets.LASERS[color]
        else:
            laser = assets.LASERS[(0, 0, 255)]
        super().__init__(laser)


class ForwardLaserGun(object):
    def __init__(self, parent, race_track, car):
        self.race_track = race_track
        self.car = car
        self.parent = parent
        self.car.extra_drawers.add(self)

    def draw(self, screen):
        pass

    def deactivate(self):
        self.car.extra_drawers.remove(self)

    def fire(self):
        pass

    def __hash__(self):
        return hash(self.car) ^ hash("forwardlasergun")


class ForwardLaser(object):
    def __init__(self):
        self.image = assets.load_image(assets.LASERS[(0, 0, 255)])
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, car):
        return ForwardLaserGun(self, race_track, car)

    def __str__(self):
        return "Laser"

    def __hash__(self):
        return hash("forwardlasergun")

    def __eq__(self, o):
        return isinstance(o, ForwardLaser)


class AutomaticLaser(object):
    def __init__(self):
        self.image = assets.load_image(assets.LASERS[(255, 0, 0)])
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, car):
        # TODO
        assert()

    def __str__(self):
        return "Targeted laser"

    def __hash__(self):
        return hash("automaticlasergun")

    def __eq__(self, o):
        return isinstance(o, AutomaticLaser)
