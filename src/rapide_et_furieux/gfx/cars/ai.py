#!/usr/bin/env

import itertools
import logging
import math
import random
import threading
import time

import pygame

from . import Car
from . import Controls
from ..weapons.common import CATEGORY_COUNTER_MEASURES
from ..weapons.common import CATEGORY_GUIDED
from ..weapons.common import CATEGORY_GUNS
from ..weapons.common import NB_CATEGORIES
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
        self.score = util.distance_sq_pt_to_pt(self.a.position, self.b.position)

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
    COLOR_PATH = (255, 0, 255)
    MIN_ANGLE_FOR_STEERING = math.pi / 16

    DISTANCE_STUCK = 8 ** 2
    MIN_TIME_STUCK = 2.0
    BACKWARD_TIME = (1.5, 4.0)  # time we try to go backward if we are stuck
    SLOW_DOWN_IF_BOGIE = 0.5
    FIRE_DELAY = 1.0  # simulate ~human reaction time

    def __init__(self, *args, waypoint_mgmt, **kwargs):
        global g_number_gen

        super().__init__(*args, **kwargs)

        self.min_pt_dist = self.game_settings['waypoint_min_distance'] ** 2
        self.max_speed = self.game_settings['max_speed']['normal']['forward']

        self.number = g_number_gen
        g_number_gen += 1
        self.waypoints = waypoint_mgmt
        self.path = []
        self.path_set = set()

        self.prev_position = (0, 0)
        self.stuck_since = None
        self.reverse_since = None
        self.backward_time = None

        self.fire_delay = self.FIRE_DELAY

        util.register_animator(self.ia_move)

    def __str__(self):
        return "IA{} ({}|{})".format(self.number, self.position, self.radians)

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
                self.reverse_since = time.time()
                self.backward_time = (
                    (random.random() *
                     (self.BACKWARD_TIME[1] - self.BACKWARD_TIME[0])) +
                    self.BACKWARD_TIME[0]
                )

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
            if (self.reverse_since is None and
                    (self.speed[0] >
                     (self.SLOW_DOWN_IF_BOGIE * self.max_speed))):
                acceleration = 0

        if acceleration != 0 and self.reverse_since is not None:
            n = time.time()
            if n - self.reverse_since < self.backward_time:
                acceleration *= -1
            else:
                self.reverse_since = None
                self.stuck_since = None
                self.prev_position = (0, 0)

        # steering ?
        steering = 0
        min_angle = self.MIN_ANGLE_FOR_STEERING
        if self.speed[0] < 0:
            next_pt = (
                -next_pt[0],
                # [-math.pi ; +math.pi]
                ((next_pt[1] + (2 * math.pi)) % (2 * math.pi)) - math.pi
            )
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

    def can_use_counter_measures(self):
        # can always use them
        return True

    def get_closest_target(self):
        closest = (0xFFFFFFFF, None)
        for car in self.parent.cars:
            if car is self:
                continue
            dist = util.distance_sq_pt_to_pt(self.position, car.position)
            if dist < closest[0]:
                closest = (dist, car)
        return closest

    def can_use_guided(self):
        # can we shoot the closest target ?
        (dist, closest) = self.get_closest_target()
        if closest is None:
            return False
        line = (self.position, closest.position)
        obstacles = self.parent.collisions.get_obstacles_on_segment(
            line, limit=2
        )
        obstacles = {
            x[0] for x in obstacles
            if x[0] is not closest and x[0] is not self
        }
        return len(obstacles) <= 0

    def can_use_forward(self):
        TOLERANCE = math.pi / 8

        # do we have someone in front of us ?
        radians = -self.radians
        for car in self.parent.cars:
            target_angle = math.atan2(
                car.position[1] - self.position[1],
                car.position[0] - self.position[0],
            )
            diff = (target_angle - radians) % (2 * math.pi)
            if diff < TOLERANCE and diff > -TOLERANCE:
                return True
        return False

    def compute_weapons(self, frame_interval):
        # sort by categories
        weapons = {}
        for (weapon, count) in self.weapons.items():
            if count <= 0:
                continue
            if weapon.category not in weapons:
                weapons[weapon.category] = set()
            weapons[weapon.category].add(weapon)

        if len(weapons) <= 0:
            # no usable weapon at all
            if self.weapon is not None:
                self.weapon.deactivate()
                self.weapon = None
            return

        CAN_USE = {
            CATEGORY_GUNS: self.can_use_forward,
            CATEGORY_GUIDED: self.can_use_guided,
            CATEGORY_COUNTER_MEASURES: self.can_use_counter_measures,
        }

        # starts by using counter-measures, then guided, then forward guns
        for category_idx in range(NB_CATEGORIES, -1, -1):
            if category_idx not in weapons:
                continue
            if CAN_USE[category_idx]():
                break
        else:
            # no usable weapon category
            return

        weapon = weapons[category_idx].pop()
        if self.weapon is None or weapon != self.weapon.parent:
            # switch weapon
            if self.weapon is not None:
                self.weapon.deactivate()
            self.weapon = weapon.activate(self.parent, self)
            self.fire_delay = self.FIRE_DELAY
        else:
            self.fire_delay -= frame_interval
            if self.fire_delay > 0:
                return
            if self.weapon.fire():
                self.weapons[self.weapon.parent] -= 1
                if self.weapons[self.weapon.parent] <= 0:
                    self.weapons.pop(self.weapon.parent)

    def ia_move(self, frame_interval):
        if not self.can_move:
            return

        path = self.waypoints.compute_path(
            self, self.position, self.next_checkpoint
        )

        # skip point too close to us
        to_skip = 0
        for pt in path:
            dist = util.distance_sq_pt_to_pt(pt, self.position)
            if dist < self.min_pt_dist:
                to_skip += 1
            else:
                break

        if to_skip >= len(path):
            self.path = path
        else:
            self.path = path[to_skip:]
        self.path_set = set(self.path)

        self.compute_controls(frame_interval)
        self.compute_weapons(frame_interval)

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
    MAX_PATH_PTS = 30

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
        wm.waypoints = set(wpts.values())
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
                if dist < closest[0]:
                    closest = (dist, wpt)
            assert(closest[1] is not None)
            self.grid_waypoints[tile_pos] = set()
            self.grid_waypoints[tile_pos].add(closest[1])

    def g_score(self, car, old_score, old_pt, new_pt, target):
        if old_score is not None:
            (x, y, g_score) = old_score[:3]
        else:
            (x, y, g_score) = (0, 0, 0)
        x += abs(new_pt[0] - old_pt[0])
        y += abs(new_pt[1] - old_pt[1])
        # g_score is the cost to reach this point
        g_score = x ** 2 + y ** 2
        return (x, y, g_score)

    def f_score(self, car, old_score, old_pt, new_pt, target, g_score=None):
        if g_score is None:
            (x, y, g_score) = self.g_score(car, old_score, old_pt, new_pt,
                                           target)
        else:
            (x, y, g_score) = g_score
        extra_cost = 0
        if self.parent.collisions.has_obstacle_in_path(car, (new_pt, target)):
            extra_cost = assets.TILE_SIZE[0] / 2
        f_score = (
            (x + abs(target[0] - new_pt[0]) + extra_cost) ** 2 +
            (y + abs(target[1] - new_pt[1]) + extra_cost) ** 2
        )
        return (x, y, g_score, f_score)

    def compute_path(self, car, origin, target):
        # turn the target checkpoint into a waypoint
        target = self.checkpoint_waypoints[target]

        # we reuse some part of the previous path if possible, but it requires
        # having the same target
        car_path = list(reversed(car.path))
        car_path_set = car.path_set
        if len(car_path) > 0 and car_path[0] != target.position:
            car_path = []
            car_path_set = set()

        # ### simple A* algorithm to find the most likely best path

        first = (0xFFFFFFF, None)
        origin_grid = (int(origin[0] / assets.TILE_SIZE[0]),
                       int(origin[1] / assets.TILE_SIZE[1]))
        if origin_grid in self.grid_waypoints:
            origins = self.grid_waypoints[origin_grid]
        else:
            logger.warning("AI: No waypoint close to {} !".format(origin_grid))
            origins = self.waypoints
        for pt in origins:
            dist = util.distance_sq_pt_to_pt(pt.position, origin)
            if dist < first[0]:
                first = (dist, pt)

        examined = set()
        to_examine = set([first[1]])
        scores = {
            pt:
            # known cost to go to the node + estimated cost to go to the
            # target
            (
                self.f_score(car, None, origin, pt.position, target.position),
                0
            )
            for pt in to_examine
        }
        came_from = {}

        current = None
        end_of_path = None
        while len(to_examine) > 0 and end_of_path is None:
            lowest_score = 0xFFFFFFF
            current = None
            for wpt in to_examine:
                (score, nb_pts) = scores[wpt]
                if score[3] < lowest_score:
                    lowest_score = score[3]
                    current = wpt
            assert current is not None

            if current.position in car_path_set:
                idx = car_path.index(current.position)
                end_of_path = car_path[:idx + 1]
                break

            if current is target:
                end_of_path = [current.position]
                break

            if nb_pts > self.MAX_PATH_PTS:
                end_of_path = [current.position]
                break

            to_examine.remove(current)
            examined.add(current)

            for path in current.paths:
                neighbor = path.b if path.a is current else path.a
                if neighbor in examined:
                    continue
                to_examine.add(neighbor)

                g_score = self.g_score(
                    car, scores[current][0], current.position,
                    neighbor.position, target.position)
                if neighbor in scores and g_score[2] > scores[neighbor][0][2]:
                    # we already know a better path
                    continue

                # best path up to now
                came_from[neighbor] = current
                scores[neighbor] = (
                    self.f_score(
                        car, scores[current][0], current.position,
                        neighbor.position, target.position,
                        g_score=g_score
                    ),
                    nb_pts + 1
                )

        if end_of_path is None:
            raise Exception("[{}] Failed to found path from {} to {}".format(
                self, origin, target
            ))

        # rebuild the path
        path = end_of_path
        while current in came_from:
            current = came_from[current]
            path.append(current.position)
        path.reverse()
        path = path[1:]
        return path
