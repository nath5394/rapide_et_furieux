#!/usr/bin/env python3

import collections
import itertools
import logging
import math

import pygame

from .. import util


logger = logging.getLogger(__name__)


class CollisionObject(object):
    def __init__(self, *args, **kwargs):
        self.pts = []  # array of (x, y)

        # following attributes aren't really used on static objects
        # they are just here so the algorithms stay the same
        # for everything
        self.radians = 0  # radians = 0 : object is turned to the right
        self.position = (0, 0)  # center

        # speed relative to the object, not the track !
        self.speed = (0, 0)

    def update_image(self):
        pass

    def apply_speed(self, frame_interval, position):
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
    def __init__(self, racetrack, game_settings):
        self.game_settings = game_settings
        self.racetrack = racetrack

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
        # than the cat or not
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
                      reverse_factor):
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

        to_nullify_pol = (speed_car_pol[0] *
                          math.cos(speed_car_pol[1] - collision_angle) *
                          reverse_factor,
                          collision_angle)

        to_nullify_cart = util.to_cartesian(to_nullify_pol)

        speed_car_cart = (
            speed_car_cart[0] - to_nullify_cart[0],
            speed_car_cart[1] + to_nullify_cart[1]
        )

        speed_car_cart = (speed_car_cart[0], -speed_car_cart[1])
        speed_car_pol = util.to_polar(speed_car_cart)

        speed_car_pol_rel = (
            speed_car_pol[0],
            speed_car_pol[1] - car_angle,
        )

        speed_car_cart_rel = util.to_cartesian(speed_car_pol_rel)
        speed_car_cart_rel = (speed_car_cart_rel[0], -speed_car_cart_rel[1])

        return (speed_car_cart_rel, to_nullify_cart)

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
        diff = car_angle - obstacle_angle
        diff *= ratio
        if abs(diff) > math.pi / 128:
            new_angle = car_angle - diff
        else:
            # close enough to the obstacle angle --> we align them
            # to reduce collisions issues
            new_angle = obstacle_angle
        return new_angle

    @staticmethod
    def add_speed(speed_a_cart_rel, angle_a, speed_b_cart):
        speed_a_pol_rel = util.to_polar(speed_a_cart_rel)
        speed_a_pol = (
            speed_a_pol_rel[0],
            speed_a_pol_rel[1] + angle_a
        )
        speed_a_cart = util.to_cartesian(speed_a_pol)
        speed_a_pol = util.to_polar((
            speed_a_cart[0] + speed_b_cart[0],
            speed_a_cart[1] + speed_b_cart[1],
        ))
        speed_a_pol_rel = (
            speed_a_pol[0],
            speed_a_pol[1] - angle_a,
        )
        return util.to_cartesian(speed_a_pol_rel)

    def get_collisions(self, moving, limit=None):
        collisions = []
        for moving_line in util.pairwise(moving.pts):
            for obstacle in itertools.chain(
                        self.racetrack.borders, self.racetrack.cars
                    ):
                if obstacle is moving:
                    # ignore self
                    continue
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

        speed = moving.speed
        collision = collisions[0]  # only the first point is taken into account

        moving_line = collision.moving_line
        obstacle = collision.obstacle
        obstacle_line = collision.obstacle_line

        # we did collide --> compute correction
        collision_angle = self.get_collision_angle(
            moving_line, obstacle_line, moving.position
        )
        obstacle_angle = self.get_obstacle_angle(
            obstacle_line, moving.radians
        )

        (speed, removed_speed) = self.nullify_speed(
            speed, moving.radians, collision_angle,
            self.game_settings['collision']['reverse_factor'],
        )
        new_angle = self.update_angle(
            moving.radians, obstacle_angle,
            self.game_settings['collision']['angle_transmission'] *
            frame_interval
        )
        # static obstacles will just ignore the new speed
        obstacle.speed = self.add_speed(
            obstacle.speed, obstacle.radians, removed_speed
        )
        return (speed, new_angle)
