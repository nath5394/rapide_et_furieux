#!/usr/bin/env python3

import collections
import itertools
import logging
import math

import pygame

from .. import assets
from .. import util


logger = logging.getLogger(__name__)


class CollisionObject(object):
    def __init__(self, *args, **kwargs):
        self.static = True

        self.pts = []  # array of (x, y)

        # following attributes aren't really used on static objects
        # they are just here so the algorithms stay the same
        # for everything
        self.radians = 0  # radians = 0 : object is turned to the right
        # speed relative to the object, not the track !
        self.speed = (0, 0)

    def update_image(self):
        pass


Collision = collections.namedtuple(
    typename="collision",
    field_names=(
        "moving_line",
        "obstacle",
        "obstacle_line",
        "point",
    ),
)


class CollisionHandler(object):
    MIN_SQ_DISTANCE_FOR_MOVING_COLLISION = (assets.TILE_SIZE[0] * 2) ** 2
    MIN_SPEED_FOR_COLLISION_SOURCE = 0.00001
    MAX_ANGLE_FOR_COLLISION_SOURCE = 2 * math.pi / 3

    def __init__(self, racetrack, game_settings):
        self.game_settings = game_settings
        self.racetrack = racetrack

        # (grid_position[0], grid_position[1]) --> obstacle
        self.precomputed_static = {}
        self.precomputed_moving = {}

        self.car_diameter_sq = (
            (assets.TILE_SIZE[0] * assets.CAR_SCALE_FACTOR) ** 2
        )

    @staticmethod
    def can_collide(line_a, line_b):
        """
        Figure out if there is even a remote chance that these line collides
        """
        (rect_a, rect_b) = [pygame.Rect(
            line[0],
            (
                line[1][0] - line[0][0] + 1,
                line[1][1] - line[0][1] + 1,
            ),
        ) for line in [line_a, line_b]]
        for rect in [rect_a, rect_b]:
            rect.normalize()
            rect.width += 1
            rect.height += 1

        return rect_a.colliderect(rect_b)

    @staticmethod
    def get_collision_point(line_a, line_b):
        return util.get_segment_intersect_point(line_a, line_b)

    @staticmethod
    def get_collision_angle(line_moving, line_obstacle, car_position):
        """
        Returns the angle of the collision if there is any
        """
        angle = math.atan2(
            - (line_obstacle[1][1] - line_obstacle[0][1]),
            (line_obstacle[1][0] - line_obstacle[0][0])
        )
        # the collision angle is at 90 degrees from the obstacle
        angle += math.pi / 2

        # cross product will tell us if the angle is on the same side
        # than the car_position or not
        v1 = (
            line_obstacle[1][0] - line_obstacle[0][0],
            (-line_obstacle[1][1]) - (-line_obstacle[0][1])
        )
        v2 = (
            line_obstacle[1][0] - car_position[0],
            (-line_obstacle[1][1]) - (-car_position[1])
        )
        xp = (v1[0] * v2[1]) - (v1[1] * v2[0])
        if xp < 0:
            # cross product tells us the angle is on the other side
            angle += math.pi

        angle %= 2 * math.pi
        return angle

    @staticmethod
    def nullify_speed(speed_car_cart_rel, car_angle, collision_angle,
                      factor):
        """
        Cancel part of the speed for the matching angle.
        Only keep the speed that is on the opposite side of the angle.

        Return the new speed, and the removed part.
        """
        speed_car_cart_rel = (speed_car_cart_rel[0], -speed_car_cart_rel[1])
        speed_car_pol_rel = util.to_polar(speed_car_cart_rel)

        speed_car_pol = (
            speed_car_pol_rel[0],
            speed_car_pol_rel[1] + car_angle,
        )

        speed_car_cart = util.to_cartesian(speed_car_pol)
        speed_car_cart = (speed_car_cart[0], -speed_car_cart[1])

        # collision angle is the opposite force ; we reverse it here
        collision_angle += math.pi
        collision_angle %= 2 * math.pi

        removed_pol = (speed_car_pol[0] *
                       math.cos(speed_car_pol[1] - collision_angle),
                       collision_angle)
        to_nullify_pol = (removed_pol[0] * factor, removed_pol[1])
        to_nullify_cart = util.to_cartesian(to_nullify_pol)
        to_nullify_cart = removed_cart = (
            to_nullify_cart[0], -to_nullify_cart[1]
        )

        speed_car_cart = (
            speed_car_cart[0] - to_nullify_cart[0],
            speed_car_cart[1] - to_nullify_cart[1]
        )

        speed_car_cart = (speed_car_cart[0], -speed_car_cart[1])
        speed_car_pol = util.to_polar(speed_car_cart)

        speed_car_pol_rel = (
            speed_car_pol[0],
            speed_car_pol[1] - car_angle,
        )

        speed_car_cart_rel = util.to_cartesian(speed_car_pol_rel)
        speed_car_cart_rel = (speed_car_cart_rel[0], -speed_car_cart_rel[1])

        return (speed_car_cart_rel, removed_cart)

    @staticmethod
    def get_obstacle_angle(line_obstacle, car_angle):
        angle = math.atan2(
            - (line_obstacle[1][1] - line_obstacle[0][1]),
            (line_obstacle[1][0] - line_obstacle[0][0])
        )
        # make sure the angle is oriented as the car
        angle -= car_angle - (math.pi / 2)
        angle %= math.pi
        angle += car_angle - (math.pi / 2)
        return angle

    @staticmethod
    def update_angle(car_angle, obstacle_angle, ratio):
        MAX_ANGLE = math.pi / 8

        diff = car_angle - obstacle_angle
        if abs(diff) <= math.pi / 32:
            # close enough to the obstacle angle --> we align them
            # to reduce collisions issues
            return obstacle_angle
        diff *= ratio

        if abs(diff) > MAX_ANGLE:
            n = diff < 0
            diff = MAX_ANGLE
            if n:
                diff *= -1

        return car_angle - diff

    @staticmethod
    def add_speed(speed_a_cart_rel, angle_a, speed_b_cart):
        speed_a_pol_rel = util.to_polar(speed_a_cart_rel)
        speed_a_pol = (
            speed_a_pol_rel[0],
            speed_a_pol_rel[1] + angle_a
        )
        speed_a_cart = util.to_cartesian(speed_a_pol)
        speed_a_cart = (speed_a_cart[0], -speed_a_cart[1])
        speed_a_cart = (
            speed_a_cart[0] - speed_b_cart[0],
            speed_a_cart[1] - speed_b_cart[1],
        )
        speed_a_pol = util.to_polar(speed_a_cart)
        speed_a_pol_rel = (speed_a_pol[0], speed_a_pol[1] - angle_a)
        speed_a_cart_rel = util.to_cartesian(speed_a_pol_rel)
        return (speed_a_cart_rel[0], speed_a_cart_rel[1])

    def precompute_static(self):
        self.precomputed_static = {}
        for obstacle in self.racetrack.borders:
            for obstacle_line in util.pairwise(obstacle.pts):
                for grid in util.raytrace(
                                obstacle_line, assets.TILE_SIZE[0]
                            ):
                        offsets = itertools.product(
                            range(-1, 2, 1),
                            range(-1, 2, 1),
                        )
                        for offset in offsets:
                            pos = (grid[0] + offset[0], grid[1] + offset[1])
                            if pos not in self.precomputed_static:
                                self.precomputed_static[pos] = set()
                            self.precomputed_static[pos].add(obstacle)

    def precompute_moving(self, *args, **kwargs):
        self.precomputed_moving = {}
        for obstacle in self.racetrack.cars:
            grid = (int(obstacle.position[0] / assets.TILE_SIZE[0]),
                    int(obstacle.position[1] / assets.TILE_SIZE[1]))
            offsets = itertools.product(
                range(-2, 3, 1),
                range(-2, 3, 1),
            )
            for offset in offsets:
                pos = (grid[0] + offset[0], grid[1] + offset[1])
                if pos not in self.precomputed_moving:
                    self.precomputed_moving[pos] = set()
                self.precomputed_moving[pos].add(obstacle)

    def get_possible_obstacle(self, precomputed, position):
        grid = (
            int(position[0] / assets.TILE_SIZE[0]),
            int(position[1] / assets.TILE_SIZE[1]),
        )
        try:
            return precomputed[grid]
        except KeyError:
            return []

    def has_obstacle_in_path(self, moving, path, optim=True):
        """
        Figure out if an moving element has a moving obstacle on its path.
        Return *approximate* result
        """
        car = self.racetrack.cars
        if optim:
            cars = self.get_possible_obstacle(
                self.precomputed_moving, moving.position
            )
        for car in cars:
            if car is moving:
                # ignore self
                continue
            dist = util.distance_sq_pt_to_segment(path, car.position)
            if dist < self.car_diameter_sq:
                return True
        return False

    def get_obstacles_on_segment(self, segment, limit=None):
        found = 0
        for (x, y) in util.raytrace(segment, grid_size=assets.TILE_SIZE[0]):
            position = (
                x * assets.TILE_SIZE[0],
                y * assets.TILE_SIZE[1],
            )
            obstacles = [
                self.get_possible_obstacle(self.precomputed_static, position),
                self.get_possible_obstacle(self.precomputed_moving, position),
            ]
            for obstacle in itertools.chain(*obstacles):
                for obstacle_line in util.pairwise(obstacle.pts):
                    if not self.can_collide(segment, obstacle_line):
                        continue
                    collision_pt = self.get_collision_point(
                        segment, obstacle_line
                    )
                    if collision_pt is None:
                        continue
                    yield((obstacle, collision_pt))
                    found += 1
                    break
            if limit is not None and found >= limit:
                return

    def get_collisions(self, moving, limit=None, optim=True, debug=False):
        collisions = []
        if optim:
            obstacles = [
                self.get_possible_obstacle(
                    self.precomputed_static, moving.position
                ),
                self.get_possible_obstacle(
                    self.precomputed_moving, moving.position
                ),
            ]
        else:
            obstacles = [
                self.get_possible_obstacle(
                    self.precomputed_static, moving.position
                ),
                self.racetrack.cars,
            ]
        for obstacle in itertools.chain(*obstacles):
            if obstacle is moving:
                # ignore self
                continue
            if hasattr(obstacle, 'position'):
                p1 = moving.position
                p2 = obstacle.position
                dist = util.distance_sq_pt_to_pt(p1, p2)
                if dist >= self.MIN_SQ_DISTANCE_FOR_MOVING_COLLISION:
                    # not close enough
                    continue
            for moving_line in util.pairwise(moving.pts):
                for obstacle_line in util.pairwise(obstacle.pts):
                    # did we collide ?
                    if not self.can_collide(moving_line, obstacle_line):
                        continue
                    collision_pt = self.get_collision_point(
                        moving_line, obstacle_line
                    )
                    if collision_pt is None:
                        continue
                    collisions.append(Collision(
                        moving_line=moving_line,
                        obstacle=obstacle,
                        obstacle_line=obstacle_line,
                        point=collision_pt
                    ))
                    if limit is not None and len(collisions) >= limit:
                        return collisions
        return collisions

    def collide(self, moving, collisions, frame_interval):
        if collisions is None or len(collisions) <= 0:
            return

        angle_trans = (
            self.game_settings['collision']['angle_transmission'] *
            frame_interval
        )

        position = moving.position
        speed = moving.speed
        radians = moving.radians

        for collision in collisions:
            moving_line = collision.moving_line
            obstacle = collision.obstacle
            obstacle_line = collision.obstacle_line

            if not obstacle.static:
                # did we collide with them, or did they collide with us ?
                speed_polar_rel = util.to_polar(speed)
                if speed[0] < self.MIN_SPEED_FOR_COLLISION_SOURCE:
                    other_speed = util.to_polar(obstacle.speed)
                    if other_speed[0] >= self.MIN_SPEED_FOR_COLLISION_SOURCE:
                        continue
                speed_angle_abs = speed_polar_rel[1] + radians
                obstacle_pos = obstacle.position
                collision_angle = -math.atan2(
                    obstacle_pos[1] - position[1],
                    obstacle_pos[0] - position[0]
                )
                diff = collision_angle - speed_angle_abs
                diff %= 2 * math.pi
                if (diff > self.MAX_ANGLE_FOR_COLLISION_SOURCE and
                        diff < ((2 * math.pi) -
                                self.MAX_ANGLE_FOR_COLLISION_SOURCE)):
                    continue

            collision_angle = self.get_collision_angle(
                moving_line, obstacle_line, position
            )

            # we did collide --> compute correction
            obstacle_angle = self.get_obstacle_angle(
                obstacle_line, radians
            )

            if obstacle.static:
                factor = self.game_settings['collision']['reverse_factor']
            else:
                factor = self.game_settings['collision']['propagation']

            (speed, removed_speed) = self.nullify_speed(
                speed, radians, collision_angle, factor,
            )
            radians = self.update_angle(
                radians, obstacle_angle, angle_trans
            )

            # static obstacles will just ignore the new speed
            obstacle.speed = self.add_speed(
                obstacle.speed, obstacle.radians, removed_speed
            )

        return (speed, radians)
