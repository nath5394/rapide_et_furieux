#!/usr/bin/env python3

import pygame

from . import common
from ... import assets


class ShieldGun(common.Weapon):
    SHIELD_TIME_LENGTH = 15
    SHIELD_HEALTH = 150
    MIN_FIRE_INTERVAL = SHIELD_TIME_LENGTH
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self, generator, race_track, shooter):
        self.race_track = race_track
        super().__init__(generator, shooter)

    def fire(self):
        if not super().fire():
            return False
        self.shooter.shield = (self.SHIELD_TIME_LENGTH, self.SHIELD_HEALTH)
        return True

    def __hash__(self):
        return hash("shield")


class ShieldGenerator(object):
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self):
        self.image = assets.load_image(assets.SHIELD)
        img_size = self.image.get_size()
        ratio = max(
            img_size[0] / 32,
            img_size[1] / 32,
        )
        img_size = (int(img_size[0] / ratio), int(img_size[1] / ratio))
        self.image = pygame.transform.scale(self.image, img_size)

    def activate(self, race_track, shooter):
        return ShieldGun(self, race_track, shooter)

    def __str__(self):
        return "Shield"

    def __hash__(self):
        return hash("shield")

    def __eq__(self, o):
        return isinstance(o, ShieldGenerator)
