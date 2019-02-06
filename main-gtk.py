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

import threading


class MainAppGTK:
    def __init__(self):
        self.layout_file = "main.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.layout_file)
        self.builder.connect_signals(self)

        self.picture_flow_box = self.builder.get_object('PictureFlowBox')
        self.builder.get_object("MainWindow").show_all()
        self.builder.get_object('MainWindow').connect('destroy', gtk.main_quit)
        self.flowbox_list_lock = threading.RLock()
        self.flowbox_list = []
        self.filesystem = filesystem.LocalFilesystem('/home/danya/Pictures/', 0.1)
        self.spritesheet_manager = spritesheet_manager.SpritesheetManager('spritesheets/data.json', self.filesystem)
        gobject.timeout_add(100, self.update_flowbox)
        threading.Thread(target=self.load_thumbnails).start()

    def create_flowbox_item(self, name):
        max_rect = (100, 100)
        img = self.spritesheet_manager.get_thumbnail(name, max_rect)
        filename = f'/tmp/{str(uuid.uuid4())}.png'
        pygame.image.save(img, filename)
#        data = pygame.image.tostring(img, 'RGB')
#        pixbuf = GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB, False, 8, img.get_width(), img.get_height(), img.get_width()*3)
        image_widget = gtk.Image()
#        image_widget.set_from_pixbuf(pixbuf)
        image_widget.set_from_file(filename)
        button = gtk.Button()
        button.add(image_widget)
        button.connect("clicked", lambda x: print('Click on image', name))
        image_widget.show_all()
        button.show_all()

        return button

    def update_flowbox(self):
        with self.flowbox_list_lock:
            for i in self.flowbox_list:
                self.picture_flow_box.add(i)
                self.flowbox_list.remove(i)
        gobject.timeout_add(100, self.update_flowbox)

    def load_thumbnails(self):
        for i in self.filesystem.get_file_list():
            image = self.create_flowbox_item(i)
            with self.flowbox_list_lock:
                self.flowbox_list.append(image)


if __name__ == "__main__":
    try:
        a = MainAppGTK()
        gtk.main()
    except KeyboardInterrupt:
        exit()
