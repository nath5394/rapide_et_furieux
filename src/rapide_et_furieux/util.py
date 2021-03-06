import itertools
import logging
import math
import sys
import time

import pygame


VERSION = "0.1"

g_event_listeners = []
g_animators = []
g_drawers = []
g_loop = True
g_rnd = 0
g_on_idle = []
g_paused = False

logger = logging.getLogger(__name__)

GAME_SETTINGS_TEMPLATE = {
    # default values
    'bonus_interval': 1.0,
    'checkpoint_min_distance': 256,
    'waypoint_min_distance': 64,
    'background_color': (0, 0, 0),
    'collision': {
        'reverse_factor': 1.2,  # when hitting a static object
        'propagation': 0.9,  # when hitting a moving one
        'angle_transmission': 4.0,
    },
    'acceleration': {
        'normal': 512,
        'crap': 256,
    },
    'braking': {
        'normal': 1024,
        'crap': 768,
    },
    'lateral_speed_slowdown': {
        # tires on the road
        'normal': 1024,
        'crap': 512,
    },
    'steering': {
        'ref_speed': 256,  # speed required for full steering
        'normal': math.pi,
        'crap': math.pi / 2,
    },
    'max_speed': {
        'normal': {
            'forward': 768,
            'reverse': 256,
        },
        'crap': {
            'forward': 256,
            'reverse': 128,
        },
    },
    'engine braking': {
        'normal': 512,
        'crap': 512,
    }
}


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    nb = 0
    first = None
    last = None
    for x in zip(a, b):
        if first is None:
            first = x[0]
        last = x[1]
        yield x
        nb += 1
    if nb > 2:
        yield (last, first)


def to_polar(coord):
    # coord are from the top-left of the screen
    return (
        math.sqrt((coord[0] ** 2) + (coord[1] ** 2)),
        math.atan2(coord[1], coord[0])
    )


def to_cartesian(polar):
    # coord are from the top-left of the screen
    return (
        polar[0] * math.cos(polar[1]),
        polar[0] * math.sin(polar[1]),
    )


def _calculate_gradient(line):
    # Ensure that the line is not vertical
    if (line[0][0] != line[1][0]):
        return (line[0][1] - line[1][1]) / (line[0][0] - line[1][0])
    return None


def _calculate_y_axis_intersect(p, m):
    """Compute the point 'b' where line crosses the Y axis"""
    return p[1] - (m * p[0])


def _get_line_intersect_points(line_a, line_b):
    """
    Calc the point where two infinitely long lines (p1 to p2 and p3 to p4)
    intersect.
    Handle parallel lines and vertical lines (the later has infinite 'm').
    Returns a point tuple of points like this ((x,y),...)  or None
    In non parallel cases the tuple will contain just one point.
    For parallel lines that lay on top of one another the tuple will contain
    all four points of the two lines
    """
    (p1, p2) = line_a
    (p3, p4) = line_b
    m1 = _calculate_gradient(line_a)
    m2 = _calculate_gradient(line_b)

    # See if the lines are parallel
    if m1 != m2:
        # Not parallel

        # See if either line is vertical
        if (m1 is not None and m2 is not None):
            # Neither line vertical
            b1 = _calculate_y_axis_intersect(p1, m1)
            b2 = _calculate_y_axis_intersect(p3, m2)
            x = (b2 - b1) / (m1 - m2)
            y = (m1 * x) + b1
        elif m1 is None:
            # Line 1 is vertical so use line 2's values
            b2 = _calculate_y_axis_intersect(p3, m2)
            x = p1[0]
            y = (m2 * x) + b2
        else:
            # Line 2 is vertical so use line 1's values
            b1 = _calculate_y_axis_intersect(p1, m1)
            x = p3[0]
            y = (m1 * x) + b1
        return ((x, y),)

    # Parallel lines with same 'b' value must be the same line so they intersect
    # everywhere in this case we return the start and end points of both lines
    # the _calculate_intersect_point method will sort out which of these points
    # lays on both line segments
    (b1, b2) = (None, None)  # vertical lines have no b value
    if m1 is not None:
        b1 = _calculate_y_axis_intersect(p1, m1)

    if m2 is not None:
        b2 = _calculate_y_axis_intersect(p3, m2)

    # If these parallel lines lay on one another
    if b1 == b2:
        return (p1, p2, p3, p4)

    return None


