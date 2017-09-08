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
        self.grid_min = (0xFFFFFFFF, 0xFFFFFFFF)
        self.grid_max = (-1, -1)

    def serialize(self):
        return [(k, v.serialize()) for (k, v) in self.grid.items()]

    def unserialize(self, data):
        self.grid = {}
        self.grid_min = (0xFFFFFFFF, 0xFFFFFFFF)
        self.grid_max = (-1, -1)

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
        self.grid[position] = tile
        tile.parent = self
        tile.relative = (
            position[0] * assets.TILE_SIZE[0],
            position[1] * assets.TILE_SIZE[1],
        )

        self.size = (
            max(self.size[0], tile.relative[0]),
            max(self.size[1], tile.relative[1]),
        )

        self._update_minmax(position)

    def _update_minmax(self, position):
        (grid_min_x, grid_min_y) = self.grid_min
        (grid_max_x, grid_max_y) = self.grid_max
        if grid_min_x > position[0]:
            grid_min_x = position[0]
        if grid_min_y > position[1]:
            grid_min_y = position[1]
        if grid_max_x < position[0]:
            grid_max_x = position[0]
        if grid_max_y < position[1]:
            grid_max_y = position[1]
        self.grid_min = (grid_min_x, grid_min_y)
        self.grid_max = (grid_max_x, grid_max_y)


    def remove_tile(self, position):
        if position not in self.grid:
            return False
        self.grid.pop(position)

        if (position[0] == self.grid_min[0] or
                position[1] == self.grid_min[1] or
                position[0] == self.grid_max[0] or
                position[1] == self.grid_max[1]):
            self.grid_min = (0xFFFFFFFF, 0xFFFFFFFF)
            self.grid_max = (-1, -1)
            for position in self.grid:
                self._update_minmax(position)

        return True

    def draw(self, screen, parent=None, grid=True):
        size = screen.get_size()

        absolute = self.get_absolute(
            parent if parent is not None else self.parent
        )
        offset = (
            absolute[0] % assets.TILE_SIZE[0],
            absolute[1] % assets.TILE_SIZE[1],
        )
        if absolute[0] > 0:
            offset = (absolute[0], offset[1])
        if absolute[1] > 0:
            offset = (offset[0], absolute[1])

        # draw grid
        if grid:
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

        # draw tiles
        for x in range(int(-(absolute[0] / assets.TILE_SIZE[0])),
                       int(-(absolute[0] / assets.TILE_SIZE[0])) +
                       int(size[0] / assets.TILE_SIZE[0]) + 2):
            for y in range(int(-(absolute[1] / assets.TILE_SIZE[1])),
                           int(-(absolute[1] / assets.TILE_SIZE[1])) +
                           int(size[1] / assets.TILE_SIZE[1]) + 2):
                grid_pos = (x, y)
                if grid_pos not in self.grid:
                    continue
                tile = self.grid[grid_pos]
                tile.draw(screen, parent)

        super().draw(screen, parent)

    def get_grid_position(self, screen_position):
        pos = self.absolute
        return (
            int((screen_position[0] - pos[0]) / assets.TILE_SIZE[0]),
            int((screen_position[1] - pos[1]) / assets.TILE_SIZE[1]),
        )

    def get_spawn_points(self):
        for (position, tile) in self.grid.items():
            if tile.resource not in assets.SPAWN_TILES:
                continue
            angle = assets.SPAWN_TILES[tile.resource]
            yield (
                (
                    (position[0] * assets.TILE_SIZE[0]) +
                    (assets.TILE_SIZE[0] / 2),
                    (position[1] * assets.TILE_SIZE[1]) +
                    (assets.TILE_SIZE[1] / 2),
                ),
                angle
            )
