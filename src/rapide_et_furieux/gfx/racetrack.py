import logging

from . import RelativeGroup

from .tiles import TileGrid


logger = logging.getLogger(__name__)


class RaceTrack(RelativeGroup):
    def __init__(self, grid_margin=0):
        super().__init__()

        self.tiles = TileGrid(margin=grid_margin)
        self.tiles.parent = self

        self.objects = []

    def add_element(self, mouse_position, element):
        element = element.copy()
        if element.aligned_on_grid:
            grid_position = self.tiles.get_grid_position(mouse_position)
            if grid_position[0] < 0 or grid_position[1] < 0:
                return
            self.tiles.set_tile(grid_position, element)
        else:
            abs_pos = self.absolute
            position = (
                mouse_position[0] - abs_pos[0],
                mouse_position[1] - abs_pos[1]
            )
            if position[0] < 0 or position[1] < 0:
                return
            element.parent = self
            element.relative = position
            logger.info("Adding static object: %s --> %s",
                        mouse_position, element.relative)
            self.objects.append((
                element.relative, element.size, element
            ))
            self.add(element)

    def draw(self, screen):
        self.tiles.draw(screen)
        super().draw(screen)
