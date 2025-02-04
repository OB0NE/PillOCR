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

import os
import sys


def backend():
    """Returns the backend module.
    """
    def dummy():
        from . import _dummy as backend; return backend
    def appindicator():
        from . import _appindicator as backend; return backend
    def darwin():
        from . import _darwin as backend; return backend
    def gtk():
        from . import _gtk as backend; return backend
    def win32():
        from . import _win32 as backend; return backend
    def xorg():
        from . import _xorg as backend; return backend
    backends = {b.__name__: b for b in (
        dummy, appindicator, darwin, gtk, win32, xorg)}

    backend_name = os.environ.get('PYSTRAY_BACKEND', None)
    if backend_name:
        try:
            candidates = [backends[backend_name]]
        except KeyError as e:
            raise ImportError('unknown backend: {}'.format(e))
    elif sys.platform == 'darwin':
        candidates = [darwin]
    elif sys.platform == 'win32':
        candidates = [win32]
    else:
        candidates = [appindicator, gtk, xorg]

    errors = []
    for candidate in candidates:
        try:
            return candidate()
        except ImportError as e:
            errors.append(e)

    raise ImportError('this platform is not supported: {}'.format(
        '; '.join(str(e) for e in errors)))


Icon = backend().Icon
del backend

from ._base import Menu, MenuItem
