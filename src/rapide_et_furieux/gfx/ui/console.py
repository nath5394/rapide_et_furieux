import itertools
import logging
import random

import pygame

from . import FPSCounter
from ... import assets
from ... import util
from ..cars.ia import IACar
from ..weapons import get_weapons


logger = logging.getLogger(__name__)


class CommandDebug(object):
    def __init__(self, race_track):
        self.console = None
        self.race_track = race_track

    def run(self, cmd, args):
        if len(args) > 0:
            if args[0] == "on":
                debug = True
            elif args[0] == "off":
                debug = False
            else:
                self.console.add_line("Debug [on|off]")
                return
            self.race_track.debug = debug
        self.console.add_line("Debug: {}".format(self.race_track.debug))


class CommandShowFPS(object):
    def __init__(self, font, screen_size):
        self.console = None
        self.font = font
        self.screen_size = screen_size

    def run(self, cmd, args):
        fps_counter = FPSCounter(self.font, position=(
            self.screen_size[0] - 128, 0
        ))
        util.register_drawer(assets.OSD_LAYER - 1, fps_counter)
        util.register_animator(fps_counter.on_frame)


class CommandEcho(object):
    def __init__(self, *args, **kwargs):
        self.console = None

    def run(self, cmd, args):
        self.console.add_line(" ".join(args))


class CommandList(object):
    def __init__(self, *args, **kwargs):
        self.console = None

    def run(self, cmd, args):
        self.console.add_line("Available commands:")
        for cmd in self.console.commands:
            self.console.add_line(" {}".format(cmd))


class CommandKillAll(object):
    def __init__(self, race_track, player_car):
        self.console = None
        self.race_track = race_track
        self.player = player_car

    def run(self, cmd, args):
        nb = 0
        for car in list(self.race_track.cars):
            if car is self.player:
                continue
            self.race_track.remove_car(car)
            util.unregister_animator(car.move)
            nb += 1
        self.console.add_line("{} cars removed".format(nb))


class CommandAddAI(object):
    def __init__(self, race_track, player_car, waypoint_mgmt):
        self.console = None
        self.race_track = race_track
        self.player = player_car
        self.waypoints = waypoint_mgmt

        self.iter_car_rsc = iter(itertools.cycle(assets.CARS[1:]))
        self.iter_spawnpoint = iter(itertools.cycle(
            list(self.race_track.tiles.get_spawn_points())[1:]
        ))

    def run(self, cmd, args):
        (spawnpoint, orientation) = next(self.iter_spawnpoint)
        car = IACar(next(self.iter_car_rsc), self.race_track,
                    self.race_track.game_settings,
                    spawnpoint, orientation,
                    waypoint_mgmt=self.waypoints)
        self.race_track.add_car(car)
        util.register_animator(car.move)
        car.can_move = True
        self.console.add_line("AI added")


def simplify_bonus_name(bonus_name):
    bonus_name = bonus_name.lower()
    bonus_name = bonus_name.replace(" ", "")
    return bonus_name


class CommandListBonuses(object):
    def __init__(self, *args, **kwargs):
        self.console = None

    def run(self, cmd, args):
        self.console.add_line("Available bonuses:")
        for bonuses in get_weapons().values():
            for bonus in bonuses:
                self.console.add_line(
                    "  {} - {}".format(
                        simplify_bonus_name(str(bonus)),
                        str(bonus)
                    )
                )


class CommandQuit(object):
    def __init__(self, *args, **kwargs):
        self.console = None

    def run(self, cmd, args):
        self.console.add_line("Quitting")
        util.idle_add(util.exit)


class CommandGetBonus(object):
    def __init__(self, player_car):
        self.console = None
        self.player = player_car

    def run(self, cmd, args):
        bonuses = list(itertools.chain(*list(get_weapons().values())))
        if len(args) <= 0:
            bonus = random.choice(bonuses)
        else:
            for bonus in bonuses:
                if simplify_bonus_name(str(bonus)) == args[0]:
                    break
            else:
                self.console.add_line("Unknown bonus: {}".format(args[0]))
                return
        nb = 1
        if len(args) >= 2:
            nb = int(args[1])
        self.player.add_weapon(bonus, nb)
        self.console.add_line("Bonus {} ({}) added".format(str(bonus), nb))


