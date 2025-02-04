# coding=utf-8
# pystray
# Copyright (C) 2016-2022 Moses Palmér
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import contextlib
import os
import tempfile


@contextlib.contextmanager
def serialized_image(image, format, extension=None):
    """Creates an image file from a :class:`PIL.Image.Image`.

    This function is a context manager that yields a temporary file name. The
    file is removed when the block is exited.

    :param PIL.Image.Image image: The in-memory image.

    :param str format: The format of the image. This format must be handled by
        *Pillow*.

    :param extension: The file extension. This defaults to ``format``
        lowercased.
    :type extensions: str or None
    """
    fd, path = tempfile.mkstemp('.%s' % (extension or format.lower()))
    try:
        with os.fdopen(fd, 'wb') as f:
            image.save(f, format=format)
        yield path

    finally:
        try:
            os.unlink(path)
        except:
            raise
