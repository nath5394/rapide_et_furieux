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

        if ((bool(keys[pygame.K_RCTRL]) or bool(keys[pygame.K_LCTRL])) and
                self.weapon):
            self.weapon.fire()
            count = self.weapons[self.weapon.parent]
            count -= 1
            if count <= 0:
                self.weapon.deactivate()
                self.weapons.pop(self.weapon.parent)
                self.weapon = None
            else:
                self.weapons[self.weapon.parent] = count
            for obs in self.weapon_observers:
                obs()

        accelerate = (
            bool(keys[pygame.K_UP]) or bool(keys[pygame.K_w]) or
            bool(keys[pygame.K_KP8])
        )
        brake = (
            bool(keys[pygame.K_DOWN]) or bool(keys[pygame.K_s]) or
            bool(keys[pygame.K_KP1]) or bool(keys[pygame.K_SPACE])
        )
        if accelerate and brake:
            # default to braking
            accelerate = False
            brake = True

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
