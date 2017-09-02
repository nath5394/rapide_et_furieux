import logging

import pygame

from .. import RelativeGroup
from .. import RelativeSprite
from ... import assets


logger = logging.getLogger(__name__)


class Tile(RelativeSprite):
    fixed_position = True

    def __init__(self, resource, image=None):
        super().__init__(resource, image)

    def copy(self):
        return Tile(self.resource, self.image)


class TileSelector(RelativeGroup):
    MARGIN = 5
    COLUMNS = 4

    def __init__(self, tiles, screen):
        super().__init__()
        for (idx, tile) in enumerate(tiles):
            tile.relative = (
                (idx % self.COLUMNS) * (assets.TILE_SIZE[0] + self.MARGIN),
                int(idx / self.COLUMNS) * (assets.TILE_SIZE[1] + self.MARGIN)
            )
            tile.parent = self
        self.add(*tiles)

        self.size = (
            self.COLUMNS * (self.MARGIN + assets.TILE_SIZE[0]),
            screen.get_size()[1]
        )

    @property
    def rect(self):
        return ((0, 0), self.size)

    def draw(self, screen):
        pygame.draw.rect(screen, (128, 128, 128), self.rect, 0)
        super().draw(screen)

    def get_element(self, position):
        for element in self.sprites():
            if element.rect.collidepoint(position):
                return element
        return None


class TileGrid(RelativeGroup):
    MARGIN = 5
    LINE_COLOR = (0, 0, 64)

    def __init__(self):
        super().__init__()
        self.grid = {}  # (pos_x, pos_y) --> Tile
        self.size = (0, 0)


    def set_tile(self, position, tile):
        tile = tile.copy()
        if position in self.grid:
            self.remove(self.grid[position])
        self.grid[position] = tile
        tile.parent = self
        tile.relative = (
            position[0] * (assets.TILE_SIZE[0] + self.MARGIN),
            position[1] * (assets.TILE_SIZE[1] + self.MARGIN),
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
                    assets.TILE_SIZE[0] + self.MARGIN
                ):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (position[0] + x - (self.MARGIN / 2), position[1]),
                (position[0] + x - (self.MARGIN / 2),
                 position[1] + self.size[1]),
                self.MARGIN
            )
        for y in range(
                    position[1], position[1] + self.size[1],
                    assets.TILE_SIZE[1] + self.MARGIN
                ):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (position[0], position[1] + y - (self.MARGIN / 2)),
                (position[0] + self.size[0],
                 position[1] + y - (self.MARGIN / 2)),
                self.MARGIN
            )
        super().draw(screen)

    def get_grid_position(self, screen_position):
        parent_pos = (0, 0)
        if self.parent:
            parent_pos = self.parent.absolute
        return (
            int((screen_position[0] - parent_pos[0]) /
                (assets.TILE_SIZE[0] + self.MARGIN)),
            int((screen_position[1] - parent_pos[1]) /
                (assets.TILE_SIZE[1] + self.MARGIN)),
        )
