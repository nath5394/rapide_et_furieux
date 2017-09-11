#!/usr/bin/env python3

import logging

import pygame

from . import common
from ... import assets


logger = logging.getLogger(__name__)


class Laser(common.Projectile):
    SPEED = assets.TILE_SIZE[0] * 20
    CONTACT_DISTANCE_SQ = (
        (assets.TILE_SIZE[0] / 2) *
        assets.CAR_SCALE_FACTOR
    ) ** 2
    DAMAGE = 25
    GRID_MARGE = 10
    EXPLOSION_SIZE = 20
    EXPLOSION_TIME = 0.5
    ASSETS = assets.LASERS
    DEFAULT_ASSET = assets.LASERS[(0, 0, 255)]


class ForwardLaserGun(common.StaticTurret):
    category = common.CATEGORY_GUNS
    MIN_FIRE_INTERVAL = 0.2
    TURRET_ANGLE = 0

    def __init__(self, generator, race_track, shooter):
        super().__init__(generator, shooter, assets.GUN_LASER)
        self.race_track = race_track

    def fire(self):
        if not super().fire():
            return False
        Laser(self.race_track, self.shooter, self.shooter.angle)
        return True

    def __hash__(self):
        return hash(self.shooter) ^ hash("forwardlasergun")


class ForwardLaserGenerator(object):
    category = common.CATEGORY_GUNS

    def __init__(self):
        self.image = assets.load_image(assets.LASERS[(0, 0, 255)])
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, shooter):
        return ForwardLaserGun(self, race_track, shooter)

    def __str__(self):
        return "Laser"

    def __hash__(self):
        return hash("forwardlasergun")

    def __eq__(self, o):
        return isinstance(o, ForwardLaserGenerator)


class AutomaticLaserGun(common.AutomaticTurret):
    category = common.CATEGORY_GUIDED
    MIN_FIRE_INTERVAL = 0.2
    TURRET_ANGLE = 0

    def __init__(self, generator, race_track, shooter):
        super().__init__(generator, race_track, shooter, assets.GUN_LASER)
        self.race_track = race_track

    def fire(self):
        if not super().fire():
            return False
        Laser(self.race_track, self.shooter, self.angle)
        return True

    def __hash__(self):
        return hash(self.shooter) ^ hash("automaticlasergun")


class AutomaticLaserGenerator(object):
    category = common.CATEGORY_GUIDED

    def __init__(self):
        self.image = assets.load_image(assets.LASERS[(255, 0, 0)])
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, shooter):
        return AutomaticLaserGun(self, race_track, shooter)

    def __str__(self):
        return "Targeted laser"

    def __hash__(self):
        return hash("automaticlasergun")

    def __eq__(self, o):
        return isinstance(o, AutomaticLaserGenerator)
