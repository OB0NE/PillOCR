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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ._util.gtk import GtkIcon, mainloop


class Icon(GtkIcon):
    def __init__(self, *args, **kwargs):
        super(Icon, self).__init__(*args, **kwargs)

        self._status_icon = Gtk.StatusIcon.new()
        self._status_icon.connect(
            'activate', self._on_status_icon_activate)
        self._status_icon.connect(
            'popup-menu', self._on_status_icon_popup_menu)

        if self.icon:
            self._update_icon()

    @mainloop
    def _show(self):
        self._status_icon.set_visible(True)

    @mainloop
    def _hide(self):
        self._status_icon.set_visible(False)

    @mainloop
    def _update_icon(self):
        self._remove_fs_icon()
        self._update_fs_icon()
        self._status_icon.set_from_file(self._icon_path)

    @mainloop
    def _update_menu(self):
        self._menu_handle = self._create_menu(self.menu)

    @mainloop
    def _update_title(self):
        self._status_icon.set_title(self.title)

    def _on_status_icon_activate(self, status_icon):
        """The handler for *activate* for the status icon.

        This signal handler will activate the icon.
        """
        self()

    def _on_status_icon_popup_menu(self, status_icon, button, activate_time):
        """The handler for *popup-menu* for the status icon.

        This signal handler will display the menu if one is set.
        """
        if self._menu_handle:
            self._menu_handle.popup(
                None, None, Gtk.StatusIcon.position_menu,
                self._status_icon, 0, Gtk.get_current_event_time())
