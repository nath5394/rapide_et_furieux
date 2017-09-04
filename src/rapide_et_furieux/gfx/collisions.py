#!/usr/bin/env python3

import collections
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
    def get_collision_angle(line_moving, line_obstacle, collision_pt):
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
        return ((0, 0), (0, 0))

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
        speed = moving.speed
        for collision in collisions:
            moving_line = collision.moving_line
            obstacle = collision.obstacle
            obstacle_line = collision.obstacle_line
            collision_pt = collision.point

            # we did collide --> compute correction
            collision_angle = self.get_collision_angle(
                moving_line, obstacle_line, collision_pt
            )
            # assert(collision_angle)
            (speed, removed_speed) = self.nullify_speed(
                speed, collision_angle
            )
            # static obstacles will just ignore the new speed
            obstacle.speed = (
                obstacle.speed[0] + removed_speed[0],
                obstacle.speed[1] + removed_speed[1]
            )
        return speed
