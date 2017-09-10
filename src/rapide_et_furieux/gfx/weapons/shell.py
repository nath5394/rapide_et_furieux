#!/usr/bin/env python3

import pygame

from ... import assets


class TankShell(object):
    def __init__(self):
        self.image = assets.load_image(assets.BULLET)
        self.image = pygame.transform.rotate(self.image, -90)
        img_size = self.image.get_size()
        img_size = (img_size[0] * 2, img_size[1] * 2)
        self.image = pygame.transform.scale(self.image, img_size)

    def activate(self, race_track, car):
        # TODO
        return None

    def __str__(self):
        return "Tank shell"

    def __hash__(self):
        return hash("Tank shell")

    def __eq__(self, o):
        return isinstance(o, TankShell)