def line_to_int(line):
    return (
        (
            int(line[0][0]),
            int(line[0][1]),
        ),
        (
            int(line[1][0]),
            int(line[1][1]),
        ),
    )


def get_segment_intersect_point(line_a, line_b):
    """
    For line segments (ie not infinitely long lines) the intersect point
    may not lay on both lines.

    If the point where two lines intersect is inside both line's bounding
    rectangles then the lines intersect. Returns intersect point if the line
    intesect o None if not
    """
    line_a = line_to_int(line_a)
    line_b = line_to_int(line_b)

    (p1, p2) = line_a
    (p3, p4) = line_b
    intersects = _get_line_intersect_points(line_a, line_b)
    if intersects is None:
        return None

    (p1, p2) = (
        (
            min(p1[0], p2[0]) - 1,
            min(p1[1], p2[1]) - 1,
        ),
        (
            max(p1[0], p2[0]) + 2,
            max(p1[1], p2[1]) + 2,
        )
    )
    (p3, p4) = (
        (
            min(p3[0], p4[0]) - 1,
            min(p3[1], p4[1]) - 1,
        ),
        (
            max(p3[0], p4[0]) + 2,
            max(p3[1], p4[1]) + 2,
        )
    )

    width = p2[0] - p1[0]
    height = p2[1] - p1[1]
    # approximate because _get_line_intersect_points
    # may reply with crappy numbers like 0.9999
    r1 = pygame.Rect(p1, (width, height))

    width = p4[0] - p3[0]
    height = p4[1] - p3[1]
    # approximate because _get_line_intersect_points
    # may reply with crappy numbers like 0.9999
    r2 = pygame.Rect(p3, (width, height))

    for point in intersects:
        point = (int(point[0]), int(point[1]))
        res1 = r1.collidepoint(point)
        res2 = r2.collidepoint(point)
        if res1 and res2:
            point = [int(pp) for pp in point]
            return point

    # This is the case where the infinitely long lines crossed but
    # the line segments didn't
    return None


def raytrace(line, grid_size=1):
    ((x0, y0), (x1, y1)) = line
    x0 = int(x0)
    y0 = int(y0)
    x1 = int(x1)
    y1 = int(y1)

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x = x0
    y = y0
    n = 1 + dx + dy
    x_inc = 1 if (x1 > x0) else -1
    y_inc = 1 if (y1 > y0) else -1
    error = dx - dy
    dx *= 2
    dy *= 2

    last_pos = None
    for n in range(0, round(n)):
        new_pos = (int(x / grid_size), int(y / grid_size))
        if new_pos != last_pos:
            yield(new_pos)
            last_pos = new_pos

        if error > 0:
            x += x_inc
            error -= dy
        else:
            y += y_inc
            error += dx


def distance_pt_to_pt(pt_a, pt_b):
    return math.sqrt(
        ((pt_a[0] - pt_b[0]) ** 2) +
        ((pt_a[1] - pt_b[1]) ** 2)
    )


def distance_pt_to_line(line, pt):
    ((x0, y0), (x1, y1)) = line
    (x2, y2) = pt
    nom = abs(
        ((y2 - y1) * x0) -
        ((x2 - x1) * y0) +
        (x2 * y1) -
        (y2 * x1)
    )
    denom = math.sqrt((y2 - y1) ** 2 + ((x2 - x1) ** 2))
    result = nom / denom
    return result


def distance_sq_pt_to_pt(pt_a, pt_b):
    return (
        ((pt_b[0] - pt_a[0]) ** 2) +
        ((pt_b[1] - pt_a[1]) ** 2)
    )


def distance_sq_pt_to_segment(segment, pt):
    line_dist = (
        ((segment[1][0] - segment[0][0]) ** 2) +
        ((segment[1][1] - segment[0][1]) ** 2)
    )
    if line_dist == 0:
        return (
            ((pt[0] - segment[0][0]) ** 2) +
            ((pt[1] - segment[0][1]) ** 2)
        )
    t = (
        ((pt[0] - segment[0][0]) * (segment[1][0] - segment[0][0])) +
        ((pt[1] - segment[0][1]) * (segment[1][1] - segment[0][1]))
    ) / line_dist
    if t < 0:
        t = 0
    if t > 1:
        t = 1
    x = (
        segment[0][0] +
        (t * (segment[1][0] - segment[0][0]))
    )
    y = (
        segment[0][1] +
        (t * (segment[1][1] - segment[0][1]))
    )
    return (((pt[0] - x) ** 2) + ((pt[1] - y) ** 2))


