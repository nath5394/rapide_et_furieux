#!/usr/bin/env python3

import json
import logging
import sys

import pygame

from . import assets
from . import util
from .gfx import ui
from .gfx.racetrack import RaceTrack

CAPTION = "Rapide et Furieux {} - Precomputing ...".format(util.VERSION)

BACKGROUND_LAYER = -1
RACE_TRACK_LAYER = 50
OSD_LAYER = 250

SCROLLING_BORDER = 10
SCROLLING_SPEED = 512

logger = logging.getLogger(__name__)


class Precomputing(object):
    def __init__(self, filepath, screen):
        self.filepath = filepath
        self.race_track = None
        self.screen = screen
        self.screen_size = screen.get_size()
        self.scrolling = (0, 0)

        self.font = pygame.font.Font(None, 32)
        self.osd_message = ui.OSDMessage(self.font, 42, (5, 5))
        self.osd_message.show("{} - {}".format(CAPTION, filepath))
        util.register_drawer(OSD_LAYER, self.osd_message)

        self.background = ui.Background()
        util.register_drawer(BACKGROUND_LAYER, self.background)

        util.register_event_listener(self.on_key)
        util.register_event_listener(self.on_mouse_motion)
        util.register_animator(self.scroll)

    def load(self):
        logger.info("Loading '%s' ...", self.filepath)
        self.osd_message.show("Loading '%s' ..." % self.filepath)
        util.idle_add(self._load)

    def _load(self):
        assets.load_resources()
        with open(self.filepath, 'r') as fd:
            data = json.load(fd)
        game_settings = util.GAME_SETTINGS_TEMPLATE
        game_settings.update(data['game_settings'])
        self.race_track = RaceTrack(grid_margin=0, debug=True,
                                    game_settings=game_settings)
        self.race_track.unserialize(data['race_track'])
        util.register_drawer(RACE_TRACK_LAYER, self.race_track)
        self.osd_message.show("Done")
        logger.info("Done")

    def on_key(self, event):
        if event.type != pygame.KEYDOWN and event.type != pygame.KEYUP:
            return

        if event.key == pygame.K_F1 or event.key == pygame.K_ESCAPE:
            self.save()
            return

        keys = pygame.key.get_pressed()
        self.scrolling = (0, 0)
        up = (
            bool(keys[pygame.K_UP]) or bool(keys[pygame.K_w]) or
            bool(keys[pygame.K_KP8])
        )
        down = (
            bool(keys[pygame.K_DOWN]) or bool(keys[pygame.K_s]) or
            bool(keys[pygame.K_KP1])
        )
        left = (
            bool(keys[pygame.K_LEFT]) or bool(keys[pygame.K_a]) or
            bool(keys[pygame.K_KP4])
        )
        right = (
            bool(keys[pygame.K_RIGHT]) or bool(keys[pygame.K_d]) or
            bool(keys[pygame.K_KP6])
        )
        if left:
            self.scrolling = (-SCROLLING_SPEED, self.scrolling[1])
        if right:
            self.scrolling = (SCROLLING_SPEED, self.scrolling[1])
        if up:
            self.scrolling = (self.scrolling[0], -SCROLLING_SPEED)
        if down:
            self.scrolling = (self.scrolling[1], SCROLLING_SPEED)

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

    def scroll(self, frame_interval):
        if self.race_track is None:
            return
        self.race_track.relative = (
            int(self.race_track.relative[0] -
                (self.scrolling[0] * frame_interval)),
            int(self.race_track.relative[1] -
                (self.scrolling[1] * frame_interval)),
        )

    def precompute(self):
        pass

    def save(self):
        pass


def main():
    util.init_logging()

    if len(sys.argv) != 2 or sys.argv[1][0] == "-":
        print("Usage: {} <file>".format(sys.argv[0]))
        sys.exit(1)

    logger.info("Loading ...")
    pygame.init()
    screen = pygame.display.set_mode(
        (1024, 768), pygame.DOUBLEBUF | pygame.HWSURFACE
    )
    pygame.display.set_caption(CAPTION)

    precompute = Precomputing(sys.argv[1], screen)
    precompute.load()
    util.idle_add(precompute.precompute)
    util.main_loop(screen)
