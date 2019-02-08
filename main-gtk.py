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
import tags

import logging

l = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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

        self.image_view = self.builder.get_object('BigImageView')

        self.tag_popover = self.builder.get_object('TagMenuPopover')
        self.tag_box = self.builder.get_object('TagMenuBox')
        self.builder.get_object('TagMenuButton').connect('clicked', self.open_tag_popover)

        self.image_tag_popover = self.builder.get_object('ImageTagMenuPopover')
        self.image_tag_box = self.builder.get_object('ImageTagMenuBox')
        self.builder.get_object('ImageTagMenuButton').connect('clicked', self.open_assign_tag_popover)

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
        self.status_message = 'Ready.'
        self.status_spinner = False
        self.status_changed = True
        self.selected_picture = ''
        gobject.timeout_add(100, self.update_status_loop)

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
        self.selected_picture = value
        self.image_view.set_from_pixbuf(self.surface_to_pixbuf(self.filesystem.get_image(eval(value))))

    def add_iconview_item(self, name, liststore):
        max_rect = (100, 100)
        img = self.spritesheet_manager.get_thumbnail(name, max_rect)
        liststore.append([self.surface_to_pixbuf(img), repr(name)])

    def update_status_loop(self):
        if self.status_changed:
            self.status_changed = False
            self.builder.get_object('BottomBarSpinner').props.active = self.status_spinner
            self.builder.get_object('BottomBarStatusLabel').set_text(self.status_message)
        gobject.timeout_add(100, self.update_status_loop)

    def update_status(self, message, spinner_active):
        self.status_message = message
        self.status_spinner = spinner_active
        self.status_changed = True

    def load_thumbnails(self):
        page = 0
        n = 0
        gn = 0
        #        iconview = self.builder.get_object('PictureIconView')
        #        iconview.set_model(liststore)
        #        iconview.show_all()
        for i in self.file_list:
            tags.new_picture(i)
            n += 1
            gn += 1
            self.update_status(f'Loading preview {gn}/{len(self.file_list)}', True)
            if n > self.items_on_page:
                n = 0
                self.len_models += 1
                page += 1
                print('new page', page)
            self.add_iconview_item(i, self.models[page])
            # time.sleep(0.01)
        self.update_status('Ready.', False)

    def surface_to_pixbuf(self, surface):
        filename = f'/tmp/thumbnailer_pixbuf_convert/{str(uuid.uuid4())}.png'
        try:
            os.makedirs('/tmp/thumbnailer_pixbuf_convert/')
        except FileExistsError:
            pass
        pygame.image.save(surface, filename)
        #        data = pygame.image.tostring(img, 'RGB')
        #        pixbuf = GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB, False, 8, img.get_width(), img.get_height(), img.get_width()*3)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        return pixbuf

    def tag_checkbox_switched(self, widget, tag):
        print(tag)

    def tag_remove_click(self, widget, tag):
        l.info('Destroying tag '+tag)
        tags.destroy_tag(tag)
        self.build_tag_menu()
        self.build_assign_tag_menu()

    def add_new_tag(self, widget):
        new_tag = widget.get_text()
        l.info('Adding new tag '+new_tag)
        tags.create_tag(new_tag)
        self.build_tag_menu()
        self.build_assign_tag_menu()

    def build_tag_menu(self):
        taglist = tags.get_all_tags()
        self.tag_box.foreach(lambda x: x.destroy())
        try:
            taglist.remove(tags.NULL)
        except ValueError:
            pass
        textbox = gtk.Entry()
        textbox.connect('activate', self.add_new_tag)
        self.tag_box.add(textbox)
        null_checkbox = gtk.CheckButton.new_with_label(tags.NULL)
        null_checkbox.connect('toggled', self.tag_checkbox_switched, tags.NULL)
        self.tag_box.add(null_checkbox)
        for tag in sorted(taglist):
            checkbox = gtk.CheckButton.new_with_label(tag)
            del_button = gtk.Button.new_from_icon_name('gtk-remove', gtk.IconSize.BUTTON)
            checkbox.connect('toggled', self.tag_checkbox_switched, tag)
            del_button.connect('clicked', self.tag_remove_click, tag)
            box = gtk.Box(gtk.Orientation.HORIZONTAL, 0)
            box.add(checkbox)
            box.add(del_button)
            self.tag_box.add(box)
        self.tag_box.show_all()

    def image_tag_checkbox_switched(self, widget, tag):
        if widget.get_active():
            tags.assign_tag(self.selected_picture, tag)
        else:
            tags.remove_tag(self.selected_picture, tag)

    def build_assign_tag_menu(self):
        taglist = tags.get_all_tags()
        self.image_tag_box.foreach(lambda x: x.destroy())
        try:
            taglist.remove(tags.NULL)
        except ValueError:
            pass
        textbox = gtk.Entry()
        textbox.connect('activate', self.add_new_tag)
        self.image_tag_box.add(textbox)
        null_checkbox = gtk.CheckButton.new_with_label(tags.NULL)
        null_checkbox.connect('toggled', self.image_tag_checkbox_switched, tags.NULL)
        self.image_tag_box.add(null_checkbox)
        taglist_activate = tags.get_tags_of_picture(self.selected_picture)
        if tags.NULL in taglist_activate:
            null_checkbox.set_active(True)
        for tag in sorted(taglist):
            checkbox = gtk.CheckButton.new_with_label(tag)
            checkbox.connect('toggled', self.image_tag_checkbox_switched, tag)
            checkbox.set_active(tag in taglist_activate)
            box = gtk.Box(gtk.Orientation.HORIZONTAL, 0)
            box.add(checkbox)
            del_button = gtk.Button.new_from_icon_name('gtk-remove', gtk.IconSize.BUTTON)
            del_button.connect('clicked', self.tag_remove_click, tag)
            box.add(del_button)
            self.image_tag_box.add(box)
        self.image_tag_box.show_all()

    def open_tag_popover(self, widget):
        self.build_tag_menu()
        self.tag_popover.popup()

    def open_assign_tag_popover(self, widget):
        self.build_assign_tag_menu()
        self.image_tag_popover.popup()


if __name__ == "__main__":
    try:
        a = MainAppGTK()
        gtk.main()
    except KeyboardInterrupt:
        exit()
