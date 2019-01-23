#!/usr/bin/python3
import threading
import traceback

import abstract
import pygame

import thumbnail_view

# activity_manager.py - Presentation manager; controls activity switching and drawing.
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


class ActivityManager:
    def __init__(self):
        """Manager of activities, responsible for drawing to the screen and receiving events from the user."""
        self.current_activity: abstract.GUIActivity = None
        self.new_activity: abstract.GUIActivity = None
        self.running = True
        self.draw_fps = True
        self.switching_activity = False
        self.switching_activity_phase = 0
        self.switching_activity_final_phase = 24
        self.display: pygame.Surface = pygame.display.set_mode((800, 600))
        self.clock: pygame.time.Clock = pygame.time.Clock()

    @property
    def current_activity(self):
        return self._current_activity

    @current_activity.setter
    def current_activity(self, value):
        self._current_activity = value
        if value is not None:
            self._current_activity.activity_manager = self

    @staticmethod
    def lerp(v0: float, v1: float, t: float):
        return (1 - t) * v0 + t * v1

    def draw_loop(self):
        while self.running:
            if not self.switching_activity:
                self.switching_activity_phase = 0
                with self.current_activity.surface_lock:
                    if self.current_activity.surface:
                        self.display.blit(self.current_activity.surface, (0, 0))
                    self.clock.tick(24)
            else:
                self.switching_activity_phase += 1
                if self.switching_activity_phase > self.switching_activity_final_phase:
                    self.switching_activity = False
                    self.current_activity.stop()
                    self.current_activity = self.new_activity
                    self.new_activity = None
                else:
                    self.clock.tick(45)
                    flphase = self.switching_activity_phase / self.switching_activity_final_phase
                    x = self.lerp(self.current_activity.surface.get_width(), self.new_activity.surface.get_width(),
                                  flphase)
                    y = self.lerp(self.current_activity.surface.get_height(), self.new_activity.surface.get_height(),
                                  flphase)
                    x = int(x)
                    y = int(y)
                    # Important note:
                    # if the below lines are uncommented, the screen will fade through the contents
                    # as well as change size. This SHOULD look nicer, but, because the screen is set_mode()'d
                    # every tick, what happens is there's a lot of flashing through to black, which is a Bad Thing.

                    #                    with self.current_activity.surface_lock:
                    #                        first = self.current_activity.surface.copy()
                    #                    with self.current_activity.surface_lock:
                    #                        second = self.new_activity.surface.copy()
                    #                    first.convert_alpha()
                    #                    first.set_alpha(int(255 * (1 - flphase)))
                    #                    second.convert_alpha()
                    #                    second.set_alpha(int(255 * flphase))
                    self.display = pygame.display.set_mode((x, y))
                    #                    self.display.convert()
                    #                    self.display.blit(first, (0, 0))
                    #                    self.display.blit(second, (0, 0))
            if self.draw_fps:
                font = pygame.font.SysFont(pygame.font.get_default_font(), 40)
                fps = self.clock.get_fps()
                color = 'white'
                if fps < 30: color = 'green'
                if fps < 20: color = 'yellow'
                if fps < 10: color = 'red'
                fps = str(fps)[:5].ljust(5, '0')
                text = font.render(fps, False, pygame.Color(color))
                self.display.blit(text, (0, 0))
            pygame.display.flip()

            for event in pygame.event.get():
                if not self.switching_activity:
                    self.current_activity.respond_to_event(event)

    def start_other_activity(self, other: abstract.GUIActivity, **data):
        self.new_activity = other
        data.update({'calling_activity': self.current_activity})
        threading.Thread(target=other.start, name='ActivityManager::StartOtherActivityThread', kwargs=data,
                         daemon=True).start()
        self.switching_activity = True


class TestActivity(abstract.GUIActivity):

    @property
    def surface(self):
        return self._surface

    @property
    def surface_lock(self):
        return self._surface_lock

    @property
    def activity_manager(self):
        return self._am

    def __init__(self):
        self.surface = pygame.Surface((100, 100))
        self.surface.fill(pygame.Color('white'))
        self.surface_lock = threading.Lock()
        self.caller = None

    def start(self, color=pygame.Color('white'), **data):
        self.surface.fill(pygame.Color(color))
        self.caller = data['calling_activity']

    def stop(self):
        pass

    def respond_to_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.activity_manager.start_other_activity(self.caller)

    @surface.setter
    def surface(self, value):
        self._surface = value

    @surface_lock.setter
    def surface_lock(self, value):
        self._surface_lock = value

    @activity_manager.setter
    def activity_manager(self, value):
        self._am = value


if __name__ == '__main__':
    pygame.init()
    am = ActivityManager()
    am.current_activity = thumbnail_view.ThumbnailView()
    threading.Thread(target=am.current_activity.start).start()
    am.draw_loop()
