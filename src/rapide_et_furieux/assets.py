TILE_SIZE = (128, 128)

MUSICS = {
    ("rapide_et_furieux.music", "Mission Plausible.ogg"),
    ("rapide_et_furieux.music", "Game Over.ogg"),
    ("rapide_et_furieux.music", "Italian Mom.ogg"),
    ("rapide_et_furieux.music", "Wacky Waiting.ogg"),
    ("rapide_et_furieux.music", "Retro Mystic.ogg"),
    ("rapide_et_furieux.music", "Retro Polka.ogg"),
    ("rapide_et_furieux.music", "Retro Beat.ogg"),
    ("rapide_et_furieux.music", "Infinite Descent.ogg"),
    ("rapide_et_furieux.music", "Flowing Rocks.ogg"),
    ("rapide_et_furieux.music", "Time Driving.ogg"),
    ("rapide_et_furieux.music", "Polka Train.ogg"),
    ("rapide_et_furieux.music", "German Virtue.ogg"),
    ("rapide_et_furieux.music", "Night at the Beach.ogg"),
    ("rapide_et_furieux.music", "Retro Comedy.ogg"),
    ("rapide_et_furieux.music", "Retro Reggae.ogg"),
    ("rapide_et_furieux.music", "Mishief Stroll.ogg"),
    ("rapide_et_furieux.music", "Alpha Dance.ogg"),
    ("rapide_et_furieux.music", "Swinging Pants.ogg"),
    ("rapide_et_furieux.music", "Drumming Sticks.ogg"),
    ("rapide_et_furieux.music", "Sad Descent.ogg"),
    ("rapide_et_furieux.music", "Cheerful Annoyance.ogg"),
    ("rapide_et_furieux.music", "Farm Frolics.ogg"),
    ("rapide_et_furieux.music", "Space Cadet.ogg"),
    ("rapide_et_furieux.music", "Sad Town.ogg"),
}

SOUNDS = {
    'shoot': {
        ("rapide_et_furieux.sounds", "laser%d.ogg" % idx)
        for idx in range(1, 10)
    },
}

CARS = [
    ("rapide_et_furieux.gfx.cars", "car_%s_%d.png" % (color, idx))
    for idx in range(1, 6)
    for color in ['black', 'blue', 'green', 'red', 'yellow']
]

MOTORCYCLES = [
    ("rapide_et_furieux.gfx.cars", "motorcycle_%s.png" % (color))
    for color in ['black', 'blue', 'green', 'red', 'yellow']
]

EXPLOSIONS = [
    [
        ("rapide_et_furieux.gfx.explosions", "regularExplosion%02d.png" % idx)
        for idx in range(0, 9)
    ],
    [
        ("rapide_et_furieux.gfx.explosions", "simpleExplosion%02d.png" % idx)
        for idx in range(0, 9)
    ],
    [
        ("rapide_et_furieux.gfx.explosions", "sonicExplosion%02d.png" % idx)
        for idx in range(0, 9)
    ],
]

OBJECTS = [
    ("rapide_et_furieux.gfx.objects", "arrow_white.png"),
    ("rapide_et_furieux.gfx.objects", "arrow_yellow.png"),
    ("rapide_et_furieux.gfx.objects", "barrel_blue_down.png"),
    ("rapide_et_furieux.gfx.objects", "barrel_blue.png"),
    ("rapide_et_furieux.gfx.objects", "barrel_red_down.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_red.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_red_race.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_white.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_white_race.png"),
    ("rapide_et_furieux.gfx.objects", "cone_down.png"),
    ("rapide_et_furieux.gfx.objects", "cone_straight.png"),
    ("rapide_et_furieux.gfx.objects", "lights.png"),
    ("rapide_et_furieux.gfx.objects", "oil.png"),
    ("rapide_et_furieux.gfx.objects", "rock1.png"),
    ("rapide_et_furieux.gfx.objects", "rock2.png"),
    ("rapide_et_furieux.gfx.objects", "rock3.png"),
    ("rapide_et_furieux.gfx.objects", "tent_blue_large.png"),
    ("rapide_et_furieux.gfx.objects", "tent_blue.png"),
    ("rapide_et_furieux.gfx.objects", "tent_red_large.png"),
    ("rapide_et_furieux.gfx.objects", "tent_red.png"),
    ("rapide_et_furieux.gfx.objects", "tires_red_alt.png"),
    ("rapide_et_furieux.gfx.objects", "tires_red.png"),
    ("rapide_et_furieux.gfx.objects", "tires_white_alt.png"),
    ("rapide_et_furieux.gfx.objects", "tires_white.png"),
    ("rapide_et_furieux.gfx.objects", "tree_large.png"),
    ("rapide_et_furieux.gfx.objects", "tree_small.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_empty.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_full.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_overhang_red.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_overhang_striped.png"),
]

POWERUPS = {
    ("rapide_et_furieux.gfx.objets", "powerupYellow_bolt.png"),
}

TILES = [
    ("rapide_et_furieux.gfx.tiles", "land_dirt%02d.png" % idx)
    for idx in range(1, 15)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "land_grass%02d.png" % idx)
    for idx in range(1, 15)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "land_sand%02d.png" % idx)
    for idx in range(1, 15)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "road_asphalt%02d.png" % idx)
    for idx in range(1, 91)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "road_dirt%02d.png" % idx)
    for idx in range(1, 91)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "road_sand%02d.png" % idx)
    for idx in range(1, 91)
]
