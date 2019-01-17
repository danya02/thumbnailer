#!/usr/bin/python3
import pygame
from typing import Optional
from abc import ABCMeta, abstractmethod, abstractproperty


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
        However, it must implement a __repr__() method that recreates that object precisely.
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
