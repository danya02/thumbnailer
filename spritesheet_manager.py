#!/usr/bin/python3
import logging
import traceback

import peewee
import pygame

import abstract
from legacy import global_variables

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


db = peewee.SqliteDatabase('spritesheets/data.sqlite', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 1024})


class BaseModel(peewee.Model):
    class Meta:
        database = db


class ThumbnailScale(BaseModel):
    width = peewee.IntegerField()
    height = peewee.IntegerField()


class Picture(BaseModel):
    name = peewee.CharField()
    width = peewee.IntegerField()
    height = peewee.IntegerField()


class Spritesheet(BaseModel):
    width = peewee.IntegerField()
    height = peewee.IntegerField()


class Thumbnail(BaseModel):
    picture = peewee.ForeignKeyField(Picture, backref='thumbnails')
    spritesheet = peewee.ForeignKeyField(Spritesheet, backref='thumbnails')
    scale = peewee.ForeignKeyField(ThumbnailScale, backref='thumbnails')
    x = peewee.IntegerField()
    y = peewee.IntegerField()
    width = peewee.IntegerField()
    height = peewee.IntegerField()


db.create_tables([ThumbnailScale, Picture, Spritesheet, Thumbnail])

DEFAULT_WIDTH = DEFAULT_HEIGHT = 2048

class LazySpritesheetLoader: # consider putting spritesheets into database.
    def __init__(self):
        self.cache = dict()
        self.deltas_without_save = dict()

    def __getitem__(self, item) -> pygame.Surface:
        l.debug('Loading spritesheet %s...', item)
        if str(item) in self.cache:
            l.debug('It was found in the cache.')
            return self.cache[str(item)]
        else:
            l.debug('It was not found in the spritesheet cache, loading from filesystem.')
            try:
                self.cache.update({str(item): pygame.image.load(f'spritesheets/{item}.png')})
                return self.cache[str(item)]
            except pygame.error:
                l.info('Spritesheet is broken or missing: ' + traceback.format_exc())
                return pygame.Surface((DEFAULT_WIDTH, DEFAULT_HEIGHT))

    def __setitem__(self, key, value: pygame.Surface):
        self.cache[key]=value
        with global_variables.global_quit_lock:
            pygame.image.save(value, f'spritesheets/{key}.png')

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

    def add_rect(self, new_rect: pygame.Rect):
        for sheet in Spritesheet.select():
            rects = [pygame.Rect(t.x,t.y,t.width,t.height) for t in sheet.thumbnails]
            sheet_rect = pygame.Rect(0,0,sheet.height, sheet.width)
            for rect in rects:
                crects = rects.copy()
                crects.remove(rect)
                new_rect.topleft = rect.topright
                if new_rect.collidelist(crects) == -1:
                    if sheet_rect.contains(new_rect):
                        return sheet, new_rect
                new_rect.topleft = rect.bottomright
                if new_rect.collidelist(crects) == -1:
                    if sheet_rect.contains(new_rect):
                        return sheet, new_rect
                new_rect.topright = rect.topleft
                if new_rect.collidelist(crects) == -1:
                    if sheet_rect.contains(new_rect):
                        return sheet, new_rect
                new_rect.topright = rect.bottomleft
                if new_rect.collidelist(crects) == -1:
                    if sheet_rect.contains(new_rect):
                        return sheet, new_rect
        sheet = Spritesheet.create(height=DEFAULT_HEIGHT, width=DEFAULT_WIDTH)
        new_rect.topleft = (0, 0)
        return sheet, new_rect

    def inform_new_sheet(self, sheet: str, size: (int, int)):
        self.sheet_sizes.update({sheet: size})

class SpritesheetManager(metaclass=abstract.Singleton):
    def __init__(self, file: str, fs: abstract.FileSystemInterface):
        self.fs = fs
        self.ssl = LazySpritesheetLoader()
        self.cache = {}
        self.packer = Packer()

    def clear_cache(self):
        self.cache.clear()
        self.ssl.cache.clear()
        db.drop_tables([Thumbnail, ThumbnailScale, Picture, Spritesheet])
        db.create_tables([Thumbnail, ThumbnailScale, Picture, Spritesheet])

    def get_thumbnail(self, name, size: (int, int)) -> pygame.Surface:
        xsep = 'x'.join([str(i) for i in size])
        thumbnail_scale, _ = ThumbnailScale.get_or_create(width=size[0], height=size[1])
        l.debug('Getting thumbnail of %s at %s', name, xsep)
        if repr(name) in self.cache.get(xsep, dict()):
            l.debug('This file is in immediate cache.')
            return self.cache[xsep][repr(name)]

        def get_new():
            l.debug('This image not in spritesheet cache, get from filesystem.')
            image = self.fs.get_image(name)
            picture = Picture.create(name=repr(name), width=image.get_width(), height=image.get_height())
            image = pygame.transform.scale(image, image.get_rect().fit(pygame.Rect((0, 0), size)).size)

            l.debug('Packing image into spritesheets...')
            spritesheet, rect = self.packer.add_rect(image.get_rect())
            l.debug(f'Packed image into  {spritesheet} at {rect}')

            sheet = self.ssl[spritesheet]
            if sheet is None:
                sheet = pygame.Surface((spritesheet.width, spritesheet.height))
            self.packer.inform_new_sheet(spritesheet, sheet.get_rect())

            sheet.blit(image, rect)
            self.ssl[spritesheet] = sheet

            thumbnail = Thumbnail.create(picture=picture, spritesheet=spritesheet, scale=thumbnail_scale, x=rect.left,
                                         y=rect.top, width=rect.width, height=rect.height)

            return image

        picture = Picture.get_or_none(name=repr(name))
        if picture is None:
            l.debug('This image has not been seen before.')
            return get_new()
        thumbnail = Thumbnail.get_or_none(Thumbnail.picture == picture, Thumbnail.scale == thumbnail_scale)
        if thumbnail is None:
            l.debug('No thumbnail of this image found at this size.')
            return get_new()
        spritesheet = thumbnail.spritesheet
        l.debug('This file exists in a spritesheet.')
        sheet = self.ssl[spritesheet]
        if sheet is None:
            l.error('Spritesheet error! Discarding all data from this spritesheet and trying again.')
            spritesheet.delete_instance(recursive=True)
            return self.get_thumbnail(name, size)

        area = pygame.Rect(thumbnail.x, thumbnail.y, thumbnail.width, thumbnail.height)
        thumb = self.ssl.cut_out(sheet, area)
        return thumb
