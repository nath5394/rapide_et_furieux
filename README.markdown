# Rapide et furieux

Crappy, buggy, but kind of fun car game with a bunch of weapons.

This game is NOT complete. You can race, but there is no menu, no lap counter,
no end to the race, no .. well .. it's probably easier to tell you what there is:

- Race track editor
- Artificial Intelligence
- Weapons
- Collision detection (buggy at times)


## Screenshot & Video

<a href="https://youtu.be/8cooFgPPiwI">
 <img src="screenshots/shot0001.jpg" width="640" height="480" />
</a>


## Installation

```shell
sudo apt install python3-numpy
sudo pip3 install pygame

cd /tmp
git clone https://github.com/jflesch/rapide_et_furieux.git
cd rapide_et_furieux
sudo python3 ./setup.py install  # or use python-virtualenv, as you prefer
```


## Usage

```shell
ref-game src/rapide_et_furieux/maps/smkart.map
```

## Controls

```
A - left arrow - turn left
D - right arrow - turn right
W - up arrow - accelerate
S - down arrow - brake / reverse
Ctrl left - Ctrl Right - fire
1, 2 and 3 - switch weapon category / switch weapon
` (top-left of the keyboard, just below escape) - Console
```

## Race track editor

```shell
ref-editor src/rapide_et_furieux/maps/simple.map
```

Escape to exit.


### Tiles

On the left are the available tiles.

Scroll wheel to browse the tiles.

Left click on any of them to select it. Left click on race track tile spaces to place it.
Right click to stop placing this tile.

Middle-click to delete a tile.


### Objects

Below the tile list are the objects. They can be placed as you wish on top the tiles.


### Special elements

In the tile list, there are 3 special elements placed first:
- Collision borders: red ; cars can't go through
- Blue: waypoints / checkpoints ; IA will follow them, and game use them to as checkpoints
  that the IA and the player must go through to complete each lap
- Green: 'crap area' (like sand ; always rectangular). Where cars are slow down
  and where tire friction sucks


## Track settings

Tracks are stored in JSON format.
In this JSON, there is a 'game\_settings' section that can be changed.
See `src/rapide_et_furieux/util.py:GAME_SETTINGS_TEMPLATE` to know
which values can be changed.



## Pre-computation

IA path finding algorithm needs the track to be precomputed in order to work efficiently.

```shell
ref-precompute src/rapide_et_furieux/maps/simple.map
```


## Thanks to

<a href="http://www.kenney.nl/">Kenney</a> for the graphisms.
Please consider donating them money if you decide to reuse the graphics
or work on this game.

Some sounds come from Kenney, other were public domain (or CC0).
