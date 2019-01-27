#!/usr/bin/python3
import threading

import pygame
import abstract

import logging

import spinner
import spritesheet_manager

l = logging.getLogger(__name__)


# image_view.py - Activity to show images in full-window mode.
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

class ImageView(abstract.GUIActivity):
    def __init__(self):
        super().__init__()
        self.file = None
        self.fs: abstract.FileSystemInterface = None
        self.ssm: spritesheet_manager.SpritesheetManager = None
        self.image: pygame.Surface = None
        self.running = True
        self.surface = pygame.Surface((800, 600))
        self.surface.fill(pygame.Color('white'))
        self.surface_lock = threading.Lock()
        self.clock = pygame.time.Clock()
        self.caller: abstract.GUIActivity = None
        self.spinner: spinner.Spinner = None

    def start(self, file=None, ssm: spritesheet_manager.SpritesheetManager = None,
              fs: abstract.FileSystemInterface = None, **data: dict):
        for i in ['file', 'fs', 'ssm']:
            if eval(i) is None:
                raise ValueError(f'{i} is a required parameter')
            setattr(self, i, eval(i))
        self.caller = data['calling_activity']
        self.spinner = spinner.EmptySquareSpinner(self.surface.get_size(), pygame.Color('red'))
        self.spinner.start()
        threading.Thread(target=self.load_image, name=f'ImageView::FileLoader::{repr(file)}').start()
        threading.Thread(target=self.draw_loop, name=f'ImageView::DrawLoop::{repr(file)}').start()

    def load_image(self):
        l.debug('Loading image from filesystem...')
        image = self.fs.get_image(self.file)
        self.image = image
        l.debug('Image loaded!')

    def draw_loop(self):
        while self.running:
            self.draw()
            self.clock.tick(10)

    def draw(self):
        with self.surface_lock:
            if self.image is not None:
                self.surface.blit(self.image, (0, 0))
                if self.surface.get_size() != self.image.get_size():
                    l.info('image size update detected!')
                    self.activity_manager.update_screen_size(self.image.get_size())
                    self.surface = pygame.Surface(self.image.get_size())
                    self.spinner.stop()
            else:
                l.debug('waiting for image to load...')
                self.surface.blit(self.spinner.surface, (0,0))

    def stop(self):
        self.running = False

    def respond_to_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.activity_manager.start_other_activity(self.caller)

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, value):
        self._surface = value

    @property
    def surface_lock(self):
        return self._surface_lock

    @surface_lock.setter
    def surface_lock(self, value):
        self._surface_lock = value

    @property
    def activity_manager(self):
        return self._am

    @activity_manager.setter
    def activity_manager(self, value):
        self._am = value
