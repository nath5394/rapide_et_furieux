#!/usr/bin/env

import pygame

from . import Car
from . import Controls
from ... import util


class PlayerCar(Car):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        util.register_animator(self.on_frame)

    def on_frame(self, frame_interval):
        keys = pygame.key.get_pressed()

        accelerate = (
            bool(keys[pygame.K_UP]) or bool(keys[pygame.K_w]) or
            bool(keys[pygame.K_KP8])
        )
        brake = (
            bool(keys[pygame.K_DOWN]) or bool(keys[pygame.K_s]) or
            bool(keys[pygame.K_KP1])
        )
        if accelerate and brake:
            accelerate = False
            brake = False

        left = (
            bool(keys[pygame.K_LEFT]) or bool(keys[pygame.K_a]) or
            bool(keys[pygame.K_KP4])
        )
        right = (
            bool(keys[pygame.K_RIGHT]) or bool(keys[pygame.K_d]) or
            bool(keys[pygame.K_KP6])
        )
        if left and right:
            left = False
            right = False

        self.controls = Controls(
            accelerate=accelerate,
            brake=brake,
            steer_left=left,
            steer_right=right,
        )
