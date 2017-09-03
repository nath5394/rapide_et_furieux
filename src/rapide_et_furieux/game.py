#!/usr/bin/env python3

import json
import logging
import os
import sys

import pygame

from . import assets
from . import util
from .gfx import ui
from .gfx.racetrack import RaceTrack


CAPTION = "Rapide et Furieux {}".format(util.VERSION)

BACKGROUND_LAYER = -1
RACE_TRACK_LAYER = 50
OSD_LAYER = 250

logger = logging.getLogger(__name__)


DEBUG = bool(int(os.getenv("DEBUG", "0")))


class Game(object):
    def __init__(self, screen, track_filepath):
        self.screen = screen
        self.track_filepath = track_filepath
        self.screen_size = screen.get_size()
        self.game_settings = util.GAME_SETTINGS_TEMPLATE

        self.font = pygame.font.Font(None, 32)
        self.osd_message = ui.OSDMessage(self.font, 42,
                                         (self.screen_size[0] / 3, 5))
        self.osd_message.show("{} - {}".format(CAPTION, track_filepath))
        if DEBUG:
            util.register_drawer(OSD_LAYER, self.osd_message)

        self.background = None
        self.race_track = None

        logger.info("Initializing ...")
        self.osd_message.show("Initializing ...")
        util.idle_add(self._init)

    def _init(self):
        assets.load_resources()

        if DEBUG:
            fps_counter = ui.FPSCounter(self.font, position=(
                self.screen.get_size()[0] - 128, 0
            ))
            util.register_drawer(OSD_LAYER - 1, fps_counter)
            util.register_animator(fps_counter.on_frame)

        self.background = ui.Background()
        self.race_track = RaceTrack(grid_margin=0, debug=DEBUG)

        util.register_drawer(RACE_TRACK_LAYER, self.race_track)

        self.osd_message.show("Done")

    def load(self):
        logger.info("Loading '%s' ...", self.track_filepath)
        self.osd_message.show("Loading '%s' ..." % self.track_filepath)
        util.idle_add(self._load)

    def _load(self):
        assets.load_resources()
        with open(self.track_filepath, 'r') as fd:
            data = json.load(fd)
        self.game_settings = data['game_settings']
        self.race_track.unserialize(data['race_track'])
        logger.info("Done")
        self.osd_message.show("Done")


def main():
    util.init_logging()

    logger.info(CAPTION)

    if len(sys.argv) != 2 or sys.argv[1][0] == "-":
        print("Usage: {} <file>".format(sys.argv[0]))
        sys.exit(1)

    logger.info("Loading ...")
    pygame.init()
    screen = util.set_default_resolution()
    pygame.display.set_caption(CAPTION)

    game = Game(screen, sys.argv[1])
    util.idle_add(game.load)

    util.main_loop(screen)
