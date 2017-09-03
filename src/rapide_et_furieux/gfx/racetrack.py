import logging

import pygame

from . import RelativeGroup
from .objects import RaceTrackObject
from .tiles import TileGrid


logger = logging.getLogger(__name__)

SELECTION_MARGIN = 15 ** 2


class CrapArea(object):
    COLOR = (0, 255, 0)

    def __init__(self, parent, pts):
        self.parent = parent
        self.pt_a = (
            min(pts[0][0], pts[1][0]),
            min(pts[0][1], pts[1][1])
        )
        self.pt_b = (
            max(pts[0][0], pts[1][0]),
            max(pts[0][1], pts[1][1])
        )

    def serialize(self):
        return {
            'a': self.pt_a,
            'b': self.pt_b,
        }

    @staticmethod
    def unserialize(data, parent):
        return CrapArea(parent, (data['a'], data['b']))

    def draw(self, screen):
        self.draw_crap_area(screen, self.pt_a, self.pt_b, self.parent.absolute,
                            self.COLOR)

    @staticmethod
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

    def __hash__(self):
        return hash(self.pt_a) ^ hash(self.pt_b)

    def matches(self, position):
        pts = [
            (
                min(self.pt_a[0], self.pt_b[0]),
                min(self.pt_a[1], self.pt_b[1]),
            ),
            (
                min(self.pt_a[0], self.pt_b[0]),
                max(self.pt_a[1], self.pt_b[1]),
            ),
            (
                max(self.pt_a[0], self.pt_b[0]),
                min(self.pt_a[1], self.pt_b[1]),
            ),
            (
                max(self.pt_a[0], self.pt_b[0]),
                max(self.pt_a[1], self.pt_b[1]),
            ),
        ]
        for pt in pts:
            if abs(
                        ((pt[0] - position[0]) ** 2) +
                        ((pt[1] - position[1]) ** 2)
                    ) <= SELECTION_MARGIN:
                return True
        return False


class Checkpoint(object):
    COLOR = (64, 64, 255)

    def __init__(self, parent, font, pt, idx):
        self.parent = parent
        self.pt = pt
        self.idx = idx
        self.txt = font.render(str(idx), True, self.COLOR)
        self.next_checkpoint = None

    def serialize(self):
        return {
            'pt': self.pt,
            'idx': self.idx,
        }

    @staticmethod
    def unserialize(data, parent, font):
        return Checkpoint(parent, font, data['pt'], data['idx'])

    def set_idx(self, font, idx):
        self.idx = idx
        self.txt = font.render(str(idx), True, self.COLOR)

    def draw(self, screen):
        self.draw_checkpoint(screen, self.pt, self.txt,
                             self.next_checkpoint.pt
                             if self.next_checkpoint is not None else None,
                             self.parent.absolute, self.COLOR)

    @staticmethod
    def draw_checkpoint(screen, pt, txt, next_pt=None,
                        parent_absolute=(0, 0), color=(0, 0, 255)):
        # point
        pygame.draw.circle(
            screen, color,
            (
                pt[0] + parent_absolute[0],
                pt[1] + parent_absolute[1],
            ),
            15
        )

        # checkpoint number
        screen.blit(
            txt,
            (
                pt[0] + parent_absolute[0] + 20,
                pt[1] + parent_absolute[1] + 20,
            )
        )

        # line to the next checkpoint
        if next_pt is not None and next_pt != pt:
            pygame.draw.line(
                screen, color,
                (
                    (pt[0] + parent_absolute[0]),
                    (pt[1] + parent_absolute[1]),
                ),
                (
                    (next_pt[0] + parent_absolute[0]),
                    (next_pt[1] + parent_absolute[1]),
                ),
                3
            )

    def matches(self, pt):
        return abs(
            ((pt[0] - self.pt[0]) ** 2) +
            ((pt[1] - self.pt[1]) ** 2)
        ) <= SELECTION_MARGIN


