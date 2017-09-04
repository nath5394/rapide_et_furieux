#!/usr/bin/env python3

import itertools
import logging

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
        assert False, "subclass must implement update_image()"


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
                line[1][0] - line[0][0],
                line[1][1] - line[0][1],
            ),
        ) for line in [line_a, line_b]]
        for rect in [rect_a, rect_b]:
            rect.normalize()

        return rect_a.colliderect(rect_b)

    @staticmethod
    def get_collision_point(line_a, line_b):
        return util.get_segment_intersect_point(line_a, line_b)

    @staticmethod
    def get_collision_angle(line_a, line_b):
        """
        Returns the angle of the collision if there is any
        """
        return None

    @staticmethod
    def nullify_speed(speed, angle):
        """
        Cancel part of the speed for the matching angle.
        Only keep the speed that is on the opposite side of the angle.

        Return the new speed, and the removed part.
        """
        return (speed, (0, 0))

    def check(self, moving):
        """
        check() must be called before the next movement of the car.
        It will cancel/reverse part of its speed if required
        """
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
                    if (self.get_collision_point(moving_line, obstacle_line)
                            is None):
                        continue

                    # we did collide --> compute correction
                    print("{} || {}".format(moving_line, obstacle_line))
                    collision_angle = self.get_collision_angle(
                        moving_line, obstacle_line
                    )
                    if collision_angle is None:
                        continue
                    (moving.speed, removed_speed) = self.nullify_speed(
                        moving.speed, collision_angle
                    )
                    # static obstacles will just ignore the new speed
                    obstacle.speed = (
                        obstacle.speed[0] + removed_speed[0],
                        obstacle.speed[1] + removed_speed[1]
                    )