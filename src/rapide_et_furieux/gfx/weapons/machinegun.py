#!/usr/bin/env python3

import pygame

from ... import assets


class MachineGun(object):
    def __init__(self):
        self.image = assets.load_image(assets.BULLET)
        self.image = pygame.transform.rotate(self.image, -90)

    def activate(self, race_track, car):
        # TODO
        assert()

    def __str__(self):
        return "Machine gun"

    def __hash__(self):
        return hash("machingun")

    def __eq__(self, o):
        return isinstance(o, MachineGun)
