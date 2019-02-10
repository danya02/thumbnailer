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

db = peewee.SqliteDatabase('./tags.sqlite', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 1024})

NULL='null tag'

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
        pic, created = Picture.get_or_create(name=name)
        if created:
            null_tag, _ = Tag.get_or_create(name=NULL)
            Mapping.create(picture=pic, tag=null_tag)
        return pic

def add_many_pictures(list, callback):
    list=list[:]
    c=0
    m=len(list)*2
    callback(c,m)
    if Picture.select().count==len(list):
        return
    for i in Picture.select():
        c+=1
        callback(c, m)
        if i.name in list:
            list.remove(i.name)
    c=m//2
    callback(c,m)
    null_tag, _ = Tag.get_or_create(name=NULL)
    with db.atomic():
        for i in list:
            pic=Picture.create(name=i)
            Mapping.create(picture=pic,tag=null_tag)
            callback(c,m)
            c+=1



def assign_tag(pic_name, tag_name):
    with db.atomic():
        pic, _ = Picture.get_or_create(name=pic_name)
        tag, _ = Tag.get_or_create(name=tag_name)
        null_tag, _ = Tag.get_or_create(name=NULL)
        null_map = Mapping.get_or_none(tag=null_tag, picture=pic)

        if null_map is not None:
            null_map.delete_instance()
        Mapping.get_or_create(picture=pic, tag=tag)


def remove_tag(pic_name, tag_name):
    with db.atomic():
        pic, _ = Picture.get_or_create(name=pic_name)
        tag, _ = Tag.get_or_create(name=tag_name)
        mapping = Mapping.get_or_none(tag=tag, picture=pic)
        if mapping is not None:
            mapping.delete_instance()
        if Mapping.select().where(Mapping.picture==pic).count() == 0:
            null_tag, _ = Tag.get_or_create(name=NULL)
            Mapping.create(tag=null_tag, picture=pic)


def create_tag(tag):
    Tag.create(name=tag)


def destroy_tag(tag):
    tag = Tag.get_or_none(name=tag)
    null_tag, _ = Tag.get_or_create(name=NULL)
    if tag is not None:
        with db.atomic():
            for i in tag.mappings:
                if i.picture.mappings.count()==1:
                    Mapping.create(picture=i.picture, tag=null_tag)
                i.delete_instance()
            tag.delete_instance()

def get_pictures_by_tags(tags):
    tag_objs = [Tag.get(Tag.name == i) for i in tags]
    mappings = list(Mapping.select(Mapping.picture).where(Mapping.tag << tag_objs))
    pictures = [i.picture.name for i in mappings]
    return pictures

def get_tags_of_picture(name):
    picture = new_picture(name)
    tags=[]
    for i in picture.mappings:
        tags.append(i.tag.name)
    return tags