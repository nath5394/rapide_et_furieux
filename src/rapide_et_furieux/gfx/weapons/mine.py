#!/usr/bin/env python3

import pygame

from . import common
from ... import assets


class Mine(object):
    category = common.CATEGORY_COUNTER_MEASURES

    def __init__(self):
        self.image = assets.load_image(assets.MINE)
        img_size = self.image.get_size()
        ratio = max(
            img_size[0] / 32,
            img_size[1] / 32,
        )
        img_size = (int(img_size[0] / ratio), int(img_size[1] / ratio))
        self.image = pygame.transform.scale(self.image, img_size)

    def activate(self, race_track, car):
        # TODO
        return None

    def __str__(self):
        return "Mine"

    def __hash__(self):
        return hash("mine")

    def __eq__(self, o):
        return isinstance(o, Mine)
