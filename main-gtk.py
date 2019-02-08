#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gi

import filesystem
import spritesheet_manager

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk, Gdk as gdk, GLib, GObject as gobject, GdkPixbuf
import pygame
import uuid
import time
import os
import threading
import collections


class MainAppGTK:
    def __init__(self):
        self.layout_file = "main.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.layout_file)
        self.builder.connect_signals(self)

        self.liststore = gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.builder.get_object("MainWindow").show_all()

        self.iconview = self.builder.get_object('PictureIconView')
        self.iconview.connect('selection_changed', self.selection_changed)

        self.models = collections.defaultdict(lambda: gtk.ListStore(GdkPixbuf.Pixbuf, str))
        self.built_models = collections.defaultdict(lambda: False)
        self.len_models = 1

        self.builder.get_object('MainWindow').connect('destroy', self.shutdown)
        self.builder.get_object('ButtonPrev').connect('clicked', self.prev)
        self.builder.get_object('ButtonNext').connect('clicked', self.next)
        self.page = 0
        self.items_on_page = 100
        self.filesystem = filesystem.LocalFilesystem('/home/danya/Pictures/', 0.01)
        self.file_list = self.filesystem.get_file_list()  # TODO: do this in thread
        self.spritesheet_manager = spritesheet_manager.SpritesheetManager('spritesheets/data.json', self.filesystem)
        threading.Thread(target=self.load_thumbnails, daemon=True).start()
        self.prev(None)

    def shutdown(self, arg):
        try:
            os.unlink('/tmp/thumbnails')
        except:
            pass
        gtk.main_quit(arg)

    def prev(self, widget):
        self.page = max(0, self.page - 1)
        print('page now', self.page)
        self.iconview.set_model(self.models[self.page])
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(-1)

    def next(self, widget):
        print('page now', self.page)
        self.page = min(self.page + 1, self.len_models)
        self.iconview.set_model(self.models[self.page])
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(-1)

    def selection_changed(self, widget):
        value, path, cell = widget.get_cursor()
        tree_iter = self.models[self.page].get_iter(path)
        value = self.models[self.page].get_value(tree_iter, 1)
        print(value)

    def add_iconview_item(self, name, liststore):
        max_rect = (100, 100)
        img = self.spritesheet_manager.get_thumbnail(name, max_rect)
        filename = f'/tmp/thumbnails/{str(uuid.uuid4())}.png'
        try:
            os.makedirs('/tmp/thumbnails/')
        except FileExistsError:
            pass
        pygame.image.save(img, filename)
        #        data = pygame.image.tostring(img, 'RGB')
        #        pixbuf = GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB, False, 8, img.get_width(), img.get_height(), img.get_width()*3)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        liststore.append([pixbuf, repr(name)])

    def load_thumbnails(self):
        page = 0
        n = 0
        #        iconview = self.builder.get_object('PictureIconView')
        #        iconview.set_model(liststore)
        #        iconview.show_all()
        for i in self.filesystem.get_file_list():
            n += 1
            if n > self.items_on_page:
                n = 0
                self.len_models += 1
                page += 1
                print('new page', page)
            self.add_iconview_item(i, self.models[page])
            # time.sleep(0.01)


if __name__ == "__main__":
    try:
        a = MainAppGTK()
        gtk.main()
    except KeyboardInterrupt:
        exit()
