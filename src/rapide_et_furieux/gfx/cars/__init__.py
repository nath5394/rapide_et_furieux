#!/usr/bin/env python3

import itertools
import logging
import math
import random

import pygame

from .. import RelativeSprite
from ... import assets
from ... import sounds
from ... import util
from ..collisions import CollisionObject
from ..weapons import common

UNIQUE = 0

logger = logging.getLogger(__name__)


class Controls(object):
    def __init__(self, accelerate, brake, steer_left, steer_right):
        self.accelerate = accelerate
        self.brake = brake
        self.steer_left = steer_left
        self.steer_right = steer_right


class SkidMark(RelativeSprite):
    HEIGHT = 24
    LIFE_LENGTH = 2.0
    OFFSET = 16

    def __init__(self, racetrack, car, resource=None, image=None, scale=True):
        if resource is None:
            scale = True
            resource = random.sample(assets.SKIDMARKS, 1)[0]
        super().__init__(resource, image)

        if scale:
            self.original = self.image = self.original.subsurface(
                (0, 0), (self.original.get_size()[0], self.HEIGHT)
            )
            self.original = self.image = pygame.transform.scale(
                self.original,
                (
                    int(self.original.get_size()[0] * assets.CAR_SCALE_FACTOR),
                    int(self.original.get_size()[1] * assets.CAR_SCALE_FACTOR),
                )
            )
            car_size = car.original.get_size()
            img = pygame.Surface(car_size, pygame.SRCALPHA)

            pos = (0, self.OFFSET)
            img.blit(self.original, pos)
            pos = (0, car_size[1] - self.original.get_size()[1] - self.OFFSET)
            img.blit(self.original, pos)
            self.image = self.original = img

        self.t = self.LIFE_LENGTH
        self.parent = racetrack
        self.car = car

        # TODO(Jflesch): could be optimized

        self.angle = car.angle
        self.image = pygame.transform.rotate(self.image, -self.angle)
        self.size = self.image.get_size()
        self.relative = car.relative

    def copy(self):
        return SkidMark(self.parent, self.car, self.resource, self.original,
                        scale=False)

    def anim(self, frame_interval):
        self.t -= frame_interval
        if self.t < 0:
            self.car.extra_drawers_below.remove(self)
            util.unregister_animator(self.anim)

    def draw(self, screen, car):
        super().draw(screen)


