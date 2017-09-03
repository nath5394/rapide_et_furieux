import logging

import pygame

from .. import RelativeGroup
from .. import RelativeSprite
from ... import assets


logger = logging.getLogger(__name__)


class Tile(RelativeSprite):
    def __init__(self, resource, image=None):
        super().__init__(resource, image)

    def serialize(self):
        return self.resource

    @staticmethod
    def unserialize(data):
        return Tile(data)

    def copy(self):
        return Tile(self.resource, self.original)

    def add_to_racetrack(self, race_track, mouse_position):
        grid_position = race_track.tiles.get_grid_position(mouse_position)
        if grid_position[0] < 0 or grid_position[1] < 0:
            return
        element = self.copy()
        race_track.tiles.set_tile(grid_position, element)


class TileGrid(RelativeGroup):
    LINE_COLOR = (0, 0, 128)

    def __init__(self, margin=0):
        super().__init__()
        self.margin = margin
        self.grid = {}  # (pos_x, pos_y) --> Tile
        self.size = (0, 0)

    def serialize(self):
        return [(k, v.serialize()) for (k, v) in self.grid.items()]

    def unserialize(self, data):
        for sprite in self.sprites():
            self.remove(sprite)
        self.grid = {}
        elements = {}
        for (position, rsc) in data:
            rsc = tuple(rsc)
            position = tuple(position)
            if rsc in elements:
                tile = elements[rsc].copy()
            else:
                elements[rsc] = tile = Tile.unserialize(rsc)
            self.set_tile(position, tile)

    def set_tile(self, position, tile):
        if position in self.grid:
            self.remove(self.grid[position])
        self.grid[position] = tile
        tile.parent = self
        tile.relative = (
            position[0] * assets.TILE_SIZE[0],
            position[1] * assets.TILE_SIZE[1],
        )
        self.add(tile)
        self.size = (
            max(self.size[0], tile.relative[0]),
            max(self.size[1], tile.relative[1]),
        )

    def remove_tile(self, position):
        if position not in self.grid:
            return False
        self.remove(self.grid[position])
        self.grid.pop(position)
        return True

    def draw(self, screen):
        size = screen.get_size()

        absolute = self.absolute
        offset = (
            absolute[0] % assets.TILE_SIZE[0],
            absolute[1] % assets.TILE_SIZE[1],
        )
        if absolute[0] > 0:
            offset = (absolute[0], offset[1])
        if absolute[1] > 0:
            offset = (offset[0], absolute[1])

        # draw grid
        for x in range(offset[0], size[0], assets.TILE_SIZE[0]):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (x - (self.margin / 2), max(0, offset[1])),
                (x - (self.margin / 2), size[1]),
                self.margin
            )
        for y in range(offset[1], size[1], assets.TILE_SIZE[1]):
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
            int((screen_position[0] - pos[0]) / assets.TILE_SIZE[0]),
            int((screen_position[1] - pos[1]) / assets.TILE_SIZE[1]),
        )
