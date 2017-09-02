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


def draw_checkpoint(screen, checkpoint, next_pt=None,
                    parent_absolute=(0, 0), color=(0, 0, 255)):
    # point
    pygame.draw.circle(
        screen, color,
        (
            checkpoint[0] + parent_absolute[0],
            checkpoint[1] + parent_absolute[1],
        ),
        15
    )

    # checkpoint number
    screen.blit(
        checkpoint[2],
        (
            checkpoint[0] + parent_absolute[0] + 20,
            checkpoint[1] + parent_absolute[1] + 20,
        )
    )

    # line to the next checkpoint
    if next_pt is not None and next_pt[:2] != checkpoint[:2]:
        pygame.draw.line(
            screen, color,
            (
                (checkpoint[0] + parent_absolute[0]),
                (checkpoint[1] + parent_absolute[1]),
            ),
            (
                (next_pt[0] + parent_absolute[0]),
                (next_pt[1] + parent_absolute[1]),
            ),
            3
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
    DELETION_MARGIN = 15

    def __init__(self, grid_margin=0):
        super().__init__()

        self.tiles = TileGrid(margin=grid_margin)
        self.tiles.parent = self

        self.objects = []
        self.borders = set()  # set of ((pt_a_x, pt_a_y), (pt_b_x, pt_b_y))
        self.crap_areas = set()  # set of pygame.Rect
        self.checkpoints = []  # list of (pt_x, pt_y, text)

        self.font = pygame.font.Font(None, 42)

    def draw(self, screen):
        self.tiles.draw(screen)
        super().draw(screen)
        absolute = self.absolute
        for crap_area in self.crap_areas:
            draw_crap_area(screen, crap_area[0], crap_area[1], absolute)
        for (idx, checkpoint) in enumerate(self.checkpoints):
            draw_checkpoint(
                screen,
                checkpoint,
                self.checkpoints[idx + 1]
                if idx + 1 < len(self.checkpoints) else self.checkpoints[0],
                absolute)
        for border in self.borders:
            draw_track_border(screen, border[0], border[1], absolute)

    def add_object(self, obj):
        self.objects.append(obj)
        self.add(obj)

    def add_border(self, border):
        self.borders.add(border)

    def add_crap_area(self, crap_area):
        self.crap_areas.add(
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

    def update_checkpoints(self):
        for (idx, checkpoint) in enumerate(list(self.checkpoints)):
            self.checkpoints[idx] = (
                checkpoint[0],
                checkpoint[1],
                self.font.render(str(idx), True, (0, 0, 255))
            )

    def add_checkpoint(self, pt):
        self.checkpoints.append(pt)
        self.update_checkpoints()

    def get_track_border(self, position):
        margin = self.DELETION_MARGIN ** 2
        for border in self.borders:
            for pt in border:
                if abs(
                            ((pt[0] - position[0]) ** 2) +
                            ((pt[1] - position[1]) ** 2)
                        ) <= margin:
                    return border
        return None

    def get_checkpoint(self, position):
        margin = self.DELETION_MARGIN ** 2
        for pt in self.checkpoints:
            if abs(
                        ((pt[0] - position[0]) ** 2) +
                        ((pt[1] - position[1]) ** 2)
                    ) <= margin:
                return pt
        return None

    def get_crap_area(self, position):
        margin = self.DELETION_MARGIN ** 2
        for area in self.crap_areas:
            pts = [
                (
                    min(area[0][0], area[1][0]),
                    min(area[0][1], area[1][1]),
                ),
                (
                    min(area[0][0], area[1][0]),
                    max(area[0][1], area[1][1]),
                ),
                (
                    max(area[0][0], area[1][0]),
                    min(area[0][1], area[1][1]),
                ),
                (
                    max(area[0][0], area[1][0]),
                    max(area[0][1], area[1][1]),
                ),
            ]
            for pt in pts:
                if abs(
                            ((pt[0] - position[0]) ** 2) +
                            ((pt[1] - position[1]) ** 2)
                        ) <= margin:
                    return area
        return None

    def get_object(self, position):
        for obj in self.objects:
            rect = pygame.Rect((obj.relative, obj.size))
            if rect.collidepoint(position):
                return obj
        return None

    def delete(self, mouse_position):
        absolute = self.absolute
        position = (
            mouse_position[0] - absolute[0],
            mouse_position[1] - absolute[1]
        )

        # position matches a checkpoint ?
        el = self.get_checkpoint(position)
        if el is not None:
            logger.info("Removing check point: %s", el)
            self.checkpoints.remove(el)
            self.update_checkpoints()
            return

        # position matches a track border ?
        el = self.get_track_border(position)
        if el is not None:
            logger.info("Removing track border: %s", el)
            self.borders.remove(el)
            return

        # position matches a crap area border ?
        el = self.get_crap_area(position)
        if el is not None:
            logger.info("Removing crap area: %s", el)
            self.crap_areas.remove(el)
            return

        # position matches an object ?
        el = self.get_object(position)
        if el is not None:
            logger.info("Removing object: %s", el)
            self.objects.remove(el)
            self.remove(el)
            return

        # position matches a tile ?
        el = self.tiles.get_grid_position(mouse_position)
        if el is not None:
            logger.info("Removing tile: %s / %s", mouse_position, el)
            if self.tiles.remove_tile(el):
                return

        logger.info("Unable to find element to remove at %s / %s",
                    mouse_position, position)
