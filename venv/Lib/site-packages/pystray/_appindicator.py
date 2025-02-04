# coding=utf-8
# pystray
# Copyright (C) 2016-2022 Moses Palmér
# Copyright (C) 2022 Stephan Helma
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as AppIndicator
except ValueError:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator

from ._util.gtk import GtkIcon, mainloop
from . import _base


class Icon(GtkIcon):
    # We expand the menu on primary button click, and we do not even support
    # empty menus
    HAS_DEFAULT_ACTION = False

    def __init__(self, *args, **kwargs):
        super(Icon, self).__init__(*args, **kwargs)

        self._appindicator = AppIndicator.Indicator.new(
            self.name,
            '',
            AppIndicator.IndicatorCategory.APPLICATION_STATUS)

        if self.icon:
            self._update_icon()

        if self.visible:
            self._show()
        else:
            self._hide()

    @mainloop
    def _show(self):
        self._appindicator.set_icon(self._icon_path)
        self._appindicator.set_menu(
            self._menu_handle or self._create_default_menu())
        self._appindicator.set_title(self.title)
        self._appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

    @mainloop
    def _hide(self):
        self._appindicator.set_status(AppIndicator.IndicatorStatus.PASSIVE)

    @mainloop
    def _update_icon(self):
        self._remove_fs_icon()
        self._update_fs_icon()
        self._appindicator.set_icon(self._icon_path)

    @mainloop
    def _update_title(self):
        self._appindicator.set_title(self.title)

    @mainloop
    def _update_menu(self):
        self._menu_handle = self._create_menu(self.menu) or \
            self._create_default_menu()

        self._appindicator.set_menu(self._menu_handle)

    def _finalize(self):
        super(Icon, self)._finalize()
        del self._appindicator

    def _create_default_menu(self):
        """Creates a :class:`Gtk.Menu` from the default menu entry.

        :return: a :class:`Gtk.Menu`
        """
        menu = Gtk.Menu.new()
        if self.menu is not None:
            menu.append(self._create_menu_item(next(
                menu_item
                for menu_item in self.menu.items
                if menu_item.default)))
        else:
            menu.append(self._create_menu_item(
                _base.MenuItem(self.name, lambda _: None)))
        menu.show_all()

        return menu
