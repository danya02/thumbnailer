#!/usr/bin/python3
import random

import pygame
import logging
import colorsys

l = logging.getLogger(__name__)


# color.py - Miscellaneous helper functions for color manipulation
# Copyright (C) 2019 Danya Generalov (https://github.com/danya02)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

def clamp(val: int) -> float:
    return val / 255


def boost(val: float) -> int:
    return int(val * 255)


def random_pure_color() -> pygame.Color:
    return pygame.Color(*[boost(i) for i in colorsys.hsv_to_rgb(random.random(), 1, 1)])


def advance_color_wheel(color: pygame.Color, amount: float) -> pygame.Color:
    r, g, b = [clamp(i) for i in tuple(color)[:3]]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h += amount
    while h > 1: h -= 1
    while h < 0: h += 1
    r, g, b = map(boost, colorsys.hsv_to_rgb(h, s, v))
    return pygame.Color(r, g, b)
