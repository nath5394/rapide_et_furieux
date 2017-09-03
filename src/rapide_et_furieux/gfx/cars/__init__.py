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
        self.radians = spawn_orientation * math.pi / 180

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
        self.speed = 0
        self.angular_speed = 0

        self.update_image()

        util.register_animator(self.move)

    def update_image(self):
        self.angle = self.radians * 180 / math.pi
        self.image = pygame.transform.rotate(self.original, -self.angle)
        self.size = self.image.get_size()
        self.relative = (
            self.position[0] - (self.size[0] / 2),
            self.position[1] - (self.size[1] / 2),
        )

    def update_speed(self, frame_interval):
        terrain = self.parent.get_terrain(self.position)

        if not self.controls.accelerate and not self.controls.brake:
            # --> engine braking
            engine_braking = self.game_settings['engine braking']
            engine_braking *= frame_interval
            speed = self.speed - engine_braking

            # if speed change sign, just stall the car
            if self.speed >= 0 and speed <= 0:
                self.speed = 0
            elif self.speed <= 0 and speed >= 0:
                self.speed = 0
            else:
                self.speed = speed
        elif self.controls.brake and self.speed > 0:
            # --> braking
            acceleration = -self.game_settings['braking'][terrain]
            acceleration *= frame_interval

            # apply to speed
            self.speed = self.speed + acceleration
            if self.speed < 0:
                self.speed = 0
        else:
            # --> accelerate (forward or rear)
            acceleration = self.game_settings['acceleration'][terrain]
            acceleration *= frame_interval

            if self.controls.brake:
                acceleration *= -1

            # apply to speed
            self.speed = self.speed + acceleration

        # limit speed
        max_speed = self.game_settings['max_speed'][terrain]
        if self.speed > max_speed['forward']:
            self.speed = max_speed['forward']
        elif self.speed < -max_speed['reverse']:
            self.speed = -max_speed['reverse']

    def apply_speed(self, frame_interval):
        speed = self.speed * frame_interval
        speed = (
            speed * math.sin(self.radians),
            speed * math.cos(self.radians),
        )
        self.position = (
            self.position[0] + speed[0],
            self.position[1] + speed[1],
        )

    def move(self, frame_interval):
        self.update_speed(frame_interval)
        self.apply_speed(frame_interval)
        self.update_image()
