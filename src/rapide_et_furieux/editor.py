#!/usr/bin/env python3

import json
import logging
import os
import sys

import pygame

from . import assets
from . import util
from .gfx import ui
from .gfx.objects import RaceTrackObject
from .gfx.racetrack import RaceTrack
from .gfx.tiles import Tile


CAPTION = "Rapide et Furieux - Level editor"

BACKGROUND_LAYER = -1
ELEMENT_SELECTOR_LAYER = 100
ELEMENT_SELECTOR_ARROWS_LAYER = 150
RACE_TRACK_LAYER = 50
MOUSE_CURSOR_LAYER = 500
OSD_LAYER = 250

SCROLLING_BORDER = 10
SCROLLING_SPEED = 512

logger = logging.getLogger(__name__)


class Editor(object):
    def __init__(self, screen, file_path):
        self.screen = screen
        self.file_path = file_path
        self.screen_size = screen.get_size()

        self.game_settings = {
            # default values
            'background_color': (0, 0, 0),
            'acceleration': {
                'normal': 256,
                'crap': 64,
            },
            'max_speed': {
                'normal': 512,
                'crap': 256,
            },
        }

        elements = []
        elements += [
            ui.TrackBorderGenerator(),
            ui.CrapAreaGenerator(),
            ui.CheckpointGenerator(),
        ]
        elements += [Tile(tile_rsc) for tile_rsc in assets.TILES]
        elements += [
            RaceTrackObject(obj_rsc, -angle)
            for obj_rsc in assets.OBJECTS
            for angle in [0, 90, 180, 270]
        ]
        elements += [
            RaceTrackObject(obj_rsc, -angle)
            for obj_rsc in assets.CARS
            for angle in [0, 90, 180, 270]
        ]
        elements += [
            RaceTrackObject(obj_rsc, -angle)
            for obj_rsc in assets.MOTORCYCLES
            for angle in [0, 90, 180, 270]
        ]
        elements += [
            RaceTrackObject(obj_rsc, -angle)
            for obj_rsc in assets.POWERUPS
            for angle in [0, 90, 180, 270]
        ]
        elements += [
            RaceTrackObject(obj_rsc, -angle)
            for explosion in assets.EXPLOSIONS
            for obj_rsc in explosion
            for angle in [0, 90, 180, 270]
        ]

        font = pygame.font.Font(None, 32)

        self.element_selector = ui.ElementSelector(elements, screen)
        self.osd_message = ui.OSDMessage(
            font, 42, (self.element_selector.size[0] + 10, 10)
        )
        self.osd_message.show("{} - {}".format(CAPTION, file_path))
        util.register_drawer(OSD_LAYER, self.osd_message)

        fps_counter = ui.FPSCounter(font, position=(
            screen.get_size()[0] - 128, 0
        ))
        util.register_drawer(OSD_LAYER - 1, fps_counter)
        util.register_animator(fps_counter.on_frame)

        self.selected = None

        self.arrow_up = ui.Arrow(assets.ARROW_UP)
        self.arrow_up.relative = (
            (self.element_selector.size[0] / 2) - (self.arrow_up.size[0] / 2),
            0
        )
        self.arrow_down = ui.Arrow(assets.ARROW_DOWN)
        self.arrow_down.relative = (
            (self.element_selector.size[0] / 2) - (self.arrow_down.size[0] / 2),
            self.screen_size[1] - self.arrow_down.size[1]
        )

        element_offset = assets.TILE_SIZE[1]
        self.element_selector_controls = [
            (self.arrow_down, -element_offset, 5),
            (self.arrow_up, element_offset, 4),
        ]

        self.race_track = RaceTrack(grid_margin=5)
        self.race_track.relative = (self.element_selector.size[0], 0)

        self.scrolling = (0, 0)

        util.register_drawer(BACKGROUND_LAYER, ui.Background())
        util.register_drawer(ELEMENT_SELECTOR_LAYER, self.element_selector)
        for (control, offset, button) in self.element_selector_controls:
            util.register_drawer(ELEMENT_SELECTOR_ARROWS_LAYER, control)
        util.register_drawer(RACE_TRACK_LAYER, self.race_track)
        util.register_event_listener(self.on_click)
        util.register_event_listener(self.on_key)
        util.register_event_listener(self.on_mouse_motion)
        util.register_animator(self.scroll)

    def load(self):
        logger.info("Loading '%s' ...", self.file_path)
        self.osd_message.show("Loading '%s' ..." % self.file_path)
        util.idle_add(self._load)

    def _load(self):
        with open(self.file_path, 'r') as fd:
            data = json.load(fd)
        self.game_settings = data['game_settings']
        self.race_track.unserialize(data['race_track'])
        logger.info("Done")
        self.osd_message.show("Done")

    def save(self):
        logger.info("Writing '%s' ...", self.file_path)
        self.osd_message.show("Writing '%s' ..." % self.file_path)
        util.idle_add(self._save)

    def _save(self):
        data = {
            'game_settings': self.game_settings,
            'race_track': self.race_track.serialize()
        }
        with open(self.file_path, 'w') as fd:
            json.dump(data, fd, indent=4, sort_keys=True)
        logger.info("Done")
        self.osd_message.show("Done")

    def on_key(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_F1 or event.key == pygame.K_ESCAPE:
            self.save()
            return
        elif event.key == pygame.K_F5:
            self.load()
            return

    def on_click(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        position = pygame.mouse.get_pos()

        # right click ? --> cancel current
        if event.button == 3:
            if self.selected:
                util.unregister_drawer(self.selected)
                self.selected.destroy()
                self.selected = None
            return

        # middle click ? --> delete element
        if event.button == 2:
            self.race_track.delete(position)
            return

        # control ?
        for (control, offset, mouse_button) in self.element_selector_controls:
            if (mouse_button == event.button or
                    control.rect.collidepoint(position)):
                self.element_selector.relative = (
                    self.element_selector.relative[0],
                    min(0, self.element_selector.relative[1] + offset)
                )
                return

        if event.button != 1:
            return

        # Element selected ?
        selected = self.element_selector.get_element(position)
        if selected is not None:
            if self.selected:
                util.unregister_drawer(self.selected)
                self.selected.destroy()
            self.selected = selected.copy()
            self.selected.relative = position
            util.register_drawer(MOUSE_CURSOR_LAYER, self.selected)
            logger.info("Selected: %s", self.selected)
            return

        if self.selected is None:
            return

        # place the selected element on the race track
        self.selected.add_to_racetrack(self.race_track, position)

    def on_mouse_motion(self, event):
        if event.type != pygame.MOUSEMOTION:
            return

        position = pygame.mouse.get_pos()
        self.scrolling = (0, 0)
        if position[0] < SCROLLING_BORDER:
            self.scrolling = (-SCROLLING_SPEED, self.scrolling[1])
        elif position[0] >= self.screen_size[0] - SCROLLING_BORDER:
            self.scrolling = (SCROLLING_SPEED, self.scrolling[1])
        if position[1] < SCROLLING_BORDER:
            self.scrolling = (self.scrolling[0], -SCROLLING_SPEED)
        elif position[1] >= self.screen_size[1] - SCROLLING_BORDER:
            self.scrolling = (self.scrolling[1], SCROLLING_SPEED)

        if self.selected is None:
            return
        self.selected.relative = position

    def scroll(self, frame_interval):
        self.race_track.relative = (
            int(self.race_track.relative[0] -
                (self.scrolling[0] * frame_interval)),
            int(self.race_track.relative[1] -
                (self.scrolling[1] * frame_interval)),
        )


def on_uncatched_exception_cb(exc_type, exc_value, exc_tb):
    logger.error(
        "=== UNCATCHED EXCEPTION ===",
        exc_info=(exc_type, exc_value, exc_tb)
    )
    logger.error(
        "==========================="
    )


def main():
    lg = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)-6s %(name)-30s %(message)s')
    handler.setFormatter(formatter)
    lg.addHandler(handler)
    sys.excepthook = on_uncatched_exception_cb
    logging.getLogger().setLevel(logging.DEBUG)

    logger.info(CAPTION)

    if len(sys.argv) != 2 or sys.argv[1][0] == "-":
        print("Usage: {} <file>".format(sys.argv[0]))
        sys.exit(1)

    logger.info("Loading ...")
    pygame.init()
    screen = util.set_default_resolution()
    pygame.display.set_caption(CAPTION)

    editor = Editor(screen, sys.argv[1])
    if os.path.exists(sys.argv[1]):
        editor.load()

    util.main_loop(screen)