class Car(RelativeSprite, CollisionObject):
    DEFAULT_HEALTH = 100
    ALIVE = True
    SHIELD_ON_RESPAWN = (5, 200)
    DRIFT_SPEED = 350

    DRIFT_NONE = 0
    DRIFT_FIRST_FRAME = 1
    DRIFT_NEXT_FRAMES = 2

    def __init__(self, resource, race_track, game_settings,
                 spawn_point, spawn_orientation, image=None,
                 has_engine_sound=False):
        global UNIQUE

        super().__init__(resource, image)

        self.color = resource[2]

        self.original_size = self.original.get_size()
        self.original_size = (
            int(self.original_size[0] * assets.CAR_SCALE_FACTOR),
            int(self.original_size[1] * assets.CAR_SCALE_FACTOR),
        )
        self.original = self.image = pygame.transform.scale(
            self.original, self.original_size
        )

        self.static = False
        self.h = hash(spawn_point) ^ UNIQUE
        UNIQUE += 1

        self.game_settings = game_settings
        self.parent = race_track

        self.angle = spawn_orientation

        self._pts = None
        self.position = (0, 0)

        self.health = self.DEFAULT_HEALTH

        self.controls = Controls(
            accelerate=False,
            brake=False,
            steer_left=False,
            steer_right=False
        )

        # relative to the car
        # so first number is the forward speed,
        # and second one is the lateral speed (drifting)
        self.speed = (0, 0)

        # we work in radians here
        self.radians = spawn_orientation * math.pi / 180 - (math.pi / 2)

        # position is the center of the car
        self.position = spawn_point

        self.next_checkpoint = self.parent.checkpoints[0]
        self.checkpoint_min_dist_sq = \
            game_settings['checkpoint_min_distance'] ** 2

        self.can_move = False

        self.extra_drawers_below = set()
        self.extra_drawers_above = set()
        self.weapons = {}  # weapon --> number of ammos
        self.weapon_observers = set()
        self.weapon = None  # active weapon

        self.oily = 0
        self.shield = (0, 0)

        self.base_exploded = ExplodedCar.generate_base_exploded(self.original)

        self.drift = self.DRIFT_NONE
        self.has_engine_sound = has_engine_sound
        if self.has_engine_sound:
            self.engine_sound_channel = sounds.reserve_channel()

        self.skidmark = SkidMark(self.parent, self)
        self.skidmark_oil = SkidMark(
            self.parent, self, assets.SKIDMARK_OIL
        )

        self.recompute_pts()
        self.update_image()

    def hash(self):
        return self.h

    COLLISION_MARGIN = 3

    def recompute_pts(self):
        self._pts = None

    def _recompute_pts(self):
        pts = [
            ((- (self.original_size[0] / 2)) + self.COLLISION_MARGIN,
             (- (self.original_size[1] / 2)) + self.COLLISION_MARGIN),
            ((self.original_size[0] / 2) - self.COLLISION_MARGIN,
             (- (self.original_size[1] / 2)) + self.COLLISION_MARGIN),
            ((self.original_size[0] / 2) - self.COLLISION_MARGIN,
             (self.original_size[1] / 2) - self.COLLISION_MARGIN),
            ((- (self.original_size[0] / 2)) + self.COLLISION_MARGIN,
             (self.original_size[1] / 2) - self.COLLISION_MARGIN),
        ]
        # TODO(Jflesch): can optim: to_polar() could be called only once,
        # and the other points can be deduced
        pts = [util.to_polar(pt) for pt in pts]
        pts = [
            (
                length,
                # The gfx are oriented to the up side, but radians=0 == right
                angle - self.radians + (math.pi / 2)
            ) for (length, angle) in pts
        ]
        pts = [util.to_cartesian(pt) for pt in pts]
        pts = [
            (x + self.position[0], y + self.position[1])
            for (x, y) in pts
        ]
        self._pts = pts

    @property
    def pts(self):
        if self._pts is None:
            self._recompute_pts()
        return self._pts

    def update_image(self):
        # The gfx are oriented to the up side, but radians=0 == right
        self.angle = (-self.radians + (math.pi / 2)) * 180 / math.pi
        self.image = pygame.transform.rotate(self.original, -self.angle)
        self.size = self.image.get_size()
        self.relative = (
            int(self.position[0]) - (self.size[0] / 2),
            int(self.position[1]) - (self.size[1] / 2),
        )

    def compute_forward_speed(self, current_speed, frame_interval, terrain):
        engine_braking = self.game_settings['engine braking'][terrain]
        engine_braking *= frame_interval
        if current_speed < 0:
            engine_braking *= -1

        if not self.controls.accelerate and not self.controls.brake:
            if current_speed == 0:
                return 0

            # --> engine braking
            speed = current_speed - engine_braking

            # if speed change sign, just stall the car
            if current_speed >= 0 and speed <= 0:
                speed = 0
            elif current_speed <= 0 and speed >= 0:
                speed = 0
        elif self.controls.brake and current_speed > 0:
            # TODO(Jflesch): burning tires

            # --> braking
            acceleration = -self.game_settings['braking'][terrain]
            acceleration *= frame_interval

            # apply to speed
            speed = current_speed + acceleration
            if speed < 0:
                speed = 0
        else:
            # --> accelerate (forward or backward)
            acceleration = self.game_settings['acceleration'][terrain]
            acceleration *= frame_interval

            if self.controls.brake:
                acceleration *= -1

            # apply to speed
            speed = current_speed + acceleration

        # limit speed based on terrain
        max_speed = self.game_settings['max_speed'][terrain]
        if speed > max_speed['forward']:
            speed = max(current_speed - engine_braking, max_speed['forward'])
        elif speed < -max_speed['reverse']:
            speed = min(current_speed - engine_braking, -max_speed['reverse'])

        return speed

    def compute_lateral_speed(self, speed, frame_interval, terrain):
        if speed == 0:
            return speed

        slowdown = self.game_settings['lateral_speed_slowdown'][terrain]
        if self.oily > 0:
            slowdown /= 10
            self.oily -= frame_interval

        if speed > 0:
            speed -= slowdown * frame_interval
            return speed if speed >= 0 else 0
        else:  # speed < 0
            speed += slowdown * frame_interval
            return speed if speed <= 0 else 0

    def update_speed(self, frame_interval, terrain):
        self.speed = (
            self.compute_forward_speed(self.speed[0], frame_interval, terrain),
            self.compute_lateral_speed(self.speed[1], frame_interval, terrain)
        )

    def apply_speed(self, frame_interval, position, speed=None):
        # self.speed is relative to the car, but self.position is relative
        # to the race track
        # so we switch to polar coordinates, change the angle, and switch
        # back to cartesian coordinates

        if speed is None:
            speed = self.speed
        speed = (speed[0] * frame_interval, speed[1] * frame_interval)
        # make sure speed isn't too big for collision detection
        speed = (
            util.clamp(speed[0],
                       -assets.TILE_SIZE[0] / 4, assets.TILE_SIZE[0] / 4),
            util.clamp(speed[1],
                       -assets.TILE_SIZE[0] / 4, assets.TILE_SIZE[0] / 4),
        )
        # max speed to avoid issues with low frame rate + collision detection
        # optim
        nspeed = (
            -1 if speed[0] < 0 else 1,
            -1 if speed[1] < 0 else 1,
        )
        speed = (
            min(abs(speed[0]), assets.TILE_SIZE[0] / 2) *
            nspeed[0],
            min(abs(speed[1]), assets.TILE_SIZE[1] / 2) *
            nspeed[1],
        )
        speed = util.to_polar(speed)
        speed = (speed[0], speed[1] - self.radians)
        speed = util.to_cartesian(speed)
        speed = (speed[0], speed[1])

        return (
            position[0] + speed[0],
            position[1] + speed[1],
        )

    def get_steering(self, frame_interval, terrain):
        if not self.controls.steer_left and not self.controls.steer_right:
            return 0
        ref_speed = self.game_settings['steering']['ref_speed']
        angle_change = self.game_settings['steering'][terrain] * frame_interval
        if self.controls.steer_left:
            angle_change *= -1
        if self.speed[0] < 0:
            angle_change *= -1
        angle_change *= min(1.0, abs(self.speed[0]) / ref_speed)
        return angle_change

    def turn(self, angle_change, frame_interval):
        self.radians = self.radians - angle_change
        self.radians %= 2 * math.pi
        self.recompute_pts()

        # cars turns, but not its speed / momentum
        # turn the speed into polar coordinates --> change the angle,
        # switch back
        speed = util.to_polar(self.speed)
        speed = (speed[0], speed[1] - angle_change)
        self.speed = util.to_cartesian(speed)
        return angle_change

    def check_checkpoint(self):
        dist = util.distance_sq_pt_to_pt(self.position, self.next_checkpoint.pt)
        if dist <= self.checkpoint_min_dist_sq:
            self.next_checkpoint = self.next_checkpoint.next_checkpoint

    def grab_bonus(self):
        grab_dist = assets.BONUS_SIZE[0] + (assets.TILE_SIZE[0] / 3)
        grab_dist **= 2

        for bonus in set(self.parent.bonuses):
            dist = util.distance_sq_pt_to_pt(bonus.position, self.position)
            if dist < grab_dist:
                bonus.add_to_car(self)
                self.parent.remove_bonus(bonus)

    def explode(self):
        ExplodedCar(self)
        common.Explosion(self.parent, self.position, assets.TILE_SIZE[0], 1.0)
        sounds.play_from_screen(
            random.sample(assets.SOUNDS['explosion'], 1)[0],
            self
        )

    def damage(self, damage):
        if self.shield[0] > 0:
            self.shield = (self.shield[0], self.shield[1] - damage)
            if self.shield[1] <= 0:
                self.shield = (0, 0)
            return
        self.health -= damage

    def respawn(self):
        if self.weapon is not None:
            self.weapon.deactivate()
            self.weapon = None
        self.weapons = {}
        for obs in self.weapon_observers:
            obs()
        self.health = 100
        self.speed = (0, 0)
        self.shield = self.SHIELD_ON_RESPAWN

        has_collision = True
        while has_collision:
            prev_cp = self.next_checkpoint

            dist = 0
            while dist < self.checkpoint_min_dist_sq:
                prev_cp = prev_cp.previous_checkpoint
                assert(prev_cp is not self.next_checkpoint)
                dist = util.distance_sq_pt_to_pt(
                    self.position, prev_cp.pt
                )

            self.next_checkpoint = prev_cp.next_checkpoint
            self.position = prev_cp.pt

            pos_diff = (
                self.next_checkpoint.pt[0] - prev_cp.pt[0],
                self.next_checkpoint.pt[1] - prev_cp.pt[1],
            )
            self.radians = math.atan2(-pos_diff[1], pos_diff[0])

            self.recompute_pts()
            collisions = self.parent.collisions.get_collisions(
                self, optim=False, limit=1, debug=True
            )
            has_collision = len(collisions) > 0

        self.parent.collisions.precompute_moving()

    def update_sound(self, frame_interval):
        if self.drift == self.DRIFT_FIRST_FRAME:
            sounds.play_from_screen(assets.TIRES, self)

        if not self.has_engine_sound:
            return

        MIN_SPEED = -250
        MAX_SPEED = 770

        speed = abs(self.speed[0])
        self.engine_sound_channel.set_volume(
            (speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED)
        )

        if self.engine_sound_channel.get_busy():
            return

        snd = assets.get_resource(assets.ENGINE[:2])
        self.engine_sound_channel.play(snd, -1)

    def move(self, frame_interval):
        if abs(self.speed[1]) < self.DRIFT_SPEED:
            self.drift = self.DRIFT_NONE
        elif self.drift == self.DRIFT_FIRST_FRAME:
            self.drift = self.DRIFT_NEXT_FRAMES
        else:
            self.drift = self.DRIFT_FIRST_FRAME

        if self.oily > 0 or self.drift != self.DRIFT_NONE:
            if self.oily > 0:
                skidmark = self.skidmark_oil.copy()
            elif self.drift != self.DRIFT_NONE:
                skidmark = self.skidmark.copy()
            self.extra_drawers_below.add(skidmark)
            util.register_animator(skidmark.anim)

        self.update_sound(frame_interval)

        if self.shield[0] > 0:
            self.shield = (self.shield[0] - frame_interval, self.shield[1])
        else:
            self.shield = (0, 0)

        if self.health <= 0:
            self.explode()
            self.respawn()

        if not self.can_move:
            return

        COLLISION = True

        terrain = self.parent.get_terrain(self.position)

        self.update_speed(frame_interval, terrain)

        # steering
        steering = self.get_steering(frame_interval, terrain)
        previous_radians = self.radians
        previous_speed = self.speed
        self.turn(steering, frame_interval)

        if COLLISION:
            collisions = self.parent.collisions.get_collisions(
                self, limit=1, optim=True
            )
            if len(collisions) > 0:
                # cancel steering
                self.speed = previous_speed
                self.radians = previous_radians
                self.recompute_pts()

        # move
        prev_position = self.position
        self.position = self.apply_speed(frame_interval, self.position)
        self.recompute_pts()

        if COLLISION:
            collisions = self.parent.collisions.get_collisions(self, optim=True)
            if len(collisions) > 0:
                # cancel movement
                self.position = prev_position
                self.recompute_pts()

                # update speed based on collision
                previous_radians = self.radians

                (self.speed, self.radians) = self.parent.collisions.collide(
                    self, collisions, frame_interval
                )

                # apply new speed if possible before it's cancelled
                # + angle
                prev_position = self.position
                self.position = self.apply_speed(frame_interval, self.position)
                self.recompute_pts()

                collisions = self.parent.collisions.get_collisions(
                    self, limit=1, optim=False
                )
                if len(collisions) > 0:
                    # .. without angle ?
                    self.radians = previous_radians
                    self.position = prev_position
                    self.position = self.apply_speed(frame_interval,
                                                     self.position)
                    self.recompute_pts()
                    collisions = self.parent.collisions.get_collisions(
                        self, limit=1, optim=False
                    )

                    if len(collisions) > 0:
                        # ok screw it ...
                        self.radians = previous_radians
                        self.position = prev_position
                        self.recompute_pts()

        self.update_image()
        self.grab_bonus()
        self.check_checkpoint()

    def draw(self, screen):
        for drawer in self.extra_drawers_below:
            drawer.draw(screen, self)

        super().draw(screen)

        for drawer in self.extra_drawers_above:
            drawer.draw(screen, self)

        if self.shield[0] > 0:
            absolute = self.parent.absolute
            frame = int(self.shield[0] * 5 % len(assets.SHIELDS))
            shield = assets.load_image(assets.SHIELDS[frame])
            shield = pygame.transform.rotate(shield, -self.angle)
            screen.blit(
                shield,
                (
                    (absolute[0] + self.position[0] -
                     (shield.get_size()[0] / 2)),
                    (absolute[1] + self.position[1] -
                     (shield.get_size()[1] / 2)),
                )
            )

        if not self.parent.debug:
            return
        # it would be faster to draw the rectangle on the image itself
        # but this piece of code is actually used to check that the points of
        # the car are correctly found.
        p = self.parent.absolute
        for (a, b) in util.pairwise(self.pts):
            pygame.draw.line(
                screen, (255, 0, 0),
                (a[0] + p[0], a[1] + p[1]),
                (b[0] + p[0], b[1] + p[1]),
                2
            )

    def add_weapon(self, weapon, count):
        if weapon in self.weapons:
            count += self.weapons[weapon]
        self.weapons[weapon] = count
        for obs in self.weapon_observers:
            obs()