def distance_sq_segment_to_segment(segment_a, segment_b):
    if get_segment_intersect_point(segment_a, segment_b):
        return 0
    m = 0xFFFFFFFF
    m = min(m, distance_sq_pt_to_segment(segment_a, segment_b[0]))
    m = min(m, distance_sq_pt_to_segment(segment_a, segment_b[1]))
    m = min(m, distance_sq_pt_to_segment(segment_b, segment_a[0]))
    m = min(m, distance_sq_pt_to_segment(segment_b, segment_a[1]))
    return m


def common_str_prefix(strings):
    "Given a list of strings, returns the longest common leading component"
    s1 = min(strings)
    s2 = max(strings)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1


def on_uncatched_exception_cb(exc_type, exc_value, exc_tb):
    logger.error(
        "=== UNCATCHED EXCEPTION ===",
        exc_info=(exc_type, exc_value, exc_tb)
    )
    logger.error(
        "==========================="
    )


def init_logging():
    lg = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)-6s %(name)-30s %(message)s')
    handler.setFormatter(formatter)
    lg.addHandler(handler)
    sys.excepthook = on_uncatched_exception_cb
    logging.getLogger().setLevel(logging.DEBUG)


def get_default_resolution():
    modes = pygame.display.list_modes()
    for mode in modes:
        if mode[0] < (mode[1] * 2):
            return mode
    return modes[0]


def set_default_resolution():
    size = get_default_resolution()
    screen = pygame.display.set_mode(
        size, pygame.FULLSCREEN | pygame.HWSURFACE
    )
    return screen


def exit():
    global g_loop
    g_loop = False


def check_base_keys(event):
    global g_paused

    if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
        logger.info("Quitting ...")
        idle_add(exit)
        return
    if event.type == pygame.KEYDOWN and event.key == pygame.K_PAUSE:
        g_paused = not g_paused
        logger.info("Paused: {}".format(g_paused))
        return


def register_event_listener(event_listener):
    global g_event_listeners
    g_event_listeners.append(event_listener)


def unregister_event_listener(event_listener):
    global g_event_listeners
    g_event_listeners.remove(event_listener)


def register_animator(animator):
    global g_animators
    g_animators.append(animator)


def unregister_animator(animator):
    global g_animators
    g_animators.remove(animator)


def register_drawer(layer, drawer):
    global g_drawers
    global g_rnd
    # g_rnd is only used to break ties when ordering
    g_drawers.append((layer, g_rnd, drawer))
    g_drawers.sort()
    g_rnd += 1


def unregister_drawer(drawer):
    global g_drawers
    for tup in g_drawers:
        if tup[2] == drawer:
            break
    else:
        raise KeyError("Unknown drawer")
    g_drawers.remove(tup)


def idle_add(action, *args, **kwargs):
    global g_on_idle
    g_on_idle.append((action, args, kwargs))


def main_loop(screen):
    global g_animators
    global g_drawers
    global g_event_listeners
    global g_loop
    global g_on_idle
    global g_paused

    g_loop = True

    if check_base_keys not in g_event_listeners:
        register_event_listener(check_base_keys)

    logger.info("Ready")

    previous_frame = time.time()
    last_frame = time.time()

    while g_loop:
        while g_paused and g_loop:
            time.sleep(0.1)
            for event in pygame.event.get():
                check_base_keys(event)

        idle = True
        for event in pygame.event.get():
            idle = False
            for event_listener in set(g_event_listeners):
                if event_listener(event):
                    break

        if idle:
            while len(g_on_idle) > 0:
                (action, args, kwargs) = g_on_idle.pop(0)
                action(*args, **kwargs)

        frame_interval = last_frame - previous_frame
        if frame_interval <= 0.0:
            # avoid divisions by zero
            frame_interval = 0.00001
        for animator in reversed(g_animators):
            animator(frame_interval)

        for (layer, _, drawer) in g_drawers:
            drawer.draw(screen)
        pygame.display.flip()

        previous_frame = last_frame
        last_frame = time.time()

    logger.info("Good bye")
