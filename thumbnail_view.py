#!/usr/bin/python3
import logging
import threading
from typing import List

import pygame

import abstract
import filesystem
import image_view
import spinner
import spritesheet_manager

l = logging.getLogger(__name__)


# thumbnail_view.py - Activity to examine the thumbnail list.
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


class ThumbnailView(abstract.GUIActivity):

    @property
    def activity_manager(self):
        return self._activity_manager

    @activity_manager.setter
    def activity_manager(self, value):
        self._activity_manager = value

    @property
    def surface_lock(self):
        return self._surface_lock

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, value):
        self._surface = value

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value

    def __init__(self):
        super().__init__()
        self.running = False
        self.surface: pygame.Surface = None
        self.surface_lock = threading.Lock()
        self.draw_thread: threading.Thread = None
        self.max_size = pygame.Rect(0, 0, 100, 100)
        self.filesystem = filesystem.LocalFilesystem('/home/danya/Pictures',0.01)
        self.thumbnails = {}
        self.grid: List[List[pygame.Rect]] = []
        self.thumbs: List[pygame.Surface] = []
        self.filelist: List[object] = []
        self.spinnies: List[List[spinner.Spinner]] = []
        self.clock = pygame.time.Clock()
        self.spritesheet_manager = spritesheet_manager.SpritesheetManager('spritesheets/data.json', self.filesystem)
        self.current_offset = 0
        self.files_amt = 0
        self.buttons_top = [('<', self.page_back_check, self.page_back),
                            ('>', self.page_forward_check, self.page_forward)]
        self.buttons_top_rects_acts = []
        self.buttons_bottom = []
        self.buttons_bottom_rects_acts = []
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 32)
        self.thumb_area = pygame.Rect(0, 32, 800, 600)

    @property
    def items_on_page(self):
        return len(self.grid) * len(self.grid[0])

    def page_back_check(self):
        return self.current_offset != 0

    def page_back(self):
        self.current_offset = max(0, self.current_offset - self.items_on_page)
        self.generate_grid()

    def page_forward_check(self):
        return self.current_offset != self.files_amt - self.items_on_page

    def page_forward(self):
        self.current_offset = min(self.files_amt - self.items_on_page, self.current_offset + self.items_on_page)
        self.generate_grid()

    def start(self, **data):
        self.running = True
        self.surface = pygame.Surface((800, 864))
        self.generate_grid()
        self.draw_thread = threading.Thread(name='ThumbnailView::DrawThread', target=self.draw_loop, daemon=True)
        self.draw_thread.start()
        self.load_thumbs()

    def respond_to_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            l.info(f'Click at {event.pos}!')
            offset = self.current_offset
            with self.surface_lock:
                for i in self.buttons_top_rects_acts + self.buttons_bottom_rects_acts:
                    if i[0].collidepoint(*event.pos):
                        i[1]()
                        return
            try:
                for linerect in self.grid:
                    for rect in linerect:
                        offset += 1
                        if rect.collidepoint(*event.pos):
                            file = self.filelist[offset]
                            self.activity_manager.start_other_activity(image_view.ImageView(), file=file,
                                                                       ssm=self.spritesheet_manager, fs=self.filesystem)
                            return
            except IndexError:
                pass

    def stop(self):
        self.running = False

    def generate_grid(self):
        self.grid = []
        self.spinnies = []
        for y in range(self.thumb_area.top, self.thumb_area.right, self.max_size.height):
            newlist = []
            spinline = []
            for x in range(self.thumb_area.left, self.thumb_area.right, self.max_size.width):
                rect = self.max_size.copy()
                rect.x = x
                rect.y = y
                newlist.append(rect)
                spinnerobj = spinner.EmptySquareSpinner.create_randomised(rect.size)
                spinnerobj.start()
                spinline.append(spinnerobj)
            self.grid.append(newlist)
            self.spinnies.append(spinline)

    def load_thumbs(self):
        files = self.filesystem.get_file_list()
        self.files_amt = len(files)
        files = iter(files)
        self.thumbs = []
        self.filelist = []
        try:
            while self.running:
                file = next(files)
                # try:
                image = self.spritesheet_manager.get_thumbnail(file, self.max_size.size)
                if image:
                    self.thumbs.append(image)
                    self.filelist.append(file)
                # except:pass
        except StopIteration:
            pass

    def draw_loop(self):
        while self.running:
            self.draw()
            self.clock.tick(24)

    def draw(self):
        with self.surface_lock:
            self.surface.fill(pygame.Color('black'))
            # Draw buttons on top
            self.buttons_top_rects_acts = []
            xpos = 0
            for btn in self.buttons_top:
                state = btn[1]()
                text = self.font.render(btn[0], True, pygame.Color('white' if state else 'grey'))
                rect = text.get_rect()
                outer_rect = rect.inflate(5, 5)
                outer_rect.top = 0
                xpos += 5
                outer_rect.left = xpos
                rect.center = outer_rect.center
                pygame.draw.rect(self.surface, pygame.Color('white' if state else 'grey'), outer_rect, 3)
                self.surface.blit(text, rect)
                xpos += outer_rect.width
                if state:
                    self.buttons_top_rects_acts.append((outer_rect, btn[2]))
            # Draw buttons on bottom
            self.buttons_bottom_rects_acts = []
            xpos = 0
            for btn in self.buttons_bottom:
                state = btn[1]()
                text = self.font.render(btn[0], True, pygame.Color('white' if state else 'grey'))
                rect = text.get_rect()
                outer_rect = rect.inflate(5, 5)
                outer_rect.top = self.thumb_area.bottom
                xpos += 5
                outer_rect.left = xpos
                rect.center = outer_rect.center
                pygame.draw.rect(self.surface, pygame.Color('white' if state else 'grey'), outer_rect, 3)
                self.surface.blit(text, rect)
                xpos += outer_rect.width
                if state:
                    self.buttons_bottom_rects_acts.append((outer_rect, btn[2]))

            # Draw thumbnails
            offset = self.current_offset
            for line, spinline in zip(self.grid, self.spinnies):
                for cell, spinnerobj in zip(line, spinline):
                    offset += 1
                    try:
                        img = self.thumbs[offset]
                        rect: pygame.Rect = img.get_rect()
                        rect.center = cell.center
                        self.surface.blit(img, rect)
                        spinnerobj.stop()
                    except IndexError:
                        if offset < self.files_amt:
                            self.surface.blit(spinnerobj.surface, cell)

    @surface_lock.setter
    def surface_lock(self, value):
        self._surface_lock = value


if __name__ == '__main__':
    pygame.init()
    v = ThumbnailView()
    v.start()
    s = pygame.display.set_mode(v.surface.get_size())
    c = pygame.time.Clock()
    while 1:
        with v.surface_lock:
            s.blit(v.surface, (0, 0))
            pygame.display.flip()
        c.tick(10)
