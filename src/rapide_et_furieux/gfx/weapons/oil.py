#!/usr/bin/env python3

import random

import pygame

from . import common
from .. import RelativeSprite
from ... import assets
from ... import util


class Oil(RelativeSprite):
    CONTACT_DISTANCE_SQ = (
        (assets.TILE_SIZE[0] / 2) *
        assets.CAR_SCALE_FACTOR
    ) ** 2
    ASSET = assets.OIL
    OILY_TIME = 3.0
    LIFE_LENGTH = 15

    def __init__(self, race_track, shooter):
        super().__init__(self.ASSET)

        self.angle = random.randint(0, 360)
        self.image = pygame.transform.scale(self.image, (
            int(self.image.get_size()[0] * 0.75),
            int(self.image.get_size()[1] * 0.75),
        ))
        self.image = pygame.transform.rotate(self.image, self.angle)
        self.size = self.image.get_size()

        self.parent = race_track
        self.shooter = shooter
        self.position = shooter.position
        self.relative = (
            shooter.position[0] - (self.size[0] / 2),
            shooter.position[1] - (self.size[1] / 2),
        )
        self.shooter = shooter
        self.time_remaining = self.LIFE_LENGTH
        util.register_drawer(assets.WEAPONS_LAYER, self)
        util.register_animator(self.anim)

    def disappear(self):
        util.unregister_drawer(self)
        util.unregister_animator(self.anim)

    def anim(self, frame_interval):
        self.time_remaining -= frame_interval
        if self.time_remaining <= 0:
            self.disappear()
            return
        for car in self.parent.cars:
            if car is self.shooter:
                continue
            dist = util.distance_sq_pt_to_pt(self.position, car.position)
            if dist < self.CONTACT_DISTANCE_SQ:
                car.oily = self.OILY_TIME


class OilGun(common.Weapon):
    MIN_FIRE_INTERVAL = 1.0
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self, generator, race_track, shooter):
        self.race_track = race_track
        super().__init__(generator, shooter)

    def fire(self):
        if not super().fire():
            return False
        Oil(self.race_track, self.shooter)
        return True

    def __hash__(self):
        return hash("oil")


class OilGenerator(object):
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self):
        self.image = assets.load_image(assets.OIL)
        img_size = self.image.get_size()
        ratio = max(
            img_size[0] / 32,
            img_size[1] / 32,
        )
        img_size = (int(img_size[0] / ratio), int(img_size[1] / ratio))
        self.image = pygame.transform.scale(self.image, img_size)

    def activate(self, race_track, shooter):
        return OilGun(self, race_track, shooter)

    def __str__(self):
        return "Oil spill"

    def __hash__(self):
        return hash("oil")

    def __eq__(self, o):
        return isinstance(o, OilGenerator)
