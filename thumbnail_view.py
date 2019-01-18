#!/usr/bin/python3
from typing import List
import threading
import pygame
import filesystem


class ThumbnailView:
    def __init__(self):
        self.display: pygame.Surface = pygame.display.set_mode((800, 600))
        self.max_size = pygame.Rect(0, 0, 100, 100)
        self.filesystem = filesystem.LocalFilesystem('/home/danya/Pictures')
        self.thumbnails = {}
        self.grid: List[List[pygame.Rect]] = []
        self.thumbs: List[List[pygame.Surface]] = []
        self.generate_grid()
        self.clock = pygame.time.Clock()
        self.draw_thread = threading.Thread(target=self.draw_loop, daemon=True)
        self.draw_thread.start()
        self.load_thumbs()

    def thumbify(self, image: pygame.Surface) -> pygame.Surface:
        return pygame.transform.scale(image, image.get_rect().fit(self.max_size).size)

    def generate_grid(self):
        self.grid = []
        for y in range(0, self.display.get_height(), self.max_size.height):
            newlist = []
            for x in range(0, self.display.get_width(), self.max_size.width):
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
        except StopIteration:
            pass

    def draw_loop(self):
        while True:
            self.draw()
            self.clock.tick(24)

    def draw(self):
        self.display.fill(pygame.Color('black'))
        for line, imgline in zip(self.grid, self.thumbs):
            for cell, img in zip(line, imgline):
                if img:
                    rect: pygame.Rect = img.get_rect()
                    rect.center = cell.center
                    self.display.blit(img, rect)
                    pygame.display.update(rect)


if __name__ == '__main__':
    v = ThumbnailView()
    v.draw()
    input()