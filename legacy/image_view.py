#!/usr/bin/python3
import threading

import pygame
import abstract

import logging

from legacy import spinner, image_save
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
        self.btn_rect = pygame.Rect(0, 0, 0, 0)
        self.clock = pygame.time.Clock()
        self.caller: abstract.GUIActivity = None
        self.spinner: spinner.Spinner = None
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 32)
        self.loaded = False
        self.max_width = 1200
        self.max_height = 800
        self.true_image = pygame.Surface((1,1))

    def start(self, file=None, ssm: spritesheet_manager.SpritesheetManager = None,
              fs: abstract.FileSystemInterface = None, **data: dict):
        for i in ['file', 'fs', 'ssm']:
            if eval(i) is None:
                raise ValueError(f'{i} is a required parameter')
            setattr(self, i, eval(i))
        self.caller = data['calling_activity']
        self.spinner = spinner.EmptySquareSpinner(self.surface.get_size(), pygame.Color('red'))
        self.spinner.start()
        threading.Thread(target=self.load_image, name=f'ImageView::FileLoader::{repr(file)}', daemon=True).start()
        threading.Thread(target=self.draw_loop, name=f'ImageView::DrawLoop::{repr(file)}', daemon=True).start()

    def load_image(self):
        self.loaded = False
        l.debug('Loading image from filesystem...')
        image = self.fs.get_image(self.file)
        self.true_image = image
        if image.get_width()>self.max_width:
            frac = image.get_width()/self.max_width
            image = pygame.transform.scale(image, (int(image.get_width()/frac), int(image.get_height()/frac)))
        if image.get_height()>self.max_height:
            frac = image.get_height()/self.max_height
            image = pygame.transform.scale(image, (int(image.get_width()/frac), int(image.get_height()/frac)))
        self.image = image
        self.btn_rect.width = self.image.get_width()
        self.btn_rect.top = self.image.get_height()
        self.btn_rect.height = 48
        l.debug('Image loaded!')

    def draw_loop(self):
        while self.running:
            self.draw()
            self.clock.tick(10)

    def draw(self):
        with self.surface_lock:
            if self.image is not None:
                self.surface.blit(self.image, (0, 0))
                pygame.draw.rect(self.surface, pygame.Color('white'), self.btn_rect, 5)
                t = self.font.render("Prepare for publishing", True, pygame.Color('white'))
                tr = t.get_rect()
                tr.center = self.btn_rect.center
                self.surface.blit(t, tr)
                if self.surface.get_size() != self.image.get_size() and not self.loaded:
                    l.info('image size update detected!')
                    self.loaded = True
                    try:
                        self.activity_manager.update_screen_size((self.image.get_width(), self.image.get_height() +
                                                                  self.btn_rect.height))
                    except AttributeError:
                        l.error('My activity manager did not attach!')
                    self.surface = pygame.Surface((self.image.get_width(), self.image.get_height() +
                                                   self.btn_rect.height))
                    self.spinner.stop()
            else:
                l.debug('waiting for image to load...')
                self.surface.blit(self.spinner.surface, (0, 0))

    def stop(self):
        self.running = False

    def respond_to_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_rect.collidepoint(*event.pos):
                self.activity_manager.start_other_activity(image_save.ImageSaver(self.surface.get_size()),
                                                           image=self.true_image, return_to=self.caller)
            else:
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
