import logging

import pygame

from .. import RelativeGroup
from .. import RelativeSprite
from ... import assets


logger = logging.getLogger(__name__)


class Tile(RelativeSprite):
    def __init__(self, resource, image=None):
        super().__init__(resource, image)

    def copy(self):
        return Tile(self.resource, self.original)

    def add_to_racetrack(self, race_track, mouse_position):
        grid_position = race_track.tiles.get_grid_position(mouse_position)
        if grid_position[0] < 0 or grid_position[1] < 0:
            return
        element = self.copy()
        race_track.tiles.set_tile(grid_position, element)

    def remove_from_racetrack(self, race_track, mouse_position):
        # TODO
        pass


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
        size = screen.get_size()

        absolute = self.absolute
        offset = (
            absolute[0] % (assets.TILE_SIZE[0] + self.margin),
            absolute[1] % (assets.TILE_SIZE[1] + self.margin),
        )
        if absolute[0] > 0:
            offset = (absolute[0], offset[1])
        if absolute[1] > 0:
            offset = (offset[0], absolute[1])

        # draw grid
        for x in range(offset[0], size[0], assets.TILE_SIZE[0] + self.margin):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (x - (self.margin / 2), max(0, offset[1])),
                (x - (self.margin / 2), size[1]),
                self.margin
            )
        for y in range(offset[1], size[1], assets.TILE_SIZE[1] + self.margin):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (max(0, offset[0]), y - (self.margin / 2)),
                (size[0], y - (self.margin / 2)),
                self.margin
            )

        super().draw(screen)

    def get_grid_position(self, screen_position):
        pos = self.absolute
        return (
            int((screen_position[0] - pos[0]) /
                (assets.TILE_SIZE[0] + self.margin)),
            int((screen_position[1] - pos[1]) /
                (assets.TILE_SIZE[1] + self.margin)),
        )
