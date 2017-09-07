#!/usr/bin/env python3

import itertools
import json
import logging
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

MIN_DISTANCE_FROM_BORDERS = assets.TILE_SIZE[0] / 2
MIN_DISTANCE_FROM_WAYPOINTS = assets.TILE_SIZE[0] / 4
MIN_DISTANCE_FROM_PATHS = assets.TILE_SIZE[0] / 8


class FindAllWaypointsThread(threading.Thread):
    def __init__(self, racetrack, ret_cb):
        super().__init__()
        self.racetrack = racetrack
        self.ret_cb = ret_cb

    @staticmethod
    def add_extra_points(pts):
        pts.append(
            (
                ((pts[1][0] - pts[0][0]) / 2) + pts[0][0],
                ((pts[1][1] - pts[0][1]) / 2) + pts[0][1],
            )
        )
        return pts

    def run(self):
        wpts = set()
        for (spawn, _) in self.racetrack.tiles.get_spawn_points():
            wpt =ia.Waypoint(
                position=spawn,
                reachable=True,
            )
            wpt.checkpoint = True  # just to keep them alive
            wpts.add(wpt)

        for cp in self.racetrack.checkpoints:
            wpt = ia.Waypoint(
                position=cp.pt,
                reachable=True,
            )
            wpt.checkpoint = cp
            wpts.add(wpt)

        borders = [
            self.add_extra_points(border.pts)
            for border in self.racetrack.borders
        ]
        print("Computing possible waypoints ...")
        for border_a in borders:
            for border_b in borders:
                if border_a is border_b:
                    continue
                for (pt_a, pt_b) in itertools.product(
                            border_a, border_b
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
        print("Found {} possible points".format(len(wpts)))

        util.idle_add(self.ret_cb, wpts)


class DropUselessWaypoints(threading.Thread):
    def __init__(self, racetrack, waypoints, ret_cb):
        super().__init__()
        self.racetrack = racetrack
        self.waypoints = waypoints
        self.ret_cb = ret_cb

    @staticmethod
    def score_wpt(wpt):
        factor_x = assets.TILE_SIZE[0] / 4
        factor_y = assets.TILE_SIZE[0] / 4
        # the closer to a multiple of 'factor', the better
        score = (
            ((wpt.position[0] / factor_x) % 1) +
            ((wpt.position[1] / factor_y) % 1)
        )
        return score

    def run(self):
        wpts = self.waypoints
        print("Dropping useless waypoints ... (starting with {})".format(
            len(wpts)
        ))

        for wpt in wpts:
            wpt.score = self.score_wpt(wpt)

        borders = self.racetrack.borders
        m_border = MIN_DISTANCE_FROM_BORDERS ** 2
        m_waypoint = MIN_DISTANCE_FROM_WAYPOINTS ** 2
        removed = set()
        for wpt in set(wpts):
            if wpt.checkpoint is not None:
                # we *must* keep those
                continue

            if wpt in removed:
                continue

            keep = True
            for border in borders:
                # drop all the waypoints on a border
                if wpt.position in border.pts:
                    keep = False
                    break
                # or close to it
                dist = util.distance_sq_pt_to_segment(border.pts, wpt.position)
                if dist < m_border:
                    keep = False
                    break
            if not keep:
                removed.add(wpt)
                try:
                    wpts.remove(wpt)
                except KeyError:
                    pass
                continue

            for wpt_b in set(wpts):
                if wpt is wpt_b or wpt in removed:
                    continue
                dist = util.distance_sq_pt_to_pt(wpt.position, wpt_b.position)
                if dist > m_waypoint:
                    continue
                if wpt.score > wpt_b.score or wpt_b.checkpoint is not None:
                    to_remove = wpt
                else:
                    to_remove = wpt_b
                removed.add(to_remove)
                try:
                    wpts.remove(to_remove)
                except KeyError:
                    pass
                if to_remove is wpt:
                    break

        print("Done: {} waypoints remaining".format(len(wpts)))
        util.idle_add(self.ret_cb, wpts)


class FindReachableWaypointsThread(threading.Thread):
    """
    Basically, here, we play connect the dots
    """

    MAX_PATHS_BY_PT = 500

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

        paths = set()

        # start points
        to_examine = set()
        for wpt in wpts:
            if wpt.reachable:
                to_examine.add(wpt)

        borders = self.racetrack.borders

        print("Looking for reachable waypoints ...")

        nb_wpts = len(wpts)
        current = 0
        m_border = MIN_DISTANCE_FROM_BORDERS ** 2
        m_path = MIN_DISTANCE_FROM_PATHS ** 2

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

                # drop path too close to borders or
                # crossing a border
                keep = True
                m_dist = 0xFFFFFFFF
                for border in borders:
                    dist = util.distance_sq_segment_to_segment(
                        (origin.position, dest.position),
                        border.pts
                    )
                    m_dist = min(m_dist, dist)
                    if dist < m_border:
                        # car won't be able to follow this path easily
                        # (or at all if the path goes through a border)
                        keep = False
                        break
                if not keep:
                    continue

                keep = True
                for wpt in wpts:
                    if wpt is origin or wpt is dest:
                        continue
                    dist = util.distance_sq_pt_to_segment(
                        (origin.position, dest.position),
                        wpt.position
                    )
                    if dist < m_path:
                        # no point in having similar path twice
                        keep = False
                        break
                if not keep:
                    continue

                path = ia.Path(origin, dest, m_dist)
                path.compute_score_length()
                new_paths.append(path)
            if len(new_paths) <= 0:
                print("No new path found")
                current += 1
                continue
            new_paths.sort(key=lambda path: path.score)
            new_paths = new_paths[:self.MAX_PATHS_BY_PT]
            kept = 0
            for path in new_paths:
                if path not in paths:
                    paths.add(path)
                    kept += 1
                if path.b.reachable:  # already examined (or will be soon)
                    continue
                path.b.reachable = True
                to_examine.add(path.b)
            print("{} new paths found (max {} kept)".format(
                kept, self.MAX_PATHS_BY_PT)
            )
            if kept > 0:
                util.idle_add(self.update_cb, wpts, paths,
                              current, len(to_examine), nb_wpts)
            current += 1

        print("Done. Got {} waypoints and {} paths".format(
            len(wpts), len(paths)
        ))
        util.idle_add(self.update_cb, wpts, paths,
                      nb_wpts, nb_wpts, nb_wpts)
        util.idle_add(self.ret_cb, wpts, paths)


class ComputeScoreThread(threading.Thread):
    def __init__(self, racetrack, waypoints, paths, ret_cb):
        super().__init__()
        self.racetrack = racetrack
        self.waypoints = waypoints
        self.paths = paths
        self.ret_cb = ret_cb

    def run(self):
        borders = self.racetrack.borders
        wpts = self.waypoints
        paths = self.paths

        print("Computing {} waypoint scores ...".format(len(wpts)))

        for wpt in wpts:
            if not wpt.reachable:
                continue
            score = 0xFFFFFFFF
            for border in borders:
                score = min(
                    score,
                    util.distance_sq_pt_to_segment(border.pts, wpt.position)
                )
            wpt.score = score

        print("Computing {} path scores ...".format(len(paths)))

        for path in paths:
            score = 0xFFFFFFFF
            for border in borders:
                score = min(
                    score,
                    util.distance_sq_segment_to_segment(
                        border.pts, (path.a.position, path.b.position)
                    )
                )
            path.score = score

        print("Done")
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
        self.waypoint_mgmt = ia.WaypointManager()
        self.waypoint_mgmt.parent = self.race_track
        util.register_drawer(WAYPOINTS_LAYER, self.waypoint_mgmt)
        self.osd_message.show("Done")
        logger.info("Done")

    def on_key(self, event):
        global RUNNING
        if event.type != pygame.KEYDOWN and event.type != pygame.KEYUP:
            return

        if event.key == pygame.K_F1 or event.key == pygame.K_ESCAPE:
            RUNNING = False
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
        self.osd_message.show("Finding all possible waypoints ...")
        t = FindAllWaypointsThread(self.race_track, self.precompute2)
        t.start()

    def precompute2(self, all_waypoints):
        self.osd_message.show("Dropping useless waypoints ...")
        wpts = set(all_waypoints)
        self.waypoint_mgmt.set_waypoints(wpts)
        t = DropUselessWaypoints(self.race_track, all_waypoints,
                                 self.precompute3)
        t.start()

    def precompute3(self, all_waypoints):
        self.osd_message.show("Finding paths and reachables waypoints ...")
        wpts = all_waypoints
        self.waypoint_mgmt.set_waypoints(wpts)

        t = FindReachableWaypointsThread(self.race_track, all_waypoints,
                                         self.precompute4,
                                         self.precompute3_update)
        t.start()

    def precompute3_update(self, all_waypoints, all_paths,
                           progression, to_examine, total):
        self.osd_message.show(
            "Connecting the dots ... {}/{}/{}".format(
                progression, to_examine, total
            )
        )
        wpts = set(all_waypoints)
        self.waypoint_mgmt.set_waypoints(wpts)
        paths = set(all_paths)
        self.waypoint_mgmt.set_paths(paths)

    def precompute4(self, all_waypoints, all_paths):
        self.osd_message.show("Computing waypoints and path scores ...")
        self.waypoint_mgmt.set_waypoints(all_waypoints)
        self.waypoint_mgmt.set_paths(all_paths)

        t = ComputeScoreThread(self.race_track, all_waypoints, all_paths,
                               self.save)
        t.start()

    def save(self, *args, **kwargs):
        self.osd_message.show("Saving ...")
        print("Saving ...")
        util.idle_add(self._save)

    def _save(self):
        self.osd_message.show("All done")
        with open(self.filepath, 'r') as fd:
            data = json.load(fd)
        data['ia'] = self.waypoint_mgmt.serialize()
        with open(self.filepath, 'w') as fd:
            json.dump(data, fd, indent=4, sort_keys=True)
        print("All Done")


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
