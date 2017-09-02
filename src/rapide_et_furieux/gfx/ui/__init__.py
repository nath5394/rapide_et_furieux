from ... import assets


import pygame


class Grid(object):
    LINE_COLOR = (0, 255, 0)

    def __init__(self):
        self.parent = None
        self.relative = (0, 0)
        self.size = assets.TILE_SIZE

    @property
    def absolute(self):
        if self.parent is None:
            parent_abs = (0, 0)
        else:
            parent_abs = self.parent.absolute
        return (
            parent_abs[0] % assets.TILE_SIZE[0],
            parent_abs[1] % assets.TILE_SIZE[1]
        )

    @property
    def rect(self):
        absolute = self.absolute
        return pygame.Rect(
            (absolute[0], absolute[1]),
            self.size
        )

    def draw(self, screen):
        self.size = screen.get_size()
        position = self.absolute
        for x in range(
                    position[0], position[0] + self.size[0], assets.TILE_SIZE[0]
                ):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (position[0] + x, position[1]),
                (position[0] + x, position[1] + self.size[1])
            )
        for y in range(
                    position[1], position[1] + self.size[1], assets.TILE_SIZE[1]
                ):
            pygame.draw.line(
                screen, self.LINE_COLOR,
                (position[0], position[1] + y),
                (position[0] + self.size[0], position[1] + y),
            )
