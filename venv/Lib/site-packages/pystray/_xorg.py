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
import functools
import six
import sys
import threading
import types

import PIL
import Xlib.display
import Xlib.threaded
import Xlib.XK

from six.moves import queue

from . import _base


# Create a display to verify that we have an X connection
display = Xlib.display.Display()
display.close()
del display


class XError(Exception):
    """An error that is thrown at the end of a code block managed by a
    :func:`display_manager` if an *X* error occurred.
    """
    pass


@contextlib.contextmanager
def display_manager(display):
    """Traps *X* errors and raises an :class:`XError` at the end if any
    error occurred.

    This handler also ensures that the :class:`Xlib.display.Display` being
    managed is sync'd.

    :param Xlib.display.Display display: The *X* display.
    """
    errors = []

    def handler(*args):
        errors.append(args)

    old_handler = display.set_error_handler(handler)
    try:
        yield
        display.sync()
    finally:
        display.set_error_handler(old_handler)
    if errors:
        raise XError(errors)


class Icon(_base.Icon):
    _XEMBED_VERSION = 0
    _XEMBED_MAPPED = 1

    _SYSTEM_TRAY_REQUEST_DOCK = 0

    # We support only the default action
    HAS_MENU = False

    # We support no menu
    HAS_MENU_RADIO = False

    # No notification (yet)!
    HAS_NOTIFICATION = False

    def __init__(self, *args, **kwargs):
        super(Icon, self).__init__(*args, **kwargs)

        #: The properly scaled version of the icon image
        self._icon_data = None

        #: The window currently embedding this icon
        self._systray_manager = None

        # This is a mapping from X event codes to handlers used by the mainloop
        self._message_handlers = {
            Xlib.X.ButtonPress: self._on_button_press,
            Xlib.X.ConfigureNotify: self._on_expose,
            Xlib.X.DestroyNotify: self._on_destroy_notify,
            Xlib.X.Expose: self._on_expose}

        self._queue = queue.Queue()

        # Connect to X
        self._display = Xlib.display.Display()

        with display_manager(self._display):
            # Create the atoms; some of these are required when creating
            # the window
            self._create_atoms()

            # Create the window and get a graphics context
            self._window = self._create_window()
            self._gc = self._window.create_gc()

            # Rewrite the platform implementation methods to ensure they
            # are executed in this thread
            self._rewrite_implementation(
                self._show,
                self._hide,
                self._update_icon,
                self._update_title,
                self._stop)

    def __del__(self):
        try:
            # Destroying the window will stop the mainloop thread
            if self._running:
                self._stop()
                if threading.current_thread().ident != self._thread.ident:
                    self._thread.join()

        finally:
            self._display.close()

    def _show(self):
        """The implementation of :meth:`_show`, executed in the mainloop
        thread.
        """
        try:
            self._assert_docked()
        except AssertionError:
            # There is no systray selection owner, so we cannot dock; ignore
            # and dock later
            self._log.error(
                'Failed to dock icon', exc_info=True)

    def _hide(self):
        """The implementation of :meth:`_hide`, executed in the mainloop
        thread.
        """
        if self._systray_manager:
            self._undock_window()

    def _update_icon(self):
        """The implementation of :meth:`_update_icon`, executed in the mainloop
        thread.
        """
        try:
            self._assert_docked()
        except AssertionError:
            # If we are not docked, we cannot update the icon
            self._log.error(
                'Failed to dock icon', exc_info=True)
            return

        # Setting _icon_data to None will force regeneration of the icon
        # from _icon
        self._icon_data = None
        self._draw()
        self._icon_valid = True

    def _update_title(self):
        """The implementation of :meth:`_update_title`, executed in the
        mainloop thread.
        """
        # The title is the window name
        self._window.set_wm_name(self.title)

    def _update_menu(self):
        # Menus are not supported on X
        pass

    def _run(self):
        self._mark_ready()

        # Run the event loop
        self._thread = threading.current_thread()
        self._mainloop()

    def _run_detached(self):
        threading.Thread(target=lambda: self.run()).start()

    def _stop(self):
        """Stops the mainloop.
        """
        self._window.destroy()
        self._display.flush()

    def _mainloop(self):
        """The body of the main loop thread.

        This method retrieves all events from *X* and makes sure to dispatch
        clicks.
        """
        try:
            for event in self._events():
                # If the systray window is destroyed, the icon has been hidden
                if (event.type == Xlib.X.DestroyNotify and
                        event.window == self._window):
                    break

                self._message_handlers.get(event.type, lambda e: None)(event)

        except:
            self._log.error(
                'An error occurred in the main loop', exc_info=True)

    def _on_button_press(self, event):
        """Handles ``Xlib.X.ButtonPress``.

        This method calls the activate callback. It will only be called for
        left button clicks.
        """
        if event.detail == 1:
            self()

    def _on_destroy_notify(self, event):
        """Handles ``Xlib.X.DestroyNotify``.

        This method clears :attr:`_systray_manager` if it is destroyed.
        """
        # Handle only the systray manager window; the destroy notification
        # for our own window is handled in the event loop
        if event.window.id != self._systray_manager.id:
            return

        # Try to locate a new systray selection owner
        self._systray_manager = None
        try:
            self._assert_docked()
        except AssertionError:
            # There is no new selection owner; we must retry later
            self._log.error(
                'Failed to dock icon', exc_info=True)

    def _on_expose(self, event):
        """Handles ``Xlib.X.ConfigureNotify`` and ``Xlib.X.Expose``.

        This method redraws the window.
        """
        # Redraw only our own window
        if event.window.id != self._window.id:
            return

        self._draw()

    def _create_atoms(self):
        """Creates the atoms used by the *XEMBED* and *systray* specifications.
        """
        self._xembed_info = self._display.intern_atom(
            '_XEMBED_INFO')
        self._net_system_tray_sx = self._display.intern_atom(
            '_NET_SYSTEM_TRAY_S%d' % (
                self._display.get_default_screen()))
        self._net_system_tray_opcode = self._display.intern_atom(
            '_NET_SYSTEM_TRAY_OPCODE')

    def _rewrite_implementation(self, *args):
        """Overwrites the platform implementation methods with ones causing the
        mainloop to execute the code instead.

        :param args: The methods to rewrite.
        """
        def dispatcher(original, atom):
            @functools.wraps(original)
            def inner(self):
                # Just invoke the method if we are currently in the correct
                # thread
                if threading.current_thread().ident == self._thread.ident:
                    original()
                else:
                    self._send_message(self._window, atom)
                    self._display.flush()

                    # Wait for the mainloop to execute the actual method, wait
                    # for completion and reraise any exceptions
                    result = self._queue.get()
                    if result is not True:
                        six.reraise(*result)

            return types.MethodType(inner, self)

        def wrapper(original):
            @functools.wraps(original)
            def inner():
                try:
                    original()
                    self._queue.put(True)
                except:
                    self._queue.put(sys.exc_info())
            return inner

        def on_client_message(event):
            handlers.get(event.client_type, lambda: None)()

        # Create the atoms and a mapping from atom to actual implementation
        atoms = [
            self._display.intern_atom(
                '_PYSTRAY_%s' % original.__name__.upper())
            for original in args]
        handlers = {
            atom: wrapper(original)
            for original, atom in zip(args, atoms)}

        # Replace the old methods
        for original, atom in zip(args, atoms):
            setattr(
                self,
                original.__name__,
                dispatcher(original, atom))

        # Make sure that we handle ClientMessage
        self._message_handlers[Xlib.X.ClientMessage] = on_client_message

    def _create_window(self):
        """Creates the system tray icon window.

        :return: a window
        """
        with display_manager(self._display):
            # Create the window
            screen = self._display.screen()
            window = screen.root.create_window(
                -1, -1, 1, 1, 0, screen.root_depth,
                event_mask=Xlib.X.ExposureMask | Xlib.X.StructureNotifyMask,
                window_class=Xlib.X.InputOutput)
            flags = (
                Xlib.Xutil.PPosition | Xlib.Xutil.PSize | Xlib.Xutil.PMinSize)
            window.set_wm_class('%sSystemTrayIcon' % self.name, self.name)
            window.set_wm_name(self.title)
            window.set_wm_normal_hints(
                flags=flags,
                min_width=24,
                min_height=24)

            # Enable XEMBED for the window
            window.change_property(self._xembed_info, self._xembed_info, 32, [
                self._XEMBED_VERSION,
                self._XEMBED_MAPPED])

            return window

    def _draw(self):
        """Paints the icon image.
        """
        try:
            dim = self._window.get_geometry()
            self._assert_icon_data(dim.width, dim.height)
            self._window.put_pil_image(self._gc, 0, 0, self._icon_data)

        except Xlib.error.BadDrawable:
            # The window has been destroyed; ignore
            pass

    def _assert_icon_data(self, width, height):
        """Asserts that the cached icon data matches the requested dimensions.

        If no cached icon data exists, or its dimensions do not match the
        requested size, the image is generated.

        :param int width: The requested width.

        :param int height: The requested height.
        """
        if self._icon_data and self._icon_data.size == (width, height):
            return

        self._icon_data = PIL.Image.new(
            'RGB',
            (width, height))
        self._icon_data.paste(self._icon.resize(
            (width, height),
            PIL.Image.LANCZOS))
        self._icon_data.tostring = self._icon_data.tobytes

    def _assert_docked(self):
        """Asserts that the icon is docked in the systray.

        :raises AssertionError: if the window is not docked
        """
        self._dock_window()
        assert self._systray_manager

    def _dock_window(self):
        """Docks the window in the systray.
        """
        # Get the selection owner
        systray_manager = self._get_systray_manager()
        if not systray_manager:
            return
        self._systray_manager = systray_manager

        # Request being docked
        self._send_message(
            self._systray_manager,
            self._net_system_tray_opcode,
            self._SYSTEM_TRAY_REQUEST_DOCK,
            self._window.id)

        # Make sure we get destroy notifications
        systray_manager.change_attributes(
            event_mask=Xlib.X.StructureNotifyMask)

        self._display.flush()

        self._systray_manager = systray_manager

    def _undock_window(self):
        """Undocks the window from the systray.
        """
        # Make sure we get do not get any notifications
        try:
            self._systray_manager.change_attributes(
                event_mask=Xlib.X.NoEventMask)
        except XError:
            # The systray manager may have been destroyed
            self._log.error(
                'Failed to stop notifications', exc_info=True)

        self._window.unmap()
        self._window.reparent(self._display.screen().root, 0, 0)
        self._systray_manager = None

        self._display.flush()

    def _get_systray_manager(self):
        """Returns the *X* window that owns the systray selection.

        :return: the window owning the selection, or ``None`` if no window owns
            it
        """
        self._display.grab_server()
        try:
            systray_manager = self._display.get_selection_owner(
                self._net_system_tray_sx)
        finally:
            self._display.ungrab_server()
        self._display.flush()

        if systray_manager != Xlib.X.NONE:
            return self._display.create_resource_object(
                'window',
                systray_manager.id)

    def _send_message(self, window, client_type, l0=0, l1=0, l2=0, l3=0):
        """Sends a generic client message message.

        This method does not trap *X* errors; that is up to the caller.

        :param int l0: Message specific data.

        :param int l1: Message specific data.

        :param int l2: Message specific data.

        :param int l3: Message specific data.
        """
        self._display.send_event(
            window,
            Xlib.display.event.ClientMessage(
                type=Xlib.X.ClientMessage,
                client_type=client_type,
                window=window.id,
                data=(
                    32,
                    (Xlib.X.CurrentTime, l0, l1, l2, l3))),
            event_mask=Xlib.X.NoEventMask)

    def _events(self):
        """Yields all events.
        """
        while True:
            event = self._display.next_event()
            if not event:
                break
            else:
                yield event
