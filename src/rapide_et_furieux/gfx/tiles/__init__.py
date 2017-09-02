import logging

import pygame

from .. import RelativeGroup
from .. import RelativeSprite
from ... import assets


logger = logging.getLogger(__name__)


class Tile(RelativeSprite):
    aligned_on_grid = True

    def __init__(self, resource, image=None):
        super().__init__(resource, image)

    def copy(self):
        return Tile(self.resource, self.original)


class TileGrid(RelativeGroup):
    LINE_COLOR = (0, 0, 64)

    def __init__(self, margin=0):
        super().__init__()
        self.margin = margin
        self.grid = {}  # (pos_x, pos_y) --> Tile
        self.size = (0, 0)

    def set_tile(self, position, tile):
        if position in self.grid:
            self.remove(self.grid[position])
        self.grid[position] = tile
        tile.parent = self
        tile.relative = (
            position[0] * (assets.TILE_SIZE[0] + self.margin),
            position[1] * (assets.TILE_SIZE[1] + self.margin),
        )
        logger.info("Adding tile at position %s / %s", position, tile.relative)
        self.add(tile)
        self.size = (
            max(self.size[0], tile.relative[0]),
            max(self.size[1], tile.relative[1]),
        )

    def draw(self, screen):
        self.size = screen.get_size()
        position = self.absolute
        for x in range(
                    position[0], position[0] + self.size[0],
                    assets.TILE_SIZE[0] + self.margin
                ):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (position[0] + x - (self.margin / 2), position[1]),
                (position[0] + x - (self.margin / 2),
                 position[1] + self.size[1]),
                self.margin
            )
        for y in range(
                    position[1], position[1] + self.size[1],
                    assets.TILE_SIZE[1] + self.margin
                ):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (position[0], position[1] + y - (self.margin / 2)),
                (position[0] + self.size[0],
                 position[1] + y - (self.margin / 2)),
                self.margin
            )
        super().draw(screen)

    def get_grid_position(self, screen_position):
        parent_pos = (0, 0)
        if self.parent:
            parent_pos = self.parent.absolute
        return (
            int((screen_position[0] - parent_pos[0]) /
                (assets.TILE_SIZE[0] + self.margin)),
            int((screen_position[1] - parent_pos[1]) /
                (assets.TILE_SIZE[1] + self.margin)),
        )
