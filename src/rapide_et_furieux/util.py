import logging
import time

import pygame


VERSION = "0.1"

g_event_listeners = set()
g_animators = set()
g_drawers = []
g_loop = True
g_rnd = 0

logger = logging.getLogger(__name__)


def get_default_resolution():
    modes = pygame.display.list_modes()
    for mode in modes:
        if mode[0] < (mode[1] * 2):
            return mode
    return modes[0]


def set_default_resolution():
    size = get_default_resolution()
    screen = pygame.display.set_mode(
        size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
    )
    return screen


def check_exit_event(event):
    global g_loop

    if event.type == pygame.QUIT:
        g_loop = False
        return
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        g_loop = False
        return


def register_event_listener(event_listener):
    global g_event_listeners
    g_event_listeners.add(event_listener)


def unregister_event_listener(event_listener):
    global g_event_listeners
    g_event_listeners.remove(event_listener)


def register_animator(animator):
    global g_animators
    g_animators.add(animator)


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


def main_loop(screen):
    global g_animators
    global g_drawers
    global g_event_listeners
    global g_loop

    g_loop = True

    if check_exit_event not in g_event_listeners:
        register_event_listener(check_exit_event)

    logger.info("Ready")

    previous_frame = time.time()
    last_frame = time.time()

    while g_loop:
        for event in pygame.event.get():
            for event_listener in g_event_listeners:
                event_listener(event)

        frame_interval = last_frame - previous_frame
        if frame_interval <= 0.0:
            # avoid divisions by zero
            frame_interval = 0.00001
        for animator in g_animators:
            animator(frame_interval)

        for (layer, _, drawer) in g_drawers:
            drawer.draw(screen)
        pygame.display.flip()

        previous_frame = last_frame
        last_frame = time.time()

    logger.info("Good bye")
