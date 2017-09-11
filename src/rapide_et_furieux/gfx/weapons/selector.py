import pygame

from . import common
from . import get_weapons


class WeaponSelector(object):
    COLORS = {
        'none': {
            'high': (255, 204, 0, 128),
            'low': (231, 185, 0, 128),
        },
        'unselected': {
            'high': (255, 204, 0, 255),
            'low': (195, 188, 0, 255),
        },
        'selected': {
            'high': (255, 246, 0, 255),
            'low': (195, 188, 0, 255),
        },
    }
    CATEGORY_NAME_SIZE = (300, 36)
    WEAPON_SIZE = (300, 48)
    WEAPON_ICON_SIZE = (100, 48)
    WEAPON_NAME_SIZE = (200, 48)
    WIDTH_RECT = 2

    def __init__(self, race_track, player_car, position=(0, -1)):
        self.race_track = race_track
        self.player_car = player_car
        self.position = position

        self.font = pygame.font.Font(None, self.CATEGORY_NAME_SIZE[1] - 5)

        self.image = None

        self.weapons = get_weapons()
        self.max_weapon_per_category = 0
        for category in self.weapons.values():
            self.max_weapon_per_category = max(
                self.max_weapon_per_category, len(category)
            )

        self.active_category = -1
        self.active_weapon = None

        self.player_car.weapon_observers.add(self.refresh)
        self.refresh()

    def refresh(self):
        if self.active_weapon is not None:
            self.active_category = self.active_weapon.category

        if (self.active_weapon is None and
                len(self.player_car.weapons.keys()) > 0):
            weapon = list(self.player_car.weapons.keys())[0]
            if self.player_car.weapons[weapon] > 0:
                self.active_weapon = weapon.activate(
                    self.race_track, self.player_car
                )
                for category_idx in range(0, common.NB_CATEGORIES):
                    wps = self.weapons[category_idx]
                    if weapon in wps:
                        self.active_category = category_idx
                        break

        self.image = pygame.Surface(
            (
                max(self.CATEGORY_NAME_SIZE[0], self.WEAPON_SIZE[0]) *
                common.NB_CATEGORIES + 1,
                self.CATEGORY_NAME_SIZE[1] +
                (self.max_weapon_per_category * self.WEAPON_SIZE[1]) + 1
            ),
            flags=pygame.SRCALPHA
        )
        self.image = self.image.convert_alpha()

        self.image.fill(self.COLORS['none']['low'])

        x = 0
        for category_idx in range(0, common.NB_CATEGORIES):
            nb = 0
            wps = self.weapons[category_idx]
            for weapon in wps:
                if weapon not in self.player_car.weapons:
                    continue
                nb += self.player_car.weapons[weapon]

            colors = self.COLORS[
                'none'
                if nb <= 0 else
                'selected'
                if category_idx == self.active_category else
                'unselected'
            ]

            pygame.draw.rect(
                self.image, colors['low'],
                (
                    (self.CATEGORY_NAME_SIZE[0] * x, 0),
                    self.CATEGORY_NAME_SIZE
                ),
                0
            )
            pygame.draw.rect(
                self.image, colors['high'],
                (
                    (self.CATEGORY_NAME_SIZE[0] * x - 1, 0),
                    (
                        self.CATEGORY_NAME_SIZE[0] + 2,
                        self.CATEGORY_NAME_SIZE[1] + 2,
                    )
                ),
                self.WIDTH_RECT
            )
            category_name = common.CATEGORY_NAMES[category_idx]
            category_name = self.font.render(
                "{} - {} ({})".format(category_idx + 1, category_name, nb),
                True, colors['high'],
            )
            category_name_actual_size = category_name.get_size()
            self.image.blit(
                category_name,
                (
                    (self.CATEGORY_NAME_SIZE[0] -
                     category_name_actual_size[0]) / 2 +
                    self.CATEGORY_NAME_SIZE[0] * x,
                    (self.CATEGORY_NAME_SIZE[1] -
                     category_name_actual_size[1]) / 2,
                )
            )

            if self.active_category != x:
                x += 1
                continue

            y = 0
            wps = self.weapons[category_idx]
            for weapon in wps:
                nb = 0
                if weapon in self.player_car.weapons:
                    nb = self.player_car.weapons[weapon]

                colors = self.COLORS[
                    'none'
                    if nb <= 0 else
                    'selected'
                    if (self.active_weapon is None or
                        weapon == self.active_weapon.parent)
                    else
                    'unselected'
                ]
                pygame.draw.rect(
                    self.image, colors['low'],
                    (
                        (
                            self.CATEGORY_NAME_SIZE[0] * x,
                            self.CATEGORY_NAME_SIZE[1] +
                            (self.WEAPON_SIZE[1] * y)
                        ),
                        self.WEAPON_SIZE
                    ),
                    0
                )
                pygame.draw.rect(
                    self.image, colors['high'],
                    (
                        (
                            self.CATEGORY_NAME_SIZE[0] * x - 1,
                            self.CATEGORY_NAME_SIZE[1] +
                            (self.WEAPON_SIZE[1] * y) - 1
                        ),
                        (
                            self.WEAPON_SIZE[0] + 2,
                            self.WEAPON_SIZE[1] + 2,
                        ),
                    ),
                    self.WIDTH_RECT
                )
                self.image.blit(
                    weapon.image,
                    (
                        (self.CATEGORY_NAME_SIZE[0] * x) +
                        ((self.WEAPON_ICON_SIZE[0] -
                            weapon.image.get_size()[0]) / 2),
                        (self.CATEGORY_NAME_SIZE[1] +
                            (self.WEAPON_SIZE[1] * y) +
                            (self.WEAPON_ICON_SIZE[1] -
                             weapon.image.get_size()[1]) / 2),
                    )
                )
                weapon_name = self.font.render(
                    "{}x {}".format(nb, str(weapon)), True, colors['high']
                )
                self.image.blit(
                    weapon_name,
                    (
                        (self.CATEGORY_NAME_SIZE[0] * x) +
                        self.WEAPON_ICON_SIZE[0] +
                        ((self.WEAPON_NAME_SIZE[0] -
                            weapon_name.get_size()[0]) / 2),
                        (self.CATEGORY_NAME_SIZE[1] +
                            (self.WEAPON_SIZE[1] * y) +
                            (self.WEAPON_NAME_SIZE[1] -
                             weapon_name.get_size()[1]) / 2),
                    )
                )

                y += 1

            x += 1

    def on_key(self, event):
        if event.type != pygame.KEYDOWN:
            return

        k = event.key
        if k >= pygame.K_1 and k <= pygame.K_9:
            k -= pygame.K_1
        elif k >= pygame.K_KP1 and k <= pygame.K_KP9:
            k -= pygame.K_KP1
        else:
            return

        if k >= common.NB_CATEGORIES or k < 0:
            return

        idx = -1
        if k != self.active_category or self.active_weapon is None:
            self.active_category = k
            self.active_weapon = None
        else:
            self.active_category = k
            wps = self.weapons[self.active_category]
            for (idx, weapon) in enumerate(wps):
                if weapon == self.active_weapon.parent:
                    break
            else:
                assert False

        wps = self.weapons[self.active_category]
        wps = wps[idx + 1:] + wps[:idx]
        if idx >= 0:
            wps.append(self.active_weapon.parent)

        if self.active_weapon is not None:
            self.active_weapon.deactivate()
            self.active_weapon = None
        for weapon in wps:
            if weapon not in self.player_car.weapons:
                continue
            nb = self.player_car.weapons[weapon]
            if nb > 0:
                self.active_weapon = weapon.activate(
                    self.race_track, self.player_car
                )
                break

        self.refresh()

    def draw(self, screen):
        screen_size = screen.get_size()
        img_size = self.image.get_size()
        position = (
            screen_size[0] + self.position[0] - img_size[0]
            if self.position[0] < 0 else
            self.position[0],
            screen_size[1] + self.position[1] - img_size[1]
            if self.position[1] < 0 else
            self.position[1],
        )
        screen.blit(self.image, position)
