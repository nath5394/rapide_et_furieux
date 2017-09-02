import logging

from .. import RelativeGroup
from .. import RelativeSprite
from ... import assets
from ... import util
from ..racetrack import CrapArea
from ..racetrack import TrackBorder

import pygame


logger = logging.getLogger(__name__)


class Arrow(RelativeSprite):
    def __init__(self, resource):
        super().__init__(resource)


class Background(object):
    def __init__(self):
        pass

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0),
                         ((0, 0), screen.get_size()))


class ElementSelector(RelativeGroup):
    MARGIN = 5
    COLUMNS = 4

    def __init__(self, elements, screen):
        super().__init__()
        for (idx, element) in enumerate(elements):
            element.relative = (
                (idx % self.COLUMNS) * (assets.TILE_SIZE[0] + self.MARGIN),
                int(idx / self.COLUMNS) * (assets.TILE_SIZE[1] + self.MARGIN)
            )
            element.parent = self
            element.image = element.image.subsurface(
                (
                    (0, 0),
                    (
                        min(element.image.get_size()[0], assets.TILE_SIZE[0]),
                        min(element.image.get_size()[1], assets.TILE_SIZE[1])
                    )
                )
            )
            element.size = element.image.get_size()
        self.add(*elements)

        self.size = (
            self.COLUMNS * (self.MARGIN + assets.TILE_SIZE[0]),
            screen.get_size()[1]
        )

    @property
    def rect(self):
        return pygame.Rect((0, 0), self.size)

    def draw(self, screen):
        pygame.draw.rect(screen, (128, 128, 128), self.rect, 0)
        super().draw(screen)

    def get_element(self, position):
        for element in self.sprites():
            if element.rect.collidepoint(position):
                return element
        return None


class ElementGenerator(RelativeSprite):
    def __init__(self, resource, image=None):
        super().__init__(resource, image)
        self.previous_pt = None
        self.race_track = None
        self.mouse_position = None
        util.register_event_listener(self.get_mouse_position)

    def get_mouse_position(self, event):
        if self.race_track is None:
            return
        mouse_position = pygame.mouse.get_pos()
        self.mouse_position = (
            mouse_position[0] - self.race_track.absolute[0],
            mouse_position[1] - self.race_track.absolute[1],
        )

    def _add_to_racetrack(self, race_track, pt_a, pt_b):
        # implemented by sub-classes
        assert()

    def add_to_racetrack(self, race_track, mouse_position):
        self.race_track = race_track

        absolute = race_track.absolute
        position = (
            mouse_position[0] - absolute[0],
            mouse_position[1] - absolute[1]
        )

        if self.previous_pt is not None:
            self._add_to_racetrack(race_track, self.previous_pt, position)

        self.previous_pt = self.mouse_position = position

    def destroy(self):
        super().destroy()
        self.previous_pt = None


class TrackBorderGenerator(ElementGenerator):
    def __init__(self, image=None):
        super().__init__(assets.RED_LINE, image)

    def copy(self):
        return TrackBorderGenerator(self.image)

    def _add_to_racetrack(self, race_track, pt_a, pt_b):
        race_track.add_border((pt_a, pt_b))

    def draw(self, screen):
        super().draw(screen)
        if self.previous_pt is None:
            return
        TrackBorder.draw_track_border(
            screen, (self.previous_pt, self.mouse_position),
            self.race_track.absolute, color=(128, 0, 0)
        )


class CrapAreaGenerator(ElementGenerator):
    def __init__(self, image=None):
        super().__init__(assets.GREEN_RECT, image)

    def copy(self):
        return CrapAreaGenerator(self.image)

    def _add_to_racetrack(self, race_track, pt_a, pt_b):
        race_track.add_crap_area((pt_a, pt_b))

    def draw(self, screen):
        super().draw(screen)
        if self.previous_pt is None:
            return
        CrapArea.draw_crap_area(screen, self.previous_pt, self.mouse_position,
                                self.race_track.absolute, color=(0, 128, 0))


class CheckpointGenerator(ElementGenerator):
    def __init__(self, image=None):
        super().__init__(assets.BLUE_DOT, image)

    def copy(self):
        return CheckpointGenerator(self.image)

    def add_to_racetrack(self, race_track, mouse_position):
        absolute = race_track.absolute
        position = (
            mouse_position[0] - absolute[0],
            mouse_position[1] - absolute[1]
        )
        race_track.add_checkpoint(position)
