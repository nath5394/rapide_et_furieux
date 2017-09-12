#!/usr/bin/env python3

import math

import pygame

from . import common
from ... import assets
from ... import util


class Missile(common.Projectile):
    SPEED = assets.TILE_SIZE[0] * 7.5
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
    DEFAULT_ASSET = assets.MISSILE
    ASSET_ANGLE = 0
    SIZE_FACTOR = 0.75
    MAX_TURN_SPEED = math.pi * 4

    def __init__(self, target, *args, **kwargs):
        self.target = target
        super().__init__(*args, **kwargs)

    def compute_turn(self, frame_interval):
        self.size = self.image.get_size()
        position = (
            self.relative[0] + (self.size[0] / 2),
            self.relative[1] + (self.size[1] / 2),
        )
        target_angle = math.atan2(
            self.target.position[1] - position[1],
            self.target.position[0] - position[0],
        )
        self.radians %= 2 * math.pi
        target_angle %= 2 * math.pi

        if self.radians == target_angle:
            return 0

        diff = self.radians - target_angle
        diff %= math.pi * 2
        diff -= math.pi
        if diff < 0:
            diff = max(diff, -self.MAX_TURN_SPEED)
        else:
            diff = min(diff, self.MAX_TURN_SPEED)
        diff *= frame_interval

        return diff

    def update_image(self):
        position = (
            self.relative[0] + (self.size[0] / 2),
            self.relative[1] + (self.size[1] / 2),
        )
        # The gfx are oriented to the up side, but radians=0 == right
        self.angle = self.radians * 180 / math.pi
        self.image = pygame.transform.rotate(self.original, -self.angle)
        self.size = self.image.get_size()
        self.relative = (
            int(position[0]) - (self.size[0] / 2),
            int(position[1]) - (self.size[1] / 2),
        )

    def apply_turn(self, angle_change):
        self.radians = self.radians + angle_change
        self.radians %= 2 * math.pi
        self.update_image()
        self.recompute_pts()

        # missile turns, so does its speed momentum
        speed = util.to_polar(self.speed)
        speed = (speed[0], speed[1] + angle_change)
        self.speed = util.to_cartesian(speed)
        return angle_change

    def turn(self, frame_interval):
        t = self.compute_turn(frame_interval)
        self.apply_turn(t)


class MissileGun(common.AutomaticTurret):
    category = common.CATEGORY_GUIDED
    MIN_FIRE_INTERVAL = 1.0
    TURRET_ANGLE = 0

    def __init__(self, generator, race_track, shooter):
        super().__init__(generator, race_track, shooter, assets.GUN_MISSILE)
        self.race_track = race_track

        # make sure to cross the whole race track
        self.max_length = util.distance_pt_to_pt(
            (
                race_track.tiles.grid_min[0] * assets.TILE_SIZE[0],
                race_track.tiles.grid_min[1] * assets.TILE_SIZE[1],
            ),
            (
                (race_track.tiles.grid_max[0] + 1) * assets.TILE_SIZE[0],
                (race_track.tiles.grid_max[1] + 1) * assets.TILE_SIZE[1],
            ),
        )

    def fire(self):
        if not super().fire():
            return False
        if self.target is None:
            return False
        Missile(self.target, self.race_track, self.shooter, self.angle)
        return True

    def __hash__(self):
        return hash(self.shooter) ^ hash("missilegun")


class GuidedMissileGenerator(object):
    category = common.CATEGORY_GUIDED

    def __init__(self):
        self.image = assets.load_image(assets.MISSILE)

    def activate(self, race_track, shooter):
        return MissileGun(self, race_track, shooter)

    def __str__(self):
        return "Missile"

    def __hash__(self):
        return hash("missile")

    def __eq__(self, o):
        return isinstance(o, GuidedMissileGenerator)
