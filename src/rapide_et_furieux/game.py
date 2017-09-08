#!/usr/bin/env python3

import itertools
import json
import logging
import os
import sys
import time

import pygame

from . import assets
from . import util
from .gfx import ui
from .gfx.cars.ia import IACar
from .gfx.cars.ia import WaypointManager
from .gfx.cars.player import PlayerCar
from .gfx.racetrack import RaceTrack
from .gfx.racetrack import RaceTrackMiniature


CAPTION = "Rapide et Furieux {}".format(util.VERSION)

BACKGROUND_LAYER = -1
RACE_TRACK_LAYER = 50
RACE_TRACK_MINIATURE_LAYER = 100
OSD_LAYER = 250

COUNTDOWN = 3

logger = logging.getLogger(__name__)


DEBUG = bool(int(os.getenv("DEBUG", "0")))


class Game(object):
    def __init__(self, screen, track_filepath):
        self.screen = screen
        self.track_filepath = track_filepath
        self.screen_size = screen.get_size()
        self.game_settings = util.GAME_SETTINGS_TEMPLATE
        self.game_start = None
        self.countdown = None

        self.font = pygame.font.Font(None, 32)
        self.osd_message = ui.OSDMessage(self.font, 42,
                                         (self.screen_size[0] / 3, 5))
        self.osd_message.show("{} - {}".format(CAPTION, track_filepath))
        if DEBUG:
            util.register_drawer(OSD_LAYER, self.osd_message)

        self.race_track = None
        self.player = None
        self.race_track_miniature = None

        self.background = ui.Background()
        util.register_drawer(BACKGROUND_LAYER, self.background)

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

        util.register_animator(self.track_player_car)

        pygame.mouse.set_visible(False)

        self.osd_message.show("Done")

    def load(self):
        logger.info("Loading '%s' ...", self.track_filepath)
        self.osd_message.show("Loading '%s' ..." % self.track_filepath)
        util.idle_add(self._load)

    def unload(self):
        if self.race_track is not None:
            self.unregister_animator(
                self.race_track.collisions.collisions.precompute_moving
            )
            for car in self.race_track.cars:
                util.unregister_animator(car.move)
            self.unregister_drawer(self.race_track)
            self.race_track = None

    def _load(self):
        assets.load_resources()

        self.unload()

        # load map / race track
        with open(self.track_filepath, 'r') as fd:
            data = json.load(fd)
        self.game_settings.update(data['game_settings'])
        self.race_track = RaceTrack(grid_margin=0, debug=DEBUG,
                                    game_settings=self.game_settings)
        util.register_drawer(RACE_TRACK_LAYER, self.race_track)
        self.race_track.unserialize(data['race_track'])
        self.race_track.collisions.precompute_static()
        self.race_track_miniature = RaceTrackMiniature(self.race_track)
        util.register_drawer(RACE_TRACK_MINIATURE_LAYER,
                             self.race_track_miniature)

        waypoint_mgmt = WaypointManager.unserialize(
            data['ia'], self.game_settings, self.race_track
        )
        waypoint_mgmt.optimize(self.race_track)

        # instantiate cars
        util.register_animator(self.race_track.collisions.precompute_moving)
        tiles = self.race_track.tiles
        iter_car_rsc = iter(itertools.cycle(assets.CARS))
        for (idx, (spawn_point, orientation)) \
                in enumerate(tiles.get_spawn_points()):
            if idx == 0:
                car = PlayerCar(next(iter_car_rsc), self.race_track,
                                self.game_settings, spawn_point, orientation)
            else:
                car = IACar(next(iter_car_rsc), self.race_track,
                            self.game_settings, spawn_point, orientation,
                            waypoint_mgmt=waypoint_mgmt)
            self.race_track.add_car(car)
            util.register_animator(car.move)
            if idx == 0:
                self.player = car

        self.game_start = time.time()
        util.register_animator(self.race_starter)

        self.osd_message.show("Done")
        logger.info("Done")

    def track_player_car(self, frame_interval):
        if not self.player:
            return
        self.race_track.relative = (
            int(self.screen_size[0] / 2 - self.player.position[0]),
            int(self.screen_size[1] / 2 - self.player.position[1]),
        )

    def race_starter(self, frame_interval):
        now = time.time()
        t = now - self.game_start
        if int(t) != self.countdown:
            logger.info("Countdown: {}".format(COUNTDOWN - int(t)))
            self.osd_message.show("{}".format(COUNTDOWN - int(t)))
            self.countdown = int(t)
        if self.countdown == COUNTDOWN:
            self.race_track.start_race()
            util.idle_add(util.unregister_animator, self.race_starter)


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
