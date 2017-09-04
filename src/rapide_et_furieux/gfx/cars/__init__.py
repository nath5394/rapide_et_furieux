#!/usr/bin/env python3

import collections
import math

import pygame

from .. import RelativeSprite
from ... import assets
from ... import util


Controls = collections.namedtuple(
    typename="controls",
    field_names=(
        # all are booleans
        "accelerate",
        "brake",
        "steer_left",
        "steer_right",
    ),
)


class Car(RelativeSprite):
    def __init__(self, resource, race_track, game_settings,
                 spawn_point, spawn_orientation, image=None):
        super().__init__(resource, image)

        self.game_settings = game_settings
        self.parent = race_track

        self.angle = spawn_orientation
        # we work in radians here
        self.radians = spawn_orientation * math.pi / 180 - (math.pi / 2)

        self.position = (
            # center of the car
            (spawn_point[0] * assets.TILE_SIZE[0]) + (assets.TILE_SIZE[0] / 2),
            (spawn_point[1] * assets.TILE_SIZE[1]) + (assets.TILE_SIZE[1] / 2),
        )

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

        self.update_image()

        util.register_animator(self.move)

    def update_image(self):
        self.angle = (self.radians + (math.pi / 2)) * 180 / math.pi
        self.image = pygame.transform.rotate(self.original, -self.angle)
        self.size = self.image.get_size()
        self.relative = (
            self.position[0] - (self.size[0] / 2),
            self.position[1] - (self.size[1] / 2),
        )

    def compute_forward_speed(self, current_speed, frame_interval, terrain):
        engine_braking = self.game_settings['engine braking'][terrain]

        if not self.controls.accelerate and not self.controls.brake:
            if current_speed == 0:
                return 0

            # --> engine braking
            engine_braking *= frame_interval

            if current_speed < 0:
                engine_braking *= -1

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
            speed = min(current_speed + engine_braking, -max_speed['reverse'])

        return speed

    def compute_lateral_speed(self, speed, frame_interval, terrain):
        slowdown = self.game_settings['lateral_speed_slowdown'][terrain]
        if speed == 0:
            return speed

        # TODO(Jflesch): we may be burning tires

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

    def apply_speed(self, frame_interval):
        # self.speed is relative to the car, but self.position is relative
        # to the race track
        # so we switch to polar coordinates, change the angle, and switch
        # back to cartesian coordinates

        speed = (
            math.sqrt((self.speed[0] ** 2) + (self.speed[1] ** 2)),
            math.atan2(-self.speed[1], self.speed[0])
        )
        speed = (speed[0], speed[1] + self.radians)
        speed = (
            speed[0] * math.cos(speed[1]) * frame_interval,
            speed[0] * math.sin(speed[1]) * frame_interval,
        )

        self.position = (
            self.position[0] + speed[0],
            self.position[1] + speed[1],
        )

    def turn(self, frame_interval, terrain):
        if not self.controls.steer_left and not self.controls.steer_right:
            return

        ref_speed = self.game_settings['steering']['ref_speed']

        angle_change = self.game_settings['steering'][terrain] * frame_interval
        if self.controls.steer_left:
            angle_change *= -1
        if self.speed[0] < 0:
            angle_change *= -1
        angle_change *= min(1.0, abs(self.speed[0]) / ref_speed)

        self.radians = self.radians + angle_change

        # cars turns, but not its speed / momentum
        # turn the speed into polar coordinates --> change the angle,
        # switch back
        speed = (
            math.sqrt(self.speed[0] ** 2 + self.speed[1] ** 2),
            math.atan2(self.speed[1], self.speed[0]) + angle_change
        )
        self.speed = (
            speed[0] * math.cos(speed[1]),
            speed[0] * math.sin(speed[1]),
        )

    def move(self, frame_interval):
        terrain = self.parent.get_terrain(self.position)

        self.update_speed(frame_interval, terrain)
        self.apply_speed(frame_interval)
        self.turn(frame_interval, terrain)
        self.update_image()
