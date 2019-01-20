#!/usr/bin/python3
from typing import List
import threading
import pygame
import filesystem
import abstract


import activity_manager


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
        self.filesystem = filesystem.LocalFilesystem('/home/danya/Pictures')
        self.thumbnails = {}
        self.grid: List[List[pygame.Rect]] = []
        self.thumbs: List[List[pygame.Surface]] = []
        self.clock = pygame.time.Clock()

    def start(self, **data):
        self.running = True
        self.surface = pygame.Surface((800,600))
        self.generate_grid()
        self.draw_thread = threading.Thread(name='ThumbnailView::DrawThread', target=self.draw_loop, daemon=True)
        self.draw_thread.start()
        self.load_thumbs()

    def respond_to_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.activity_manager.start_other_activity(activity_manager.TestActivity(), color='red')

    def stop(self):
        self.running = False

    def thumbify(self, image: pygame.Surface) -> pygame.Surface:
        return pygame.transform.scale(image, image.get_rect().fit(self.max_size).size)

    def generate_grid(self):
        self.grid = []
        for y in range(0, self.surface.get_height(), self.max_size.height):
            newlist = []
            for x in range(0, self.surface.get_width(), self.max_size.width):
                rect = self.max_size.copy()
                rect.x = x
                rect.y = y
                newlist.append(rect)
            self.grid.append(newlist)

    def load_thumbs(self):
        files = iter(self.filesystem.get_file_list())
        self.thumbs = [[None for x in y] for y in self.grid]
        try:
            for y in range(len(self.grid)):
                for x in range(len(self.grid[0])):
                    file = next(files)
                    image = self.filesystem.get_image(file, True)
                    if image:
                        image = self.thumbify(image)
                        self.thumbs[y][x] = image
                        self.draw()
        except StopIteration:
            pass

    def draw_loop(self):
        while self.running:
            self.draw()
            self.clock.tick(24)

    def draw(self):
        with self.surface_lock:
            self.surface.fill(pygame.Color('black'))
            for line, imgline in zip(self.grid, self.thumbs):
                    for cell, img in zip(line, imgline):
                        if img:
                            rect: pygame.Rect = img.get_rect()
                            rect.center = cell.center
                            self.surface.blit(img, rect)

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
            s.blit(v.surface, (0,0))
            pygame.display.flip()
        c.tick(10)
