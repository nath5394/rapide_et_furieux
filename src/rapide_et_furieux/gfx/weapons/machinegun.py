#!/usr/bin/env python3

import logging
import math

import pygame

from . import common
from .. import RelativeSprite
from ... import assets
from ... import util


logger = logging.getLogger(__name__)


class GunFire(RelativeSprite):
    TIME_VISIBLE = 0.3

    def __init__(self, race_track, line, color):
        self.race_track = race_track
        self.line = line
        self.color = color
        self.t = 0
        util.register_drawer(assets.WEAPONS_LAYER, self)
        util.register_animator(self.anim)

    def draw(self, screen):
        absolute = self.race_track.absolute
        r = 128 * self.t / self.TIME_VISIBLE
        color = (
            max(r, self.color[0]),
            max(r, self.color[1]),
            max(r, self.color[2]),
        )
        pygame.draw.line(
            screen, color,
            (
                absolute[0] + self.line[0][0],
                absolute[1] + self.line[0][1],
            ),
            (
                absolute[0] + self.line[1][0],
                absolute[1] + self.line[1][1],
            ),
        )

    def anim(self, frame_interval):
        self.t += frame_interval
        if self.t < self.TIME_VISIBLE:
            return
        util.unregister_drawer(self)
        util.unregister_animator(self.anim)


class MachineGun(common.AutomaticTurret):
    category = common.CATEGORY_GUIDED
    MIN_FIRE_INTERVAL = 0.02
    TURRET_ANGLE = 180
    DAMAGE = 5
    EXPLOSION_SIZE = 20
    EXPLOSION_TIME = 0.5

    def __init__(self, generator, race_track, shooter):
        super().__init__(generator, race_track, shooter, assets.GUN_MACHINEGUN)
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
        radians = (self.angle - 90) * math.pi / 180
        position = self.shooter.position

        line = (
            position,
            (
                position[0] + (self.max_length * math.cos(radians)),
                position[1] + (self.max_length * math.sin(radians)),
            ),
        )

        # find where the shoots ends
        obstacles = self.race_track.collisions.get_obstacles_on_segment(line)
        closest = (0xFFFFFFFF, None, None)
        for (obstacle, collision_pt) in obstacles:
            if obstacle is self.shooter:
                continue
            dist = util.distance_sq_pt_to_pt(position, collision_pt)
            if dist < closest[0]:
                closest = (dist, obstacle, collision_pt)

        if closest[1] is not None:
            target = closest[1]
            line = (position, closest[2])
            common.Explosion(
                self.race_track, closest[2],
                self.EXPLOSION_SIZE, self.EXPLOSION_TIME
            )
            if hasattr(target, 'damage'):
                target.damage(self.DAMAGE)

        GunFire(self.race_track, line, self.shooter.color)
        return True

    def __hash__(self):
        return hash(self.shooter) ^ hash("machinegun")


class MachineGunGenerator(object):
    category = common.CATEGORY_GUIDED

    def __init__(self):
        self.image = assets.load_image(assets.BULLET)
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, shooter):
        return MachineGun(self, race_track, shooter)

    def __str__(self):
        return "Machine gun"

    def __hash__(self):
        return hash("machinegun")

    def __eq__(self, o):
        return isinstance(o, MachineGunGenerator)
