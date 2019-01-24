#!/usr/bin/python3
from abc import ABCMeta, abstractmethod
from typing import Optional, TYPE_CHECKING

import pygame
import threading

if TYPE_CHECKING:
    import activity_manager
else:
    class Null:pass
    activity_manager=Null()
    activity_manager.ActivityManager = Null()

# abstract.py - Abstract Base Classes and miscellaneous object-oriented programming items.
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

class FileSystemInterface:
    __metaclass__ = ABCMeta

    def __init__(self):
        """A file system abstraction."""
        pass

    @abstractmethod
    def get_file_list(self) -> [object]:
        """
        Get a list of image file addresses.
        This list must be consistently ordered between calls.

        An address is any object that uniquely identifies the image it is referencing.
        It should be treated by the calling environment as an opaque object.
        However, it must implement a __repr__() method that recreates that object.
        It must also be hashable, and the hash of an object from here must equal the hash of the repr-object.
        """

    @abstractmethod
    def get_image(self, name) -> Optional[pygame.Surface]:
        """
        Return a Pygame surface with the target image.
        The image is specified by the address object from get_file_list().
        """


class GUIActivity:
    __metaclass__ = ABCMeta

    def __init__(self):
        """Any user-facing window."""
        pass

    @abstractmethod
    def start(self, **data: dict):
        """
        Show the activity on the screen.

        "data" is anything the calling activity would like this activity to know.
        One field will always exist: "calling_activity", the instance of this class that launched this.

        This class must be able to be stop()'ed and start()'d multiple times.
        """

    @property
    @abstractmethod
    def running(self):
        """
        Is the event loop running?

        If False, executing start() on another activity must be safe.
        This means this object must not attempt to draw on the screen or listen for events.
        """

    @abstractmethod
    def stop(self):
        """
        Shut down all loops previously start()'ed.
        When this is done, self.running must be False.
        """

    @property
    @abstractmethod
    def surface(self) -> pygame.Surface:
        """The surface on which the interface will be drawn."""

    @abstractmethod
    def respond_to_event(self, event: pygame.event.Event):
        """
        Do internal actions to react to an event.

        This must return as fast as possible, or you risk missing too many frame updates.
        This is not run if the activity is being switched out.
        """

    @property
    @abstractmethod
    def surface_lock(self) -> threading.Lock:
        """
        A lock for the surface.
        If it is released, it is OK to show this surface to the user.
        """

    @property
    @abstractmethod
    def activity_manager(self) -> activity_manager.ActivityManager:
        """
        The activity manager this activity is linked to.
        This must be set before start() is called.
        """


# from https://stackoverflow.com/a/6798042/5936187
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
