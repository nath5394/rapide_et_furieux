#!/usr/bin/env python3

import logging
import math

import pygame

from . import common
from .. import RelativeSprite
from ... import assets
from ... import util


logger = logging.getLogger(__name__)


class Laser(RelativeSprite):
    SPEED = assets.TILE_SIZE[0] * 10
    CONTACT_DISTANCE_SQ = (
        (assets.TILE_SIZE[0] / 2) *
        assets.CAR_SCALE_FACTOR
    ) ** 2
    DAMAGE = 50
    GRID_MARGE = 10
    EXPLOSION_SIZE = (20, 20)
    EXPLOSION_TIME = 0.5

    def __init__(self, race_track, shooter, position, angle):
        self.shooter = shooter

        color = self.shooter.color
        if color in assets.LASERS:
            laser = assets.LASERS[color]
        else:
            laser = assets.LASERS[(0, 0, 255)]
        super().__init__(laser)

        self.image = pygame.transform.rotate(self.image, -angle)
        self.size = self.image.get_size()
        self.parent = race_track
        self.relative = (
            shooter.position[0] - (self.size[0] / 2),
            shooter.position[1] - (self.size[1] / 2),
        )

        angle -= 90
        angle *= math.pi / 180
        (cos, sin) = (math.cos(angle), math.sin(angle))
        self.relative = (
            self.relative[0] + (assets.TILE_SIZE[0] * cos),
            self.relative[1] + (assets.TILE_SIZE[1] * sin),
        )

        util.register_drawer(assets.WEAPONS_LAYER, self)
        util.register_animator(self.move)

        # relative to the race_track
        self.speed = (
            self.SPEED * cos,
            self.SPEED * sin,
        )

    def disappear(self):
        util.unregister_drawer(self)
        util.unregister_animator(self.move)

    def move(self, frame_interval):
        self.relative = (
            self.relative[0] + (self.speed[0] * frame_interval),
            self.relative[1] + (self.speed[1] * frame_interval),
        )
        position = (
            self.relative[0] + (self.size[0] / 2),
            self.relative[1] + (self.size[1] / 2),
        )

        # are we still in the game ?
        grid_pos = (
            position[0] / assets.TILE_SIZE[0],
            position[1] / assets.TILE_SIZE[1],
        )
        grid_min = self.parent.tiles.grid_min
        grid_min = (
            grid_min[0] - self.GRID_MARGE,
            grid_min[1] - self.GRID_MARGE,
        )
        grid_max = self.parent.tiles.grid_max
        grid_max = (
            grid_max[0] + self.GRID_MARGE,
            grid_max[1] + self.GRID_MARGE,
        )
        if (grid_pos[0] < grid_min[0] or grid_pos[1] < grid_min[1] or
                grid_pos[0] > grid_max[0] or grid_pos[1] > grid_max[1]):
            self.disappear()
            return

        for car in self.parent.cars:
            if car is self.shooter:
                continue
            # TODO(Jflesch): Improve collision detection
            dist = util.distance_sq_pt_to_pt(car.position, position)
            if dist < self.CONTACT_DISTANCE_SQ:
                break
        else:
            return

        self.disappear()
        common.Explosion(self.parent, position,
                         self.EXPLOSION_SIZE,
                         self.EXPLOSION_TIME)
        car.health -= self.DAMAGE
        logger.info("Target health: {}".format(car.health))


class ForwardLaserGun(common.Weapon):
    category = common.CATEGORY_GUNS
    MIN_FIRE_INTERVAL = 0.2

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
            return False
        Laser(self.race_track, self.car,
              self.car.position, self.car.angle)
        return True

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
