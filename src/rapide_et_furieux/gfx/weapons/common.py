import logging
import math
import random
import time

import pygame

from . import common
from .. import RelativeSprite
from ... import assets
from ... import util


logger = logging.getLogger(__name__)

CATEGORY_GUNS = 0  # straight forward only
CATEGORY_GUIDED = 1  # guided
CATEGORY_COUNTER_MEASURES = 2  # backward only
NB_CATEGORIES = 3

CATEGORY_NAMES = {
    CATEGORY_GUNS: 'Guns',
    CATEGORY_GUIDED: 'Smart weapons',
    CATEGORY_COUNTER_MEASURES: 'Counter-measures',
}


EXPLOSION_SIZES = [20, 64, 128, assets.TILE_SIZE[0]]
EXPLOSION_SURFACES = {}  # size --> list of list of surfaces


def load_explosions():
    global EXPLOSION_SURFACES

    EXPLOSION_SURFACES = {}
    for size in EXPLOSION_SIZES:
        EXPLOSION_SURFACES[size] = []
        for imgs in assets.EXPLOSIONS:
            # first image give us the reference size
            src_imgs = [assets.load_image(img) for img in imgs]
            src_size = src_imgs[0].get_size()
            ratio = max(
                src_size[0] / size,
                src_size[1] / size,
            )
            dst_size = (
                src_size[0] / ratio,
                src_size[1] / ratio,
            )

            dst_imgs = []
            for src_img in src_imgs:
                img = pygame.transform.scale(
                    src_img,
                    (
                        int(src_img.get_size()[0] / ratio),
                        int(src_img.get_size()[1] / ratio),
                    )
                )
                dst_img = pygame.Surface(dst_size, pygame.SRCALPHA)
                dst_img.blit(
                    img,
                    (
                        int((dst_size[0] - img.get_size()[0]) / 2),
                        int((dst_size[1] - img.get_size()[0]) / 2),
                    )
                )
                dst_imgs.append(dst_img)
            EXPLOSION_SURFACES[size].append(dst_imgs)


class Explosion(object):
    def __init__(self, race_track, position, size, anim_length):
        self.frames = random.choice(EXPLOSION_SURFACES[size])
        self.parent = race_track
        self.relative = (position[0] - (size / 2), position[1] - (size / 2))
        self.anim_length = anim_length
        self.t = 0
        util.register_drawer(assets.WEAPONS_LAYER, self)
        util.register_animator(self.anim)

    def disappear(self):
        util.unregister_drawer(self)
        util.unregister_animator(self.anim)

    def anim(self, frame_interval):
        self.t += frame_interval
        if self.t > self.anim_length:
            self.disappear()

    @property
    def absolute(self):
        p = self.parent.absolute
        return (
            p[0] + self.relative[0],
            p[1] + self.relative[1],
        )

    def draw(self, screen):
        frame_idx = int(len(self.frames) * self.t / self.anim_length)
        screen.blit(
            self.frames[frame_idx],
            self.absolute
        )


