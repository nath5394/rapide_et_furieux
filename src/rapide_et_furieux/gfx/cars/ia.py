#!/usr/bin/env

import itertools
import logging
import math
import threading
import time

import pygame

from . import Car
from . import Controls
from ... import assets
from ... import util


logger = logging.getLogger(__name__)
g_number_gen = 0


class Waypoint(object):
    def __init__(self, position, reachable):
        self.position = (int(position[0]), int(position[1]))
        self.reachable = reachable
        self.score = 0
        self.paths = []
        self.checkpoint = None

    def __str__(self):
        return ("Waypoint: {} ({})".format(
            self.position,
            self.score
        ))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.position)

    def __eq__(self, o):
        return self.position == o.position

    def serialize(self):
        return {
            'position': self.position,
            'score': self.score,
        }

    @staticmethod
    def unserialize(data):
        wpt = Waypoint(data['position'], True)
        wpt.score = data['score']
        return wpt


class Path(object):
    def __init__(self, a, b, score):
        self.a = a  # first waypoint
        self.b = b  # second waypoint
        self.score = score  # bigger is worst

    def compute_score_length(self):
        self.score = (
            ((self.a.position[0] - self.b.position[0]) ** 2) +
            ((self.a.position[1] - self.b.position[1]) ** 2)
        )

    def __str__(self):
        return ("Path({}): {} | {}".format(
            self.score,
            self.a,
            self.b
        ))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.a, self.b))

    def __eq__(self, o):
        return (self.a, self.b) == (o.a, o.b)

    def serialize(self):
        return {
            'a': self.a.position,
            'b': self.b.position,
            'score': self.score,
        }

    @staticmethod
    def unserialize(data, wpts):
        pt_a = wpts[tuple(data['a'])]
        pt_b = wpts[tuple(data['b'])]
        p = Path(pt_a, pt_b, data['score'])
        pt_a.paths.append(p)
        pt_b.paths.append(p)
        return p


class IACar(Car):
    COLOR_PATH = (0, 255, 0)
    MIN_ANGLE_FOR_STEERING = math.pi / 16

    DISTANCE_STUCK = 8 ** 2
    MIN_TIME_STUCK = 4.0
    BACKWARD_TIME = 3.0  # time we try to go backward if we are stuck

    def __init__(self, *args, waypoint_mgmt, **kwargs):
        global g_number_gen

        super().__init__(*args, **kwargs)

        self.min_pt_dist = self.game_settings['waypoint_min_distance'] ** 2

        self.number = g_number_gen
        g_number_gen += 1
        self.waypoints = waypoint_mgmt
        self.path = []

        self.prev_position = (0, 0)
        self.stuck_since = None
        self.reverse_since = None

        util.register_animator(self.ia_move)

    def __str__(self):
        return "IA{} ({}|{})".format(self.number, self.position, self.radians)

    def __repr__(self):
        return str(self)

    def compute_controls(self, frame_interval):
        next_pt = self.path[0]
        path = (self.position, next_pt)

        dist = util.distance_sq_pt_to_pt(self.prev_position, self.position)
        if dist >= self.DISTANCE_STUCK:
            self.stuck_since = None
            self.prev_position = self.position
        else:
            if self.stuck_since is None:
                self.stuck_since = time.time()
            elif self.reverse_since is None and (
                        time.time() - self.stuck_since >= self.MIN_TIME_STUCK
                    ):
                logger.warning("Car %s appears to be stuck "
                               "--> reversing direction",
                               self)
                self.reverse_since = time.time()

        has_bogie = self.parent.collisions.has_obstacle_in_path(self, path)

        # next point relative to the car
        next_pt = (
            (next_pt[0] - self.position[0]),
            (next_pt[1] - self.position[1]),
        )

        next_pt = util.to_polar(next_pt)

        if next_pt[0] < 0:
            next_pt = (-next_pt[0], next_pt[1] + math.pi)

        next_pt = (next_pt[0], next_pt[1] + self.radians)

        next_pt = (
            next_pt[0],
            # [-math.pi ; +math.pi]
            ((next_pt[1] + math.pi) % (2 * math.pi)) - math.pi
        )

        # accelerate / brake / go forward ?
        acceleration = 1

        if has_bogie:
            logger.warning("%s: Bogie detected on trajectory --> slowing down",
                           self)
            acceleration = 0

        if self.reverse_since is not None:
            n = time.time()
            if n - self.reverse_since < self.BACKWARD_TIME:
                acceleration *= -1
            else:
                logger.info("%s: Stopped reversing speed", self)
                self.reverse_since = None
                self.stuck_since = None
                self.prev_position = (0, 0)

        # steering ?
        min_angle = self.MIN_ANGLE_FOR_STEERING
        steering = 0
        if next_pt[1] < -min_angle:
            steering = -1
        elif next_pt[1] > min_angle:
            steering = 1

        self.controls = Controls(
            accelerate=acceleration > 0,
            brake=acceleration < 0,
            steer_left=steering < 0,
            steer_right=steering > 0,
        )

    def ia_move(self, frame_interval):
        if not self.can_move:
            return

        path = self.waypoints.compute_path(
            self, self.position, self.next_checkpoint
        )

        # skip point too close to us
        to_skip = 0
        for pt in self.path:
            dist = util.distance_sq_pt_to_pt(pt, self.position)
            if dist < self.min_pt_dist:
                to_skip += 1
            else:
                break

        if to_skip >= len(path):
            self.path = path
        else:
            self.path = path[to_skip:]

        self.compute_controls(frame_interval)

    def draw(self, screen):
        super().draw(screen)
        if self.parent.debug:
            self.draw_ia_path(screen)

    def draw_ia_path(self, screen):
        parent_abs = self.parent.absolute
        path = [self.position] + self.path
        for (pa, pb) in zip(path, path[1:]):
            pygame.draw.line(
                screen,
                self.COLOR_PATH,
                (
                    pa[0] + parent_abs[0],
                    pa[1] + parent_abs[1],
                ),
                (
                    pb[0] + parent_abs[0],
                    pb[1] + parent_abs[1],
                ),
                3
            )


