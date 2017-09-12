#!/usr/bin/env python3

import pygame

from . import common
from ... import assets


class Mine(common.Projectile):
    SPEED = 0
    CONTACT_DISTANCE_SQ = (
        (assets.TILE_SIZE[0] / 2) *
        assets.CAR_SCALE_FACTOR
    ) ** 2
    DAMAGE = 100
    GRID_MARGE = 10
    EXPLOSION_SIZE = 128
    EXPLOSION_TIME = 1
    EXPLOSION_DAMAGE = 50
    ASSETS = None
    DEFAULT_ASSET = assets.MINE
    ASSET_ANGLE = 0
    SIZE_FACTOR = 1.0


class MineGun(common.Weapon):
    MIN_FIRE_INTERVAL = 0.2
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self, generator, race_track, shooter):
        self.race_track = race_track
        super().__init__(generator, shooter)

    def fire(self):
        if not super().fire():
            return False
        Mine(self.race_track, self.shooter, self.shooter.angle)
        return True

    def __hash__(self):
        return hash("mine")


class MineGenerator(object):
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self):
        self.image = assets.load_image(assets.MINE)
        img_size = self.image.get_size()
        ratio = max(
            img_size[0] / 32,
            img_size[1] / 32,
        )
        img_size = (int(img_size[0] / ratio), int(img_size[1] / ratio))
        self.image = pygame.transform.scale(self.image, img_size)

    def activate(self, race_track, shooter):
        return MineGun(self, race_track, shooter)

    def __str__(self):
        return "Mine"

    def __hash__(self):
        return hash("mine")

    def __eq__(self, o):
        return isinstance(o, MineGenerator)
