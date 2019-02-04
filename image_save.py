#!/usr/bin/python3
import threading

import pygame

import abstract
import spinner
import os


class ImageSaver(abstract.GUIActivity):

    @property
    def surface(self):
        return self._surface

    @property
    def surface_lock(self):
        return self._surface_lock

    @property
    def running(self):
        return self._running

    @property
    def activity_manager(self):
        return self._activity_manager

    def __init__(self, size):
        super().__init__()
        self.surface = pygame.Surface(size)
        self.surface_lock = threading.RLock()
        self.text = 'You shouldn\'t be reading this.'
        self.image_source = self.surface
        self.spinner = None
        self.return_to = None
        self.screen_rect = None
        self.font = None
        self.running = True
        self.draw_thread = None
        self.size_select_thread = None
        self.max_dimension = 512
        self.max_size = 512 * 1024
        self.extension = '.jpg'
        self.clock = pygame.time.Clock()
        self.timeout = -1

    def start(self, **data: dict):
        if 'return_to' in data:
            self.return_to = data['return_to']
        else:
            self.return_to = data['calling_activity']
        self.image_source = data['image']
        self.surface = pygame.Surface(data['calling_activity'].surface.get_size())
        self.spinner = spinner.EmptySquareSpinner.create_randomised(self.surface.get_size())
        self.spinner.do_color_shift = True
        self.spinner.start()
        self.screen_rect = self.surface.get_rect()
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 48)
        self.running = True
        self.timeout = -1
        self.draw_thread = threading.Thread(target=self.draw_loop, daemon=True, name='ImageSaver::DrawLoop')
        self.draw_thread.start()
        self.size_select_thread = threading.Thread(target=self.select_size, daemon=True, name='ImageSaver::SizeSelect')
        self.size_select_thread.start()

    def stop(self):
        self.spinner.stop()

    def respond_to_event(self, event: pygame.event.Event):
        pass

    def draw_loop(self):
        while self.running:
            with self.surface_lock:
                self.draw()
            self.clock.tick(10)

    def draw(self):
        self.timeout -= 1
        if self.timeout == 0:
            self.activity_manager.start_other_activity(self.return_to)
        self.surface.blit(self.spinner.surface, (0, 0))
        tcenter = self.screen_rect.center
        tcenter = (tcenter[0], tcenter[1] * 1.5)
        text = self.font.render(self.text, True, self.spinner.fgcolor)
        trect = text.get_rect()
        trect.center = tcenter
        self.surface.blit(text, trect)

    def select_size(self):
        # select path
        existing = os.listdir('./output/')
        file = './output/' + str(len(existing) + 1) + self.extension

        def scale(img: pygame.Surface, max_dimension):
            fraction = (max(img.get_width(), img.get_height())) / max_dimension
            return pygame.transform.scale(img, (int(img.get_width() * fraction), int(img.get_height() * fraction)))

        # rescale under maximum dimension
        if max(*self.image_source.get_size()) > self.max_dimension:
            self.image_source = scale(self.image_source, self.max_dimension)
        max_dimension = max(*self.image_source.get_size()) + 1

        def is_file_ok():
            try:
                return os.path.getsize(file) < self.max_size
            except FileNotFoundError:
                return False

        # rescale under max file size
        while not is_file_ok():
            max_dimension -= 1
            self.text = 'Trying scale down to ' + str(max_dimension) + 'px...'
            image = scale(self.image_source, max_dimension)
            pygame.image.save(image, file)
        self.text = 'Saved to ' + file
        self.timeout = 50

    @activity_manager.setter
    def activity_manager(self, value):
        self._activity_manager = value

    @running.setter
    def running(self, value):
        self._running = value

    @surface.setter
    def surface(self, value):
        self._surface = value

    @surface_lock.setter
    def surface_lock(self, value):
        self._surface_lock = value