class WaypointManager(object):
    COLOR_UNREACHABLE = pygame.Color(200, 200, 200, 255)
    COLOR_REACHABLE = pygame.Color(0, 255, 0, 255)
    COLOR_PATH = pygame.Color(0, 255, 0, 255)

    def __init__(self, game_settings, race_track):
        self.parent = race_track

        self.waypoints = set()
        self.paths = set()

        # closest points to each tile
        # (grid_x, grid_y) = set([waypoint_a, waypoint_b, ...])
        self.grid_waypoints = {}
        # checkpoint -> waypoint
        self.checkpoint_waypoints = {}

        self.lock = threading.Lock()

    def set_waypoints(self, waypoints):
        with self.lock:
            self.waypoints = waypoints

    def set_paths(self, paths):
        with self.lock:
            self.paths = paths

    def _draw(self, screen, parent_abs):
        for pt in self.waypoints:
            rect = pygame.Rect(
                (pt.position[0] - 5 + parent_abs[0],
                 pt.position[1] - 5 + parent_abs[1]),
                (10, 10)
            )
            screen.fill(
                self.COLOR_REACHABLE
                if pt.reachable else self.COLOR_UNREACHABLE,
                rect
            )
        for path in self.paths:
            pygame.draw.line(
                screen,
                self.COLOR_PATH,
                (
                    path.a.position[0] + parent_abs[0],
                    path.a.position[1] + parent_abs[1],
                ),
                (
                    path.b.position[0] + parent_abs[0],
                    path.b.position[1] + parent_abs[1],
                )
            )

    def draw(self, screen):
        with self.lock:
            self._draw(screen, self.parent.absolute)

    def serialize(self):
        waypoints = [
            wpt.serialize()
            for wpt in self.waypoints
            if wpt.reachable
        ]
        paths = [path.serialize() for path in self.paths]
        return {
            'waypoints': waypoints,
            'paths': paths,
        }

    @staticmethod
    def unserialize(data, game_settings, race_track):
        wpts = {}
        for d in data['waypoints']:
            w = Waypoint.unserialize(d)
            wpts[w.position] = w
        paths = set()
        for d in data['paths']:
            paths.add(Path.unserialize(d, wpts))
        wm = WaypointManager(game_settings, race_track)
        wm.waypoints = wpts.values()
        wm.paths = paths
        return wm

    def optimize(self, racetrack):
        # index checkpoints
        self.checkpoint_waypoints = {}
        for cp in racetrack.checkpoints:
            for wpt in self.waypoints:
                if wpt.position == cp.pt:
                    break
            else:
                raise Exception("No waypoint matching checkpoint {} !".format(
                    cp
                ))
            wpt.checkpoint = cp
            self.checkpoint_waypoints[cp] = wpt

        self.grid_waypoints = {}
        # for each tile, we want the closest possible waypoints
        # so:
        # - the waypoint in a given grid tile
        # - the waypoints in the adjacent tiles
        for wpt in self.waypoints:
            offsets = itertools.product(
                range(-1, 2, 1),
                range(-1, 2, 1),
            )
            for offset in offsets:
                pos = (
                    int((wpt.position[0] / assets.TILE_SIZE[0]) + offset[0]),
                    int((wpt.position[1] / assets.TILE_SIZE[1]) + offset[1]),
                )
                if pos not in self.grid_waypoints:
                    self.grid_waypoints[pos] = set()
                self.grid_waypoints[pos].add(wpt)

        # If there are no close waypoint (unlikely but possible):
        # - fallback on the waypoint closest to the center of the tile
        for tile_pos in racetrack.tiles.grid.keys():
            if tile_pos in self.grid_waypoints:
                continue
            center = (
                (tile_pos[0] * assets.TILE_SIZE[0]) + (assets.TILE_SIZE[0] / 2),
                (tile_pos[1] * assets.TILE_SIZE[1]) + (assets.TILE_SIZE[1] / 2),
            )
            closest = (0xFFFFFFFF, None)
            for wpt in self.waypoints:
                dist = util.distance_sq_pt_to_pt(center, wpt.position)
            assert(closest[1] is not None)
            self.grid_waypoints[tile_pos] = set()
            self.grid_waypoints[tile_pos].add(closest[1])

    def pathfinding_heuristic(self, car, origin, point, target):
        h = util.distance_pt_to_pt(point, target)
        if self.parent.collisions.has_obstacle_in_path(car, (point, target)):
            h += assets.TILE_SIZE[0] * 2
        return h

    def compute_path(self, car, origin, target):
        # turn the target checkpoint into a waypoint
        target = self.checkpoint_waypoints[target]

        #### simple A* algorithm to find the most likely best path

        first = (0xFFFFFFF, None)
        for pt in self.grid_waypoints[
                    int(origin[0] / assets.TILE_SIZE[0]),
                    int(origin[1] / assets.TILE_SIZE[1]),
                ]:
            dist = util.distance_sq_pt_to_pt(pt.position, origin)
            if dist < first[0]:
                first = (dist, pt)

        examined = set()
        to_examine = set([first[1]])
        f_scores = {
            pt:
            # known cost to go to the node + estimated cost to go to the
            # target
            (util.distance_pt_to_pt(origin, pt.position) +
             self.pathfinding_heuristic(
                 car, origin, pt.position, target.position
             ))
            for pt in to_examine
        }
        best_origin = {}
        g_scores = {
            # pt --> actual best cost found to reach each node
            pt: util.distance_pt_to_pt(origin, pt.position)
            for pt in to_examine
        }
        came_from = {}

        current = None
        success = False
        while len(to_examine) > 0 and not success:
            lowest_score = 0xFFFFFFF
            current = None
            for wpt in to_examine:
                score = f_scores[wpt]
                if score < lowest_score:
                    lowest_score = score
                    current = wpt
            assert current is not None

            if current is target:
                success = True
                break
            to_examine.remove(current)
            examined.add(current)

            for path in current.paths:
                neighbor = path.b if path.a is current else path.a
                if neighbor in examined:
                    continue
                to_examine.add(neighbor)

                g_score = g_scores[current] + util.distance_pt_to_pt(
                    current.position, neighbor.position
                )
                if neighbor in g_scores and g_score > g_scores[neighbor]:
                    # we already know a better path
                    continue

                # best path up to now
                came_from[neighbor] = current
                g_scores[neighbor] = g_score

                f_scores[neighbor] = g_score + self.pathfinding_heuristic(
                    car, origin, neighbor.position, target.position
                )

        if not success:
            raise Exception("[{}] Failed to found path from {} to {}".format(
                self, origin, target
            ))

        # rebuild the path
        path = [current.position]
        while current in came_from:
            current = came_from[current]
            path.append(current.position)
        path.reverse()
        path = path[1:]
        return path