class TrackBorder(object):
    COLOR = (255, 0, 0)

    def __init__(self, parent, pts):
        self.parent = parent
        self.pts = pts

    def serialize(self):
        return {
            'pts': self.pts,
        }

    @staticmethod
    def unserialize(data, parent):
        return TrackBorder(parent, data['pts'])

    def draw(self, screen):
        self.draw_track_border(screen, self.pts,
                               self.parent.absolute, self.COLOR)

    @staticmethod
    def draw_track_border(screen, pts, parent_absolute=(0, 0),
                          color=(255, 0, 0)):
        pygame.draw.line(
            screen, color,
            (
                (pts[0][0] + parent_absolute[0]),
                (pts[0][1] + parent_absolute[1]),
            ),
            (
                (pts[1][0] + parent_absolute[0]),
                (pts[1][1] + parent_absolute[1]),
            ),
            5
        )

    def matches(self, position):
        for pt in self.pts:
            if abs(
                        ((pt[0] - position[0]) ** 2) +
                        ((pt[1] - position[1]) ** 2)
                    ) <= SELECTION_MARGIN:
                return True
        return False


class RaceTrack(RelativeGroup):
    DELETION_MARGIN = 15

    def __init__(self, grid_margin=0, debug=False):
        super().__init__()

        self.debug = debug

        self.tiles = TileGrid(margin=grid_margin)
        self.tiles.parent = self

        self.objects = []
        self.borders = []
        self.crap_areas = []
        self.checkpoints = []

        self.font = pygame.font.Font(None, 42)

    def draw(self, screen):
        self.tiles.draw(screen)
        super().draw(screen)

        if self.debug:
            to_draw = [
                self.objects,
                self.borders,
                self.crap_areas,
                self.checkpoints,
            ]
        else:
            to_draw = [
                self.objects,
            ]

        for el_list in to_draw:
            for el in el_list:
                el.draw(screen)

    def add_object(self, obj):
        self.objects.append(obj)

    def add_border(self, border):
        if not isinstance(border, TrackBorder):
            border = TrackBorder(self, border)
        self.borders.append(border)

    def add_crap_area(self, crap_area):
        if not isinstance(crap_area, CrapArea):
            crap_area = CrapArea(self, crap_area)
        self.crap_areas.append(crap_area)

    def update_checkpoints(self):
        for (idx, checkpoint) in enumerate(self.checkpoints):
            self.checkpoints[idx].set_idx(self.font, idx)
            if idx + 1 < len(self.checkpoints):
                self.checkpoints[idx].next_checkpoint = \
                    self.checkpoints[idx + 1]
            else:
                self.checkpoints[idx].next_checkpoint = self.checkpoints[0]

    def add_checkpoint(self, pt):
        if not isinstance(pt, Checkpoint):
            pt = Checkpoint(self, self.font, pt, len(self.checkpoints))
        self.checkpoints.append(pt)
        self.update_checkpoints()

    def get_track_border(self, position):
        for border in self.borders:
            if border.matches(position):
                return border
        return None

    def get_checkpoint(self, position):
        for pt in self.checkpoints:
            if pt.matches(position):
                return pt
        return None

    def get_crap_area(self, position):
        for area in self.crap_areas:
            if area.matches(position):
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
            return

        # position matches a tile ?
        el = self.tiles.get_grid_position(mouse_position)
        if el is not None:
            logger.info("Removing tile: %s / %s", mouse_position, el)
            if self.tiles.remove_tile(el):
                return

        logger.info("Unable to find element to remove at %s / %s",
                    mouse_position, position)

    def serialize(self):
        return {
            'tiles': self.tiles.serialize(),
            'objects': [obj.serialize() for obj in self.objects],
            'borders': [border.serialize() for border in self.borders],
            'crap_areas': [area.serialize() for area in self.crap_areas],
            'checkpoints': [cp.serialize() for cp in self.checkpoints],
        }

    def unserialize(self, data):
        # cleanup
        for sprite in self.sprites():
            self.remove(sprite)
        self.objects = []
        self.borders = []
        self.crap_areas = []
        self.checkpoints = []

        # loading
        self.tiles.unserialize(data['tiles'])
        for obj in data['objects']:
            self.add_object(RaceTrackObject.unserialize(obj, self))
        for border in data['borders']:
            self.add_border(TrackBorder.unserialize(border, self))
        for area in data['crap_areas']:
            self.add_crap_area(CrapArea.unserialize(area, self))
        for cp in data['checkpoints']:
            self.add_checkpoint(Checkpoint.unserialize(cp, self, self.font))
