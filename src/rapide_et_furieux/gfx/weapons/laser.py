#!/usr/bin/env python3

import logging
import time

import pygame

from . import common
from .. import RelativeSprite
from ... import assets


logger = logging.getLogger(__name__)


class Laser(RelativeSprite):
    def __init__(self, color, position, angle):
        if color in assets.LASERS:
            laser = assets.LASERS[color]
        else:
            laser = assets.LASERS[(0, 0, 255)]
        super().__init__(laser)


class ForwardLaserGun(common.Weapon):
    category = common.CATEGORY_GUNS
    MIN_FIRE_INTERVAL = 0.5

    def __init__(self, generator, race_track, car):
        super().__init__(generator, car)
        self.race_track = race_track
        self.car.extra_drawers.add(self)
        self.turret_base = assets.load_image(assets.TURRET_BASE)
        self.turret = assets.load_image(assets.GUN_LASER)
        self.turret = pygame.transform.rotate(self.turret, 180)

    def draw(self, screen, car):
        turret_base = self.turret_base
        turret_base_size = turret_base.get_size()

        turret = self.turret
        turret = pygame.transform.rotate(turret, -car.angle)
        turret_size = turret.get_size()

        car_parent_abs = car.parent.absolute
        car_position = car.position

        for (size, el) in [
                    (turret_base_size, turret_base),
                    (turret_size, turret)
                ]:
            screen.blit(
                el,
                (
                    car_parent_abs[0] + car_position[0] - (size[0] / 2),
                    car_parent_abs[1] + car_position[1] - (size[1] / 2),
                )
            )

    def deactivate(self):
        self.car.extra_drawers.remove(self)

    def fire(self):
        if not super().fire():
            return
        print("PWEE")

    def __hash__(self):
        return hash(self.car) ^ hash("forwardlasergun")


class ForwardLaserGenerator(object):
    category = common.CATEGORY_GUNS

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
        return isinstance(o, ForwardLaserGenerator)


class AutomaticLaserGenerator(object):
    def __init__(self):
        self.image = assets.load_image(assets.LASERS[(255, 0, 0)])
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, car):
        # TODO
        return

    def __str__(self):
        return "Targeted laser"

    def __hash__(self):
        return hash("automaticlasergun")

    def __eq__(self, o):
        return isinstance(o, AutomaticLaserGenerator)
