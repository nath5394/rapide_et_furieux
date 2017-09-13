import logging
import math
import random
import time

import pygame

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
        if frame_idx > len(self.frames):
            frame_idx = len(self.frames) - 1
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
    ASSET_ANGLE = 0
    SIZE_FACTOR = 1.0

    def __init__(self, race_track, shooter, angle):
        self.shooter = shooter
        self.explosion_range_sq = (self.EXPLOSION_SIZE / 2) ** 2

        color = self.shooter.color
        if self.ASSETS is not None and color in self.ASSETS:
            projectile = self.ASSETS[color]
        else:
            projectile = self.DEFAULT_ASSET
        super().__init__(projectile)
        if self.SIZE_FACTOR != 1.0:
            self.original = self.image = pygame.transform.scale(
                self.image, (
                    int(self.size[0] * self.SIZE_FACTOR),
                    int(self.size[1] * self.SIZE_FACTOR),
                )
            )
        if self.ASSET_ANGLE != 0:
            self.original = self.image = pygame.transform.rotate(
                self.image, self.ASSET_ANGLE
            )

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

        util.register_drawer(assets.WEAPONS_LAYER, self)
        util.register_animator(self.move)

        # relative to the race_track
        self.speed = (
            self.SPEED * cos,
            self.SPEED * sin,
        )
        self.radians = angle  # to make collide() happy

        self._pts = ()
        self.recompute_pts()

        self.max_speed_sq = (
            ((self.image.get_size()[0] * 1.5) ** 2) +
            ((self.image.get_size()[1] * 1.5) ** 2)
        )
        self.max_speed = math.sqrt(self.max_speed_sq)

    def recompute_pts(self):
        # TODO(Jflesch): very approximative ...
        s = self.image.get_size()
        self._pts = (
            (0, 0),
            (0, s[1]),
            (s[0], s[1]),
            (s[0], 0),
        )

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
        for pt in self._pts:
            yield (
                relative[0] + pt[0],
                relative[1] + pt[1],
            )

    def turn(self, frame_interval):
        # most projectiles actually don't turn
        return

    def move(self, frame_interval):
        self.turn(frame_interval)

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
        Explosion(self.parent, position,
                  self.EXPLOSION_SIZE,
                  self.EXPLOSION_TIME)

        target = collisions[0].obstacle
        if hasattr(target, 'damage'):
            target.damage(self.DAMAGE)
            logger.info("Hit: {} ; health: {} ; shield : {}".format(
                target, target.health, target.shield
            ))

        if self.EXPLOSION_DAMAGE > 0:
            self.parent.collisions.collide(
                self, collisions, frame_interval
            )
            for car in self.parent.cars:
                dist = util.distance_sq_pt_to_pt(car.position, position)
                if dist < self.explosion_range_sq:
                    car.damage(self.EXPLOSION_DAMAGE)
                    logger.info("Hit: {} ; health: {} ; shield : {}".format(
                        car, car.health, car.shield
                    ))


class Weapon(object):
    MIN_FIRE_INTERVAL = 0.5

    def __init__(self, generator, shooter):
        self.parent = generator
        self.shooter = shooter
        self.shooter.weapon = self
        self.last_shot = 0

    def deactivate(self):
        pass

    def fire(self):
        n = time.time()
        if n - self.last_shot <= self.MIN_FIRE_INTERVAL:
            return False
        self.last_shot = n
        return True


class Turret(Weapon):
    MIN_FIRE_INTERVAL = 0.2
    TURRET_ANGLE = 180

    def __init__(self, generator, shooter, turret_rsc):
        super().__init__(generator, shooter)
        self.shooter.extra_drawers.add(self)
        self.angle = 0
        self.turret_base = assets.load_image(assets.TURRET_BASE)
        self.turret = assets.load_image(turret_rsc)
        self.turret = pygame.transform.rotate(self.turret, self.TURRET_ANGLE)

    def draw(self, screen, shooter):
        turret_base = self.turret_base
        turret_base_size = turret_base.get_size()

        turret = self.turret
        turret = pygame.transform.rotate(turret, -self.angle)
        turret_size = turret.get_size()

        shooter_parent_abs = shooter.parent.absolute
        shooter_position = shooter.position

        for (size, el) in [
                    (turret_base_size, turret_base),
                    (turret_size, turret)
                ]:
            screen.blit(
                el,
                (
                    shooter_parent_abs[0] + shooter_position[0] - (size[0] / 2),
                    shooter_parent_abs[1] + shooter_position[1] - (size[1] / 2),
                )
            )

    def deactivate(self):
        self.shooter.extra_drawers.remove(self)


class StaticTurret(Turret):
    def __init__(self, generator, shooter, turret_rsc):
        super().__init__(generator, shooter, turret_rsc)

    def draw(self, screen, shooter):
        self.angle = shooter.angle
        super().draw(screen, shooter)


class CrossairDrawer(object):
    def __init__(self, turret, crossair):
        self.turret = turret
        self.crossair = crossair

    def draw(self, screen):
        if self.turret.target is None:
            return
        cross_size = self.crossair.get_size()
        target_absolute = self.turret.target.absolute
        target_size = self.turret.target.image.get_size()
        position = (
            target_absolute[0] + ((target_size[0] - cross_size[0]) / 2),
            target_absolute[1] + ((target_size[1] - cross_size[1]) / 2),
        )
        screen.blit(self.crossair, position)


class AutomaticTurret(Turret):
    def __init__(self, generator, race_track, shooter, turret_rsc):
        super().__init__(generator, shooter, turret_rsc)
        self.race_track = race_track
        if shooter.color in assets.CROSSAIRS:
            crossair = assets.load_image(
                assets.CROSSAIRS[shooter.color][:2]
            )
        else:
            crossair = assets.load_image(
                assets.CROSSAIRS[(255, 255, 255)][:2]
            )
        self.target = None
        self.crossair = CrossairDrawer(self, crossair)
        util.register_drawer(assets.WEAPONS_LAYER, self.crossair)

    @staticmethod
    def find_closest_target(shooter, race_track):
        best = (0xFFFFFFFF, None)
        for car in race_track.cars:
            if car is shooter:
                continue
            if not car.ALIVE:
                continue
            dist = util.distance_sq_pt_to_pt(shooter.position, car.position)
            if dist < best[0]:
                best = (dist, car)
        return best[1]

    def draw(self, screen, shooter):
        self.target = self.find_closest_target(shooter, self.race_track)
        if self.target is None:
            self.angle = shooter.angle
        else:
            self.angle = math.atan2(
                self.target.position[0] - shooter.position[0],
                -(self.target.position[1] - shooter.position[1]),
            ) * 180 / math.pi
        super().draw(screen, shooter)

    def deactivate(self):
        super().deactivate()
        util.unregister_drawer(self.crossair)
