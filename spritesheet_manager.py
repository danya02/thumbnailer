#!/usr/bin/python3
import uuid

import pygame
import json

import abstract
import logging

l = logging.getLogger(__name__)


# spritesheet_manager.py - Manager of spritesheets to store thumbnails.
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


class LazySpritesheetLoader:
    def __init__(self):
        self.cache = dict()

    def __getitem__(self, item) -> pygame.Surface:
        l.debug('Loading spritesheet %s...', item)
        if str(item) in self.cache:
            l.debug('It was found in the cache.')
            return self.cache[str(item)]
        else:
            l.debug('It was not found in the spritesheet cache, loading from filesystem.')
            self.cache.update({str(item): pygame.image.load(f'spritesheets/{item}.png')})
            return self.cache[str(item)]

    def __setitem__(self, key, value: pygame.Surface):
        l.debug('Saving spritesheet %s', key)
        pygame.image.save(value, f'spritesheets/{key}.png')
        self.cache[key] = value

    @staticmethod
    def cut_out(sheet: pygame.Surface, area: pygame.Rect) -> pygame.Surface:
        output = pygame.Surface(area.size)
        negate = lambda x: tuple((-i for i in x))
        output.blit(sheet, negate(area.topleft))
        return output


class Packer:
    def __init__(self):
        self.sheets: {object: [pygame.Rect]} = dict()
        self.sheet_sizes: {str: pygame.Rect} = dict()

    def load_from_data(self, data):
        for res in data:
            if 'x' in res:
                for file in data[res]:
                    self.sheets.update(
                        {data[res][file]['sheetname']: list(set(
                            self.sheets.get(data[res][file]['sheetname'], []) + [tuple(data[res][file]['area'])]))})
            elif res == 'sheet_sizes':
                for sheet in data[res]:
                    self.sheet_sizes.update({sheet: pygame.Rect((0, 0), data[res][sheet])})
        for i in self.sheets:
            self.sheets.update({i: [pygame.Rect(q) for q in self.sheets[i]]})

    def add_rect(self, new_rect: pygame.Rect):
        for sheet in self.sheets:
            rects = self.sheets[sheet].copy()
            for rect in rects:
                crects = rects.copy()
                crects.remove(rect)
                new_rect.topleft = rect.topright
                if new_rect.collidelist(crects)==-1:
                    if self.sheet_sizes[sheet].contains(new_rect):
                        self.sheets[sheet].append(new_rect)
                        return sheet, new_rect
                new_rect.topleft = rect.bottomright
                if new_rect.collidelist(crects)==-1:
                    if self.sheet_sizes[sheet].contains(new_rect):
                        self.sheets[sheet].append(new_rect)
                        return sheet, new_rect
                new_rect.topright = rect.topleft
                if new_rect.collidelist(crects)==-1:
                    if self.sheet_sizes[sheet].contains(new_rect):
                        self.sheets[sheet].append(new_rect)
                        return sheet, new_rect
                new_rect.topright = rect.bottomleft
                if new_rect.collidelist(crects)==-1:
                    if self.sheet_sizes[sheet].contains(new_rect):
                        self.sheets[sheet].append(new_rect)
                        return sheet, new_rect
        sheet = str(uuid.uuid4())
        new_rect.topleft = (0, 0)
        self.sheets.update({sheet:[new_rect]})
        return sheet, new_rect

    def inform_new_sheet(self, sheet: str, size: (int, int)):
        self.sheet_sizes.update({sheet: size})


class SpritesheetManager(metaclass=abstract.Singleton):
    def __init__(self, file: str, fs: abstract.FileSystemInterface):
        self.fs = fs
        self.ssl = LazySpritesheetLoader()
        self.cache = {}
        self.datapath = file
        self.packer = Packer()
        self.epochs_without_save = 0
        try:
            with open(file) as o:
                self.data = json.load(o)
        except FileNotFoundError:
            self.data = dict()
        self.packer.load_from_data(self.data)

    def save_data(self):
        self.epochs_without_save+=1
        if self.epochs_without_save>10:
            self.epochs_without_save=0
            l.info('Saving spritesheet arrangement now!')
            with open(self.datapath, 'w') as o:
                json.dump(self.data, o)

    def get_thumbnail(self, name, size: (int, int)) -> pygame.Surface:
        xsep = 'x'.join([str(i) for i in size])
        l.debug('Getting thumbnail of %s at %s', name, xsep)
        if repr(name) in self.cache.get(xsep, dict()):
            l.debug('This file is in immediate cache.')
            return self.cache[xsep][repr(name)]

        def get_new():
            l.debug('This image not in spritesheet cache, get from filesystem.')
            image = self.fs.get_image(name)
            image = pygame.transform.scale(image, image.get_rect().fit(pygame.Rect((0, 0), size)).size)
            l.debug('Packing image into spritesheets...')
            fname, rect = self.packer.add_rect(image.get_rect())
            l.debug(f'Packed image into  {fname} at {rect}')
            try:
                sheet = self.ssl[fname]
            except pygame.error:
                sheet = pygame.Surface((2048, 2048))
            self.packer.inform_new_sheet(fname, sheet.get_rect())
            sheet_sizes = self.data.get('sheet_sizes', dict())
            if fname not in sheet_sizes:
                sheet_sizes.update({fname: sheet.get_size()})
                self.data.update({'sheet_sizes': sheet_sizes})
            sheet.blit(image, rect)
            self.ssl[fname] = sheet
            ndata = self.data.get(xsep, dict())
            ndata.update({repr(name): {'sheetname': fname, 'area': tuple(rect)}})
            self.data.update({xsep: ndata})
            self.save_data()
            return image

        if xsep in self.data:
            if repr(name) in self.data[xsep]:
                l.debug('This file exists in a spritesheet.')
                item = self.data[xsep][repr(name)]
                sheet = self.ssl[item['sheetname']]
                area = pygame.Rect(item['area'])
                thumb = self.ssl.cut_out(sheet, area)
                new = self.cache.get(xsep, dict())
                new.update({repr(name): thumb})
                self.cache[xsep] = new
                self.save_data()
                return thumb
            else:
                return get_new()
        else:
            return get_new()
