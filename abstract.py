#!/usr/bin/python3
from abc import ABCMeta, abstractmethod
from typing import Optional

import pygame


class FileSystemInterface:
    __metaclass__ = ABCMeta

    def __init__(self):
        """A file system abstraction."""
        pass

    @abstractmethod
    def get_file_list(self) -> [object]:
        """
        Get a list of image file addresses.

        An address is any object that uniquely identifies the image it is referencing.
        It should be treated by the calling environment as an opaque object.
        However, it must implement a __repr__() method that recreates that object.
        It must also be hashable, and the hash of an object from here must equal the hash of the repr-object.
        """

    @abstractmethod
    def get_image(self, name, for_thumbnail=False) -> Optional[pygame.Surface]:
        """
        Return a Pygame surface with the target image.
        The image is specified by the address object from get_file_list().
        If for_thumbnail, the image may have a smaller size than the actual image.

        If an error occurs, this should throw an exception only if not for_thumbnail.
        If for_thumbnail, this should return None instead.
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
        Set the window dimensions and start the draw/event loop.
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
