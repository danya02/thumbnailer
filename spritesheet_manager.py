#!/usr/bin/python3
import uuid

import pygame
import json

import abstract


class LazySpritesheetLoader:
    def __init__(self):
        self.cache = dict()

    def __getitem__(self, item) -> pygame.Surface:
        if str(item) in self.cache:
            return self.cache[str(item)]
        else:
            self.cache.update({str(item): pygame.image.load(f'spritesheets/{item}.png')})
            return self.cache[str(item)]

    def __setitem__(self, key, value: pygame.Surface):
        pygame.image.save(value, f'spritesheets/{key}.png')
        self.cache[key] = value

    @staticmethod
    def cut_out(sheet: pygame.Surface, area: pygame.Rect) -> pygame.Surface:
        output = pygame.Surface(area.size)
        negate = lambda x: tuple((-i for i in x))
        output.blit(sheet, negate(area.topleft))
        return output


class SpritesheetManager(metaclass=abstract.Singleton):
    def __init__(self, file: str, fs: abstract.FileSystemInterface):
        self.fs = fs
        self.ssl = LazySpritesheetLoader()
        self.cache = {}
        try:
            with open(file) as o:
                self.data = json.load(o)
        except FileNotFoundError:
            self.data = dict()

    def get_thumbnail(self, name, size: (int, int)) -> pygame.Surface:
        xsep = 'x'.join([str(i) for i in size])
        if repr(name) in self.cache.get(xsep, dict()):
            return self.cache[xsep][repr(name)]

        def get_new():
            image = self.fs.get_image(name)
            image = pygame.transform.scale(image, image.get_rect().fit(pygame.Rect((0, 0), size)).size)
            fname = str(uuid.uuid4())
            self.ssl[fname] = image  # TODO: add an algorithm that packs pictures into existing sheets.
            ndata = self.data.get(xsep, dict())
            ndata.update({repr(name): {'sheetname': fname, 'area': (0, 0, size[0], size[1])}})
            self.data.update({xsep: ndata})
            return image

        if xsep in self.data:
            if repr(name) in self.data[xsep]:
                item = self.data[xsep][repr(name)]
                sheet = self.ssl[item['sheetname']]
                area = pygame.Rect(item['area'])
                thumb = self.ssl.cut_out(sheet, area)
                new = self.cache.get(xsep, dict())
                new.update({repr(name): thumb})
                self.cache[xsep] = new
                return thumb
            else:
                return get_new()
        else:
            return get_new()
