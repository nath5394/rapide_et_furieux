#!/usr/bin/env python3

from .laser import ForwardLaser


CATEGORY_GUNS = 0
CATEGORY_GUIDED = 1
CATEGORY_COUNTER_MEASURES = 2

CATEGORIES = {
    'guns': CATEGORY_GUNS,  # straight forward only
    'missiles and turrets': CATEGORY_GUIDED,  # guided
    'counter-measures': CATEGORY_COUNTER_MEASURES,  # backward only
}

WEAPONS = [
    ForwardLaser,
]
