#!/usr/bin/python3
import peewee

# tags.py - Store tags in a database.
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

db = peewee.SqliteDatabase('./tags.sqlite')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Picture(BaseModel):
    name = peewee.CharField(unique=True)


class Tag(BaseModel):
    name = peewee.CharField(unique=True)


class Mapping(BaseModel):
    picture = peewee.ForeignKeyField(Picture, backref='mappings')
    tag = peewee.ForeignKeyField(Tag, backref='mappings')


db.create_tables([Picture, Tag, Mapping])


def get_all_tags():
    return [i.name for i in Tag.select()]


def new_picture(name):
    with db.atomic():
        pic = Picture.create(name=name)
        null_tag, _ = Tag.get_or_create(name='null tag')
        Mapping.create(picture=pic, tag=null_tag)


def assign_tag(pic_name, tag_name):
    with db.atomic():
        pic, _ = Picture.get_or_create(name=pic_name)
        tag, _ = Tag.get_or_create(name=tag_name)
        null_tag, _ = Tag.get_or_create(name='null tag')
        null_map = Mapping.get_or_none(tag=null_tag, picture=pic)
        if null_tag is not None:
            null_map.delete().execute()
        Mapping.create(picture=pic, tag=tag)


def remove_tag(pic_name, tag_name):
    with db.atomic():
        pic, _ = Picture.get_or_create(name=pic_name)
        tag, _ = Tag.get_or_create(name=tag_name)
        mapping = Mapping.get_or_none(tag=tag, picture=pic)
        if mapping is not None:
            mapping.delete().execute()
        if Mapping.select().where(Mapping.picture==pic).count() == 0:
            null_tag, _ = Tag.get_or_create(name='null tag')
            Mapping.create(tag=null_tag, picture=pic)


def create_tag(tag):
    Tag.create(name=tag)


def destroy_tag(tag):
    tag = Tag.get_or_none(name=tag)
    null_tag, _ = Tag.get_or_create(name='null tag')
    if tag is not None:
        with db.atomic():
            for i in tag.mappings:
                if i.picture.mappings==1:
                    Mapping.create(picture=i.picture, tag=null_tag)
                i.delete().execute()
            tag.delete().execute()

def get_pictures_by_tags(tags):
    tag_objs = [Tag.get(Tag.name == i) for i in tags]
    mappings = list(Mapping.select(Mapping.picture).where(Mapping.tag << tag_objs))
    pictures = [i.picture.name for i in mappings]
    return pictures
