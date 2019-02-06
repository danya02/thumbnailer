#!/usr/bin/python3
import colorsys
import random
import threading

import pygame

import logging

from legacy import color

l = logging.getLogger(__name__)


# spinner.py - Various loading spinnies.
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

class Spinner:
    @property
    def surface(self):
        with self.surface_lock:
            return self._surface

    @surface.setter
    def surface(self, value):
        self._surface = value

    def __init__(self, size: (int, int)):
        self.surface = pygame.Surface(size)
        self.running = False
        self.surface_lock = threading.RLock()
        self.clock = pygame.time.Clock()
        self.framerate = 10

    def start(self):
        self.running = True
        threading.Thread(target=self.draw_loop, name='Spinner draw loop', daemon=True).start()

    def stop(self):
        self.running = False

    def draw_loop(self):
        while self.running:
            with self.surface_lock:
                self.draw()
            self.clock.tick(self.framerate)

    def draw(self):
        raise NotImplementedError

    @classmethod
    def create_randomised(cls, size):
        raise NotImplementedError


class EmptySquareSpinner(Spinner):
    @classmethod
    def create_randomised(cls, size):
        color = tuple([int(i * 255) for i in colorsys.hsv_to_rgb(random.random(), 1, 1)])
        c = EmptySquareSpinner(size, pygame.Color(*color))
        #c.bgcolor = pygame.Color(64,0,0)
        c.spinner_phase = random.randint(0, 7)
        c.framerate = random.randint(5, 20)
        c.delta = random.choice([-1, 1])
        c.color_shift_amount = (random.random() / 50) * random.choice([1, -1])
        #c.do_color_shift = True
        return c

    def __init__(self, size: (int, int), fgcolor: pygame.Color, bgcolor: pygame.Color = pygame.Color('black'),
                 rect_size=10, roff=20):
        super().__init__(size)
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.spinner_phase = 0
        midx = self.surface.get_width() // 2
        midy = self.surface.get_height() // 2
        self.rects = [pygame.Rect(0, 0, rect_size, rect_size) for _ in range(8)]
        self.rects[0].center = (midx - roff, midy - roff)
        self.rects[1].center = (midx, midy - roff)
        self.rects[2].center = (midx + roff, midy - roff)
        self.rects[3].center = (midx + roff, midy)
        self.rects[4].center = (midx + roff, midy + roff)
        self.rects[5].center = (midx, midy + roff)
        self.rects[6].center = (midx - roff, midy + roff)
        self.rects[7].center = (midx - roff, midy)
        self.delta = 1
        self.do_color_shift = False
        self.color_shift_amount = 0.0

    def draw(self):
        self.surface.fill(self.bgcolor)
        for i, j in enumerate(self.rects):
            if i != self.spinner_phase:
                self.surface.fill(self.fgcolor, j)
        self.spinner_phase += self.delta
        if self.spinner_phase >= 8:
            self.spinner_phase = 0
        if self.spinner_phase <= -1:
            self.spinner_phase = 7
        if self.do_color_shift:
            self.fgcolor = color.advance_color_wheel(self.fgcolor, self.color_shift_amount)
            self.bgcolor = color.advance_color_wheel(self.bgcolor, self.color_shift_amount)
