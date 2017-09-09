#!/usr/bin/env python3

from . import laser
from . import machinegun
from . import mine
from . import missile
from . import oil
from . import shield
from . import shell


CATEGORY_GUNS = 0  # straight forward only
CATEGORY_GUIDED = 1  # guided
CATEGORY_COUNTER_MEASURES = 2  # backward only
NB_CATEGORIES = 3

CATEGORY_NAMES = {
    CATEGORY_GUNS: 'Guns',
    CATEGORY_GUIDED: 'Smart weapons',
    CATEGORY_COUNTER_MEASURES: 'Counter-measures',
}

def get_weapons():
    return {
        # Weapons must implement a method 'activate(car)'
        # which we return a gun object with methods: 'deactivate()' and 'fire()'
        CATEGORY_GUNS: [
            laser.ForwardLaser(),
            shell.TankShell(),
        ],
        CATEGORY_GUIDED: [
            laser.AutomaticLaser(),
            machinegun.MachineGun(),
            missile.GuidedMissile(),
        ],
        CATEGORY_COUNTER_MEASURES: [
            shield.Shield(),
            mine.Mine(),
            oil.Oil(),
        ],
    }


def get_weapons_probabilities():
    # must be kept sorted by probabilities
    return [
        # probability, weapon, ammos
        (1.0, laser.ForwardLaser, 5),
        (1.0, shell.TankShell, 1),
        (1.0, laser.AutomaticLaser, 3),
        (1.0, machinegun.MachineGun, 3),
        (1.0, missile.GuidedMissile, 1),
        (1.0, shield.Shield, 1),
        (1.0, mine.Mine, 1),
        (1.0, oil.Oil, 1),
    ]
