import pygame

from .. import RelativeGroup
from .. import RelativeSprite
from ... import assets


class Tile(RelativeSprite):
    def __init__(self, resource):
        super().__init__(resource)

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
