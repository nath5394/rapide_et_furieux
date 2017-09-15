import itertools
import logging

import pygame

from .. import assets
from .. import util


logger = logging.getLogger(__name__)

g_channels = []  # [(reserved, channel), ...]
g_channel_idx = 0
g_screen_size = (0, 0)


def pre_init():
    pygame.mixer.pre_init(44100, -16, 2, 1024)


def init(screen_size):
    global g_channels
    global g_screen_size

    pygame.mixer.set_num_channels(32)
    nb = pygame.mixer.get_num_channels()
    g_channels = [(False, pygame.mixer.Channel(idx)) for idx in range(0, nb)]
    g_screen_size = screen_size


def _get_free_channel():
    global g_channels
    global g_channel_idx

    for g_channel_idx in itertools.chain(
                range(g_channel_idx, len(g_channels)),
                range(0, g_channel_idx)
            ):
        if g_channels[g_channel_idx][0]:  # reserved
            continue
        if not g_channels[g_channel_idx][1].get_busy():
            break
    else:
        # all channels are busy --> looking for any busy non-reserved
        # channels
        for g_channel_idx in itertools.chain(
                    range(g_channel_idx + 1, len(g_channels)),
                    range(0, g_channel_idx + 1)
                ):
            if not g_channels[g_channel_idx][0]:  # not reserved
                break
        if g_channel_idx >= len(g_channels):
            g_channel_idx = 0
        g_channels[g_channel_idx][1].stop()
    channel = g_channels[g_channel_idx][1]
    return (channel, g_channel_idx)


def reserve_channel():
    global g_channels

    (channel, channel_idx) = _get_free_channel()
    g_channels[channel_idx] = (True, channel)
    return channel


def unreserve_channel(reserved_channel):
    global g_channels

    for (idx, (reserved, channel)) in enumerate(g_channels):
        if channel == reserved_channel:
            assert reserved
            break
    else:
        assert False
    g_channels[idx] = (False, reserved_channel)


def unreserve_all():
    global g_channels

    for (idx, (reserved, channel)) in enumerate(list(g_channels)):
        g_channels[idx] = (False, channel)


def play(snd, balance=(1.0, 1.0), channel=None, queue=False, loops=0,
         fadeout=0):
    sound = assets.get_resource(snd[:2])

    if channel is None:
        (channel, _) = _get_free_channel()

    balance = (balance[0] * snd[2], balance[0] * snd[2])
    channel.set_volume(*balance)

    if not queue:
        channel.play(sound, loops, fade_ms=fadeout)
    else:
        channel.queue(sound)


def play_from_screen(sound, relative_sprite, channel=None, queue=False,
                     loops=0, fadeout=0):
    global g_screen_size
    MAX_DIST = g_screen_size[0]

    pos = relative_sprite.absolute
    size = relative_sprite.size
    pos = (pos[0] + (size[0] / 2), pos[1] + (size[1] / 2))

    dist = util.distance_pt_to_pt(
        (g_screen_size[0] / 2, g_screen_size[1] / 2),
        pos
    )
    if dist > MAX_DIST:
        return

    volume = 1.0 - (dist / MAX_DIST)

    w = g_screen_size[0]

    balance_r = util.clamp(
        (pos[0] + (w / 2)) / (2 * w),
        0.0, 1.0
    )
    balance_l = 1.0 - balance_r

    if balance_l != 0 and balance_r != 0:
        factor = min(
            1.0 / balance_l,
            1.0 / balance_r
        )
        balance_l *= factor
        balance_r *= factor

    play(sound, (volume * balance_l, volume * balance_r), channel, queue, loops,
         fadeout)