class ExplodedCar(Car):
    LIFE_LENGTH = 1.5
    IMG_PER_SECOND = 5.0
    ALIVE = False

    def __init__(self, parent_car):
        super().__init__(
            parent_car.resource, parent_car.parent,
            parent_car.game_settings, parent_car.position,
            parent_car.angle
        )
        self.radians = parent_car.radians
        self.images = parent_car.base_exploded
        self.speed = parent_car.speed
        self.can_move = True
        self.original = self.images[0]
        self.update_image()

        self.parent.add_car(self)
        self.parent.collisions.precompute_moving()
        util.register_animator(self.anim)

        self.t = 0
        self.frame = 0

    def anim(self, frame_interval):
        self.move(frame_interval)
        self.t += frame_interval
        if self.t >= self.LIFE_LENGTH:
            util.unregister_animator(self.anim)
            self.parent.remove_car(self)
            self.parent.collisions.precompute_moving()
            return
        frame = int(self.t * self.IMG_PER_SECOND)
        if frame >= len(self.images):
            frame = len(self.images) - 1
        if frame == self.frame:
            return
        self.frame = frame
        self.original = self.images[frame]
        self.update_image()

    @staticmethod
    def generate_base_exploded(img):
        # generate basic grayscale image
        base_img = img.copy()
        base_img = img.convert_alpha()
        pixels = pygame.surfarray.pixels3d(base_img)
        for (x, y) in itertools.product(
                    range(0, base_img.get_size()[0]),
                    range(0, base_img.get_size()[1])
                ):
            p = pixels[x][y]
            v = p[0] + p[1] + p[2]
            v /= 3
            if v >= 192:
                # turn whites into dark grays
                v = 255 - v
            pixels[x][y] = (v, v, v)

        # TODO(Jflesch): scratches

        # generate images with various transparency
        imgs = []
        for t in range(0, int(
                    ExplodedCar.LIFE_LENGTH * ExplodedCar.IMG_PER_SECOND
                )):
            # opacity 255 -> 0
            t *= 0.75
            t = 255 - int(
                255 * t / (ExplodedCar.LIFE_LENGTH * ExplodedCar.IMG_PER_SECOND)
            )
            img = base_img.copy()
            pixels = pygame.surfarray.pixels_alpha(img)
            for (x, y) in itertools.product(
                        range(0, img.get_size()[0]),
                        range(0, img.get_size()[1])
                    ):
                p = pixels[x][y]
                if p > t:
                    p = t
                pixels[x][y] = p
            imgs.append(img)
        return imgs

    def damange(self, *args, **kwargs):
        # cannot be damaged
        pass

    def __str__(self):
        return "ExplodedCar ({}|{})".format(self.position, self.radians)

    def __repr__(self):
        return str(self)