class Console(logging.Handler):
    PREFERED_FONTS = [
        'ubuntumono',
        'dejavusansmono',
    ]
    FONT_SIZE = 24
    FONT_COLOR = (200, 255, 200, 255)
    BG_COLOR = (64, 200, 64, 64)

    CONSOLE_HEIGHT = 1 / 2  # of the screen height
    GOLDEN_RATIO = 1.61803398875
    HISTORY_MAX = 10

    def __init__(self, commands):
        super().__init__()

        self.commands = commands
        for cmd in commands.values():
            if hasattr(cmd, 'console'):
                cmd.console = self

        self._formatter = logging.Formatter(
            '%(levelname)-6s %(name)s %(message)s'
        )
        logger = logging.getLogger()
        logger.addHandler(self)

        self.visible = False
        self.lines = []

        for fontname in self.PREFERED_FONTS:
            try:
                fontpath = pygame.font.match_font(fontname)
                if fontpath is None:
                    continue
                self.font = pygame.font.Font(fontpath, self.FONT_SIZE)
                break
            except:
                pass
        else:
            self.font = pygame.font.Font(None, self.FONT_SIZE)
            logger.warning("No monospace font found")

        self.prompt = self.font.render("> ", True, self.FONT_COLOR)
        self.typing = ("", self.font.render("", True, self.FONT_COLOR))
        self.history = []
        self.history_idx = 0

        self.valid_chars = list(range(pygame.K_a, pygame.K_z + 1))
        self.valid_chars += list(range(pygame.K_0, pygame.K_9 + 1))
        self.valid_chars += [
            pygame.K_SPACE, pygame.K_SLASH, pygame.K_BACKSLASH,
            pygame.K_COMMA, pygame.K_COLON, pygame.K_UNDERSCORE,
            pygame.K_QUOTE, pygame.K_PLUS, pygame.K_MINUS,
        ]
        self.valid_chars = set(self.valid_chars)
        self.screen_size = None

    def add_line(self, lines):
        for line in lines.split("\n"):
            self.lines.append(self.font.render(line, True, self.FONT_COLOR))
        self.image = None

    def emit(self, record):
        self.add_line(self._formatter.format(record))

    def execute(self, cmd, args):
        if cmd not in self.commands:
            self.add_line("Unknown command: {}".format(cmd))
            return
        try:
            self.commands[cmd].run(cmd, args)
        except Exception as exc:
            logger.error(
                "UNCATCHED EXCEPTION:",
                exc_info=exc
            )

    def on_key(self, event):
        if event.type != pygame.KEYDOWN:
            return False

        k = event.key
        if k == pygame.K_BACKQUOTE:
            self.visible = not self.visible
            logger.info("Console visible: {}".format(self.visible))
            return True

        if not self.visible:
            return False

        if k >= pygame.K_KP0 and k <= pygame.K_KP9:
            k += pygame.K_0 - pygame.K_KP0

        mods = pygame.key.get_mods()
        txt = self.typing[0]
        if k == pygame.K_RETURN or k == pygame.K_KP_ENTER:
            self.add_line("> " + txt)
            self.history.append(txt)
            self.history_idx = len(self.history)

            txt = txt.split(" ")
            cmd = txt[0]
            args = txt[1:]
            self.execute(cmd, args)
            txt = ""
        elif k == pygame.K_BACKSPACE or k == pygame.K_DELETE:
            txt = txt[:-1]
        elif k == pygame.K_PAGEUP:
            self.history_idx -= 1
            if self.history_idx < 0:
                self.history_idx = len(self.history) - 1
            if self.history_idx >= 0:
                txt = self.history[self.history_idx]
        elif k == pygame.K_PAGEDOWN:
            self.history_idx += 1
            if self.history_idx >= len(self.history):
                self.history_idx = 0
            if len(self.history) > 0:
                txt = self.history[self.history_idx]
        elif k == pygame.K_TAB:
            nb = 0
            match = None
            for cmd in self.commands:
                if cmd.startswith(txt):
                    if match is None:
                        match = cmd
                    else:
                        match = util.common_str_prefix([match, cmd])
                    nb += 1
            if match is not None:
                txt = match
            if nb == 1:
                txt += " "
        elif k in self.valid_chars:
            k = chr(k)
            if mods & pygame.KMOD_SHIFT:
                if k == '-':
                    k = '_'
                elif k >= 'a' and k <= 'z':
                    k = chr(ord(k) + ord('A') - ord('a'))
            txt += k
        else:
            # wasn't for us
            return False

        self.typing = (
            txt,
            self.font.render(txt, True, self.FONT_COLOR)
        )
        self.refresh()
        return True

    def refresh(self):
        if self.screen_size is None:
            return

        (w, h) = self.screen_size
        h *= self.CONSOLE_HEIGHT

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(
            self.image,
            self.BG_COLOR,
            ((0, 0), (w, h)),
        )

        typing_h = max(self.FONT_SIZE, self.typing[1].get_size()[1],
                       self.prompt.get_size()[1])
        h -= typing_h
        w = 0

        self.image.blit(self.prompt, (w, h))
        w += self.prompt.get_size()[0]

        self.image.blit(self.typing[1], (w, h))
        w += self.typing[1].get_size()[0]

        pygame.draw.rect(
            self.image, self.FONT_COLOR,
            (
                (w + 3, h + 3),
                ((self.FONT_SIZE - 6) / self.GOLDEN_RATIO,
                 self.FONT_SIZE - 6),
            )
        )

        for (lidx, line) in enumerate(reversed(self.lines)):
            h -= line.get_size()[1]
            if h < 0:
                break
            self.image.blit(
                line,
                (0, h)
            )

        self.lines = self.lines[len(self.lines) - lidx - 1:]

    def draw(self, screen):
        if not self.visible:
            return
        if self.screen_size is None:
            self.screen_size = screen.get_size()
        if self.image is None:
            self.refresh()
        screen.blit(self.image, (0, 0))
