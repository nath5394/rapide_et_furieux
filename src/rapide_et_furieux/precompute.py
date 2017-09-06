#!/usr/bin/env python3

import copy
import itertools
import json
import logging
import queue
import sys
import threading

import pygame

from . import assets
from . import util
from .gfx import ui
from .gfx.cars import ia
from .gfx.racetrack import RaceTrack

RUNNING = True


CAPTION = "Rapide et Furieux {} - Precomputing ...".format(util.VERSION)

BACKGROUND_LAYER = -1
RACE_TRACK_LAYER = 50
WAYPOINTS_LAYER = 100
OSD_LAYER = 250

SCROLLING_BORDER = 10
SCROLLING_SPEED = 512

logger = logging.getLogger(__name__)


class FindAllWaypointsThread(threading.Thread):
    def __init__(self, racetrack, ret_cb):
        super().__init__()
        self.racetrack = racetrack
        self.ret_cb = ret_cb

    def run(self):
        wpts = set()
        for wpt in (
                    ia.Waypoint(
                        position=position,
                        reachable=True,
                    ) for (position, _)
                    in self.racetrack.tiles.get_spawn_points()
                ):
            wpts.add(wpt)

        for wpt in (
                    ia.Waypoint(
                        position=checkpoint.pt,
                        reachable=True,
                    ) for checkpoint in self.racetrack.checkpoints
                ):
            wpts.add(wpt)

        borders = self.racetrack.borders
        print("Computing {} waypoints ...".format(
            len(borders) * (len(borders) - 1)
        ))
        for border_a in borders:
            for border_b in borders:
                if border_a is border_b:
                    continue
                for (pt_a, pt_b) in itertools.product(
                            border_a.pts, border_b.pts
                        ):
                    middle = (
                        int(((pt_b[0] - pt_a[0]) / 2) + pt_a[0]),
                        int(((pt_b[1] - pt_a[1]) / 2) + pt_a[1]),
                    )
                    wpts.add(
                        ia.Waypoint(
                            position=middle,
                            reachable=False,
                        )
                    )
        print("Done")

        util.idle_add(self.ret_cb, wpts)


class DropWaypointsOnBorders(threading.Thread):
    MIN_DISTANCE_FROM_BORDERS = 5

    def __init__(self, racetrack, waypoints, ret_cb):
        super().__init__()
        self.racetrack = racetrack
        self.waypoints = waypoints
        self.ret_cb = ret_cb

    def run(self):
        wpts = self.waypoints
        print("Dropping waypoints on borders ... (starting with {})".format(
            len(wpts)
        ))
        borders = self.racetrack.borders
        m = self.MIN_DISTANCE_FROM_BORDERS ** 2
        for wpt in set(wpts):
            keep = True
            for border in borders:
                # drop all the waypoints on a border
                if wpt.position in border.pts:
                    keep = False
                    break
                # or close to it
                dist = util.distance_sq_pt_to_segment(border.pts, wpt.position)
                if dist < m:
                    keep = False
                    break
            if not keep:
                wpts.remove(wpt)
        print("Done: {} waypoints remaining".format(len(wpts)))
        util.idle_add(self.ret_cb, wpts)


class FindReachableWaypointsThread(threading.Thread):
    MAX_PATHS_BY_PT = 10

    def __init__(self, racetrack, waypoints, ret_cb, update_cb):
        super().__init__()
        self.racetrack = racetrack
        self.waypoints = waypoints
        self.ret_cb = ret_cb
        self.update_cb = update_cb

    def run(self):
        wpts = self.waypoints
        for wpt in wpts:
            wpt.examined = False

        paths = []

        # start points
        to_examine = set()
        for wpt in self.waypoints:
            if wpt.reachable:
                to_examine.add(wpt)

        borders = self.racetrack.borders

        print("Looking for reachable waypoints ...")

        nb_wpts = len(wpts)
        current = 0

        while RUNNING:
            try:
                origin = to_examine.pop()
            except KeyError:
                break
            print("Examining connexions with {} ({}/{})".format(
                origin, current, nb_wpts
            ))

            new_paths = []
            for dest in wpts:
                if origin is dest:
                    continue
                if dest.reachable:  # already examined (or will be soon)
                    continue
                can_reach = True
                for border in borders:
                    intersect_pt = util.get_segment_intersect_point(
                        (origin.position, dest.position),
                        border.pts
                    )
                    if intersect_pt:
                        can_reach = False
                        break
                if not can_reach:
                    continue
                path = ia.Path(origin, dest)
                path.compute_score_length()
                new_paths.append(path)
            print("{} new paths found (max {} kept)".format(
                len(new_paths), self.MAX_PATHS_BY_PT)
            )
            new_paths.sort(key=lambda path: path.score)
            new_paths = new_paths[:self.MAX_PATHS_BY_PT]
            paths += new_paths
            for path in new_paths:
                path.b.reachable = True
                to_examine.add(path.b)
            util.idle_add(self.update_cb, wpts, paths)
            current += 1

        print("Done")
        util.idle_add(self.update_cb, wpts, paths)
        util.idle_add(self.ret_cb, wpts, paths)


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

        self.background = ui.Background()

        fps_counter = ui.FPSCounter(self.font, position=(
            self.screen.get_size()[0] - 128, 0
        ))

        util.register_drawer(OSD_LAYER, self.osd_message)
        util.register_drawer(BACKGROUND_LAYER, self.background)
        util.register_drawer(OSD_LAYER - 1, fps_counter)
        util.register_animator(fps_counter.on_frame)
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
        self.waypoint_drawer = ia.WaypointDrawer()
        self.waypoint_drawer.parent = self.race_track
        util.register_drawer(WAYPOINTS_LAYER, self.waypoint_drawer)
        self.osd_message.show("Done")
        logger.info("Done")

    def on_key(self, event):
        global RUNNING
        if event.type != pygame.KEYDOWN and event.type != pygame.KEYUP:
            return

        if event.key == pygame.K_F1 or event.key == pygame.K_ESCAPE:
            RUNNING = False
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
        t = FindAllWaypointsThread(self.race_track, self.precompute2)
        t.start()

    def precompute2(self, all_waypoints):
        wpts = set(all_waypoints)
        self.waypoint_drawer.set_waypoints(wpts)
        t = DropWaypointsOnBorders(self.race_track, all_waypoints,
                                   self.precompute3)
        t.start()

    def precompute3(self, all_waypoints):
        wpts = all_waypoints
        self.waypoint_drawer.set_waypoints(wpts)

        t = FindReachableWaypointsThread(self.race_track, all_waypoints,
                                         self.precompute4,
                                         self.precompute3_update)
        t.start()

    def precompute3_update(self, all_waypoints, all_paths):
        wpts = all_waypoints
        self.waypoint_drawer.set_waypoints(wpts)
        paths = all_paths
        self.waypoint_drawer.set_paths(paths)

    def precompute4(self, all_waypoints, all_paths):
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
        (1280, 720), pygame.DOUBLEBUF | pygame.HWSURFACE
    )
    pygame.display.set_caption(CAPTION)

    precompute = Precomputing(sys.argv[1], screen)
    precompute.load()
    util.idle_add(precompute.precompute)
    util.main_loop(screen)