class Projectile(RelativeSprite):
    SPEED = assets.TILE_SIZE[0] * 20
    CONTACT_DISTANCE_SQ = (
        (assets.TILE_SIZE[0] / 2) *
        assets.CAR_SCALE_FACTOR
    ) ** 2
    DAMAGE = 25
    GRID_MARGE = 10
    EXPLOSION_SIZE = 20
    EXPLOSION_TIME = 0.5
    EXPLOSION_DAMAGE = 0
    ASSETS = None
    DEFAULT_ASSET = None
    SIZE_FACTOR = 1.0

    def __init__(self, race_track, shooter):
        self.shooter = shooter
        self.explosion_range_sq = (self.EXPLOSION_SIZE / 2) ** 2

        color = self.shooter.color
        if color in self.ASSETS:
            projectile = self.ASSETS[color]
        else:
            projectile = self.DEFAULT_ASSET
        super().__init__(projectile)
        if self.SIZE_FACTOR != 1.0:
            self.image = pygame.transform.scale(
                self.image, (
                    int(self.size[0] * self.SIZE_FACTOR),
                    int(self.size[1] * self.SIZE_FACTOR),
                )
            )

        angle = shooter.angle
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
            self.relative[0] + ((assets.TILE_SIZE[0] / 8) * cos),
            self.relative[1] + ((assets.TILE_SIZE[1] / 8) * sin),
        )

        util.register_drawer(assets.WEAPONS_LAYER, self)
        util.register_animator(self.move)

        # relative to the race_track
        self.speed = (
            self.SPEED * cos,
            self.SPEED * sin,
        )
        self.radians = 0  # to make collide() happy

        # TODO(Jflesch): very approximative ...
        self._pts = (
            (0, 0),
            self.image.get_size()
        )

        self.max_speed_sq = (
            ((self.image.get_size()[0] * 1.5) ** 2) +
            ((self.image.get_size()[1] * 1.5) ** 2)
        )
        self.max_speed = math.sqrt(self.max_speed_sq)

    def disappear(self):
        util.unregister_drawer(self)
        util.unregister_animator(self.move)

    @property
    def position(self):
        return (
            self.relative[0] + (self.size[0] / 2),
            self.relative[1] + (self.size[1] / 2),
        )

    @property
    def pts(self):
        relative = self.relative
        return [
            (
                relative[0] + self._pts[0][0],
                relative[1] + self._pts[0][1],
            ),
            (
                relative[0] + self._pts[1][0],
                relative[1] + self._pts[1][1],
            ),
        ]

    def move(self, frame_interval):
        speed = (self.speed[0] * frame_interval, self.speed[1] * frame_interval)
        speed_sq = (speed[0] ** 2) + (speed[1] ** 2)
        if speed_sq > self.max_speed_sq:
            ratio = math.sqrt(speed_sq) / self.max_speed
            speed = (speed[0] / ratio, speed[1] / ratio)

        self.relative = (
            int(self.relative[0] + speed[0]),
            int(self.relative[1] + speed[1]),
        )
        position = self.position

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

        collisions = self.parent.collisions.get_collisions(self)
        collisions = [
            collision for collision in collisions
            if collision.obstacle is not self.shooter
        ]
        if len(collisions) <= 0:
            return

        self.disappear()
        common.Explosion(self.parent, position,
                         self.EXPLOSION_SIZE,
                         self.EXPLOSION_TIME)

        target = collisions[0].obstacle
        if hasattr(target, 'health'):
            target.health -= self.DAMAGE
            logger.info("Hit: {} ; health: {}".format(target, target.health))

        if self.EXPLOSION_DAMAGE > 0:
            self.parent.collisions.collide(
                self, collisions, frame_interval
            )
            for car in self.parent.cars:
                dist = util.distance_sq_pt_to_pt(car.position, position)
                if dist < self.explosion_range_sq:
                    car.health -= self.EXPLOSION_DAMAGE
                    logger.info("Hit: {} ; health: {}".format(car, car.health))


class Weapon(object):
    MIN_FIRE_INTERVAL = 0.5

    def __init__(self, generator, car):
        self.parent = generator
        self.car = car
        self.car.weapon = self
        self.last_shot = 0

    def deactivate(self):
        pass

    def fire(self):
        n = time.time()
        if n - self.last_shot <= self.MIN_FIRE_INTERVAL:
            return False
        self.last_shot = n
        return True


class StaticTurret(Weapon):
    MIN_FIRE_INTERVAL = 0.2
    TURRET_ANGLE = 180

    def __init__(self, generator, car, turret_rsc):
        super().__init__(generator, car)
        self.car.extra_drawers.add(self)
        self.turret_base = assets.load_image(assets.TURRET_BASE)
        self.turret = assets.load_image(turret_rsc)
        self.turret = pygame.transform.rotate(self.turret, self.TURRET_ANGLE)

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
