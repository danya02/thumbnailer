#!/usr/bin/python3
from typing import Optional

import pygame
import os
import abstract


class LocalFilesystem(abstract.FileSystemInterface):
    def __init__(self, basepath):
        """An interface to the local file system."""
        super().__init__()
        self.base_path = basepath
        self.picture_endings = ['.png', '.jpg', '.jpeg']  # TODO: add more image extensions.

    def get_file_list(self) -> [str]:
        outp = []
        for i in os.walk(self.base_path):
            for j in i[2]:
                path = i[0] + os.path.sep + j
                for e in self.picture_endings:
                    if path.endswith(e):
                        outp += [path]
        return outp

    def get_image(self, name, for_thumbnail=False) -> Optional[pygame.Surface]:
        if for_thumbnail:
            try:
                return pygame.image.load(name)
            except:
                return None
        else:
            return pygame.image.load(name)
