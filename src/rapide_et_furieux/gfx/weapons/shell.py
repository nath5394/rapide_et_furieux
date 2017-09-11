#!/usr/bin/env python3

import pygame

from . import common
from ... import assets


class TankShell(common.Projectile):
    SPEED = assets.TILE_SIZE[0] * 10
    CONTACT_DISTANCE_SQ = (
        (assets.TILE_SIZE[0] / 2) *
        assets.CAR_SCALE_FACTOR
    ) ** 2
    DAMAGE = 100
    GRID_MARGE = 10
    EXPLOSION_SIZE = 128
    EXPLOSION_TIME = 1
    EXPLOSION_DAMAGE = 50
    ASSETS = assets.BULLETS
    DEFAULT_ASSET = assets.BULLETS[(0, 0, 255)]
    SIZE_FACTOR = 1.5


class TankGun(common.StaticTurret):
    category = common.CATEGORY_GUNS
    MIN_FIRE_INTERVAL = 1.0

    def __init__(self, generator, race_track, shooter):
        super().__init__(generator, shooter, assets.GUN_TANKSHELL)
        self.race_track = race_track

    def fire(self):
        if not super().fire():
            return False
        TankShell(self.race_track, self.shooter, self.shooter.angle)
        return True

    def __hash__(self):
        return hash(self.shooter) ^ hash("tankgun")


class TankShellGenerator(object):
    category = common.CATEGORY_GUNS

    def __init__(self):
        self.image = assets.load_image(assets.BULLET)
        self.image = pygame.transform.rotate(self.image, -90)
        img_size = self.image.get_size()
        img_size = (img_size[0] * 2, img_size[1] * 2)
        self.image = pygame.transform.scale(self.image, img_size)

    def activate(self, race_track, shooter):
        return TankGun(self, race_track, shooter)

    def __str__(self):
        return "Tank shell"

    def __hash__(self):
        return hash("tankshell")

    def __eq__(self, o):
        return isinstance(o, TankShellGenerator)
