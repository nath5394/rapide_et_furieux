import logging

import pygame

from . import RelativeGroup
from .tiles import TileGrid


logger = logging.getLogger(__name__)


def draw_crap_area(screen, pt_a, pt_b, parent_absolute=(0, 0),
                   color=(0, 255, 0)):
    pygame.draw.rect(
        screen, color,
        pygame.Rect(
            (
                (pt_a[0] + parent_absolute[0]),
                (pt_a[1] + parent_absolute[1]),
            ),
            (
                (pt_b[0] - pt_a[0]),
                (pt_b[1] - pt_a[1]),
            )
        ),
        5
    )


def draw_track_border(screen, pt_a, pt_b, parent_absolute=(0, 0),
                      color=(255, 0, 0)):
    pygame.draw.line(
        screen, color,
        (
            (pt_a[0] + parent_absolute[0]),
            (pt_a[1] + parent_absolute[1]),
        ),
        (
            (pt_b[0] + parent_absolute[0]),
            (pt_b[1] + parent_absolute[1]),
        ),
        5
    )


class RaceTrack(RelativeGroup):
    def __init__(self, grid_margin=0):
        super().__init__()

        self.tiles = TileGrid(margin=grid_margin)
        self.tiles.parent = self

        self.objects = []
        self.borders = set()  # set of ((pt_a_x, pt_a_y), (pt_b_x, pt_b_y))
        self.crap_area = set()  # set of pygame.Rect

    def draw(self, screen):
        self.tiles.draw(screen)
        super().draw(screen)
        for crap_area in self.crap_area:
            draw_crap_area(screen, crap_area[0], crap_area[1], self.absolute)
        for border in self.borders:
            draw_track_border(screen, border[0], border[1], self.absolute)

    def add_object(self, obj):
        self.objects.append(obj)
        self.add(obj)

    def add_border(self, border):
        self.borders.add(border)

    def add_crap_area(self, crap_area):
        self.crap_area.add(
            (
                (
                    min(crap_area[0][0], crap_area[1][0]),
                    min(crap_area[0][1], crap_area[1][1]),
                ),
                (
                    max(crap_area[0][0], crap_area[1][0]),
                    max(crap_area[0][1], crap_area[1][1]),
                ),
            )
        )
