#!/usr/bin/env python3

from . import common
from . import laser
from . import machinegun
from . import mine
from . import missile
from . import oil
from . import shield
from . import shell


def get_weapons():
    return {
        # Weapons must implement a method 'activate(car)'
        # which we return a gun object with methods: 'deactivate()' and 'fire()'
        common.CATEGORY_GUNS: [
            laser.ForwardLaserGenerator(),
            shell.TankShellGenerator(),
        ],
        common.CATEGORY_GUIDED: [
            laser.AutomaticLaserGenerator(),
            machinegun.MachineGunGenerator(),
            missile.GuidedMissileGenerator(),
        ],
        common.CATEGORY_COUNTER_MEASURES: [
            shield.ShieldGenerator(),
            mine.MineGenerator(),
            oil.OilGenerator(),
        ],
    }


def get_weapons_probabilities():
    # must be kept sorted by probabilities
    return [
        # probability, weapon, ammos
        (1.0, laser.ForwardLaserGenerator, 10),
        (1.0, shell.TankShellGenerator, 1),
        (1.0, laser.AutomaticLaserGenerator, 5),
        (1.0, machinegun.MachineGunGenerator, 3),
        (1.0, missile.GuidedMissileGenerator, 1),
        (1.0, shield.ShieldGenerator, 1),
        (1.0, mine.MineGenerator, 1),
        (1.0, oil.OilGenerator, 1),
    ]
