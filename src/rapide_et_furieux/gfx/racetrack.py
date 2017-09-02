import logging

import pygame

from . import RelativeGroup
from .tiles import TileGrid


logger = logging.getLogger(__name__)


def draw_track_border(screen, pt_a, pt_b, parent_absolute=(0, 0)):
    pygame.draw.line(
        screen, (255, 0, 0),
        (
            (pt_a[0] + parent_absolute[0]),
            (pt_a[1] + parent_absolute[1]),
        ),
        (
            (pt_b[0] + parent_absolute[0]),
            (pt_b[1] + parent_absolute[1]),
        ),
    )


class RaceTrack(RelativeGroup):
    def __init__(self, grid_margin=0):
        super().__init__()

        self.tiles = TileGrid(margin=grid_margin)
        self.tiles.parent = self

        self.objects = []
        self.borders = set()  # set of ((pt_a_x, pt_a_y), (pt_b_x, pt_b_y))

    def draw(self, screen):
        self.tiles.draw(screen)
        super().draw(screen)
        for border in self.borders:
            draw_track_border(screen, border[0], border[1], self.absolute)

    def add_object(self, obj):
        self.objects.append(obj)
        self.add(obj)

    def add_border(self, border):
        self.borders.add(border)
