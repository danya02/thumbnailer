#!/usr/bin/python3
from typing import Optional

import pygame
import os
import abstract

# filesystem.py - Abstraction for the local filesystem.
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
