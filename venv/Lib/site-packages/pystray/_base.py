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

import functools
import inspect
import itertools
import logging
import threading

from six.moves import queue


class Icon(object):
    """A representation of a system tray icon.

    The icon is initially hidden. Set :attr:`visible` to ``True`` to show it.

    :param str name: The name of the icon. This is used by the system to
        identify the icon.

    :param icon: The icon to use. If this is specified, it must be a
        :class:`PIL.Image.Image` instance.

    :param str title: A short title for the icon.

    :param menu: A menu to use as popup menu. This can be either an instance of
        :class:`Menu` or an iterable, which will be interpreted as arguments to
        the :class:`Menu` constructor, or ``None``, which disables the menu.

        The behaviour of the menu depends on the platform. Only one action is
        guaranteed to be invokable: the first menu item whose
        :attr:`~pystray.MenuItem.default` attribute is set.

        Some platforms allow both menu interaction and a special way of
        activating the default action, some platform allow only either an
        invisible menu with a default entry as special action or a full menu
        with no special way to activate the default item, and some platforms do
        not support a menu at all.

    :param kwargs: Any non-standard platform dependent options. These should be
        prefixed with the platform name thus: ``appindicator_``, ``darwin_``,
        ``gtk_``, ``win32_`` or ``xorg_``.

        Supported values are:

        ``darwin_nsapplication``
            An ``NSApplication`` instance used to run the event loop. If this
            is not specified, the shared application will be used.
    """
    #: Whether this particular implementation has a default action that can be
    #: invoked in a special way, such as clicking on the icon.
    HAS_DEFAULT_ACTION = True

    #: Whether this particular implementation supports menus.
    HAS_MENU = True

    #: Whether this particular implementation supports displaying mutually
    #: exclusive menu items using the :attr:`MenuItem.radio` attribute.
    HAS_MENU_RADIO = True

    #: Whether this particular implementation supports displaying a
    #: notification.
    HAS_NOTIFICATION = True

    #: The timeout, in secods, before giving up on waiting for the setup thread
    #: when stopping the icon.
    SETUP_THREAD_TIMEOUT = 5.0

    def __init__(
            self, name, icon=None, title=None, menu=None, **kwargs):
        self._name = name
        self._icon = icon or None
        self._title = title or ''
        self._menu = menu if isinstance(menu, Menu) \
            else Menu(*menu) if menu is not None \
            else None
        self._visible = False
        self._icon_valid = False
        self._log = logging.getLogger(__name__)

        self._running = False
        self.__queue = queue.Queue()

        prefix = self.__class__.__module__.rsplit('.', 1)[-1][1:] + '_'
        self._options = {
            key[len(prefix):]: value
            for key, value in kwargs.items()
            if key.startswith(prefix)}

    def __del__(self):
        if self.visible:
            self._hide()

    def __call__(self):
        if self._menu is not None:
            self._menu(self)
            self.update_menu()

    @property
    def name(self):
        """The name passed to the constructor.
        """
        return self._name

    @property
    def icon(self):
        """The current icon.

        Setting this to a falsy value will hide the icon. Setting this to an
        image while the icon is hidden has no effect until the icon is shown.
        """
        return self._icon

    @icon.setter
    def icon(self, value):
        self._icon = value
        self._icon_valid = False
        if value:
            if self.visible:
                self._update_icon()
        else:
            if self.visible:
                self.visible = False

    @property
    def title(self):
        """The current icon title.
        """
        return self._title

    @title.setter
    def title(self, value):
        if value != self._title:
            self._title = value
            if self.visible:
                self._update_title()

    @property
    def menu(self):
        """The menu.

        Setting this to a falsy value will disable the menu.
        """
        return self._menu

    @menu.setter
    def menu(self, value):
        self._menu = value
        self.update_menu()

    @property
    def visible(self):
        """Whether the icon is currently visible.

        :raises ValueError: if set to ``True`` and no icon image has been set
        """
        return self._visible

    @visible.setter
    def visible(self, value):
        if self._visible == value:
            return

        if value:
            if not self._icon:
                raise ValueError('cannot show icon without icon data')

            if not self._icon_valid:
                self._update_icon()
            self._show()
            self._visible = True

        else:
            self._hide()
            self._visible = False

    def run(self, setup=None):
        """Enters the loop handling events for the icon.

        This method is blocking until :meth:`stop` is called. It *must* be
        called from the main thread.

        :param callable setup: An optional callback to execute in a separate
            thread once the loop has started. It is passed the icon as its sole
            argument.

            Please note that this function is started in a thread, and when the
            icon is stopped, an attempt to join this thread is made, so
            stopping the icon may be blocking for up to
            ``SETUP_THREAD_TIMEOUT`` seconds if the function is not
            well-behaved.

            If not specified, a simple setup function setting :attr:`visible`
            to ``True`` is used. If you specify a custom setup function, you
            must explicitly set this attribute.
        """
        self._start_setup(setup)
        self._run()

    def run_detached(self, setup=None):
        """Prepares for running the loop handling events detached.

        This allows integrating *pystray* with other libraries requiring a
        mainloop. Call this method before entering the mainloop of the other
        library.

        Depending on the backend used, calling this method may require special
        preparations:

        macOS
            Pass an instance of ``NSApplication`` retrieved from the library
            with which you are integrating as the argument
            ``darwin_nsapplication``. This will allow this library to integrate
            with the main loop.

        :param callable setup: An optional callback to execute in a separate
            thread once the loop has started. It is passed the icon as its sole
            argument.

            If not specified, a simple setup function setting :attr:`visible`
            to ``True`` is used. If you specify a custom setup function, you
            must explicitly set this attribute.

        :raises NotImplementedError: if this is not implemented for the
            preparations taken
        """
        self._start_setup(setup)
        self._run_detached()

    def stop(self):
        """Stops the loop handling events for the icon.

        If the icon is not running, calling this method has no effect.
        """
        if self._running:
            self._stop()
            if self._setup_thread.ident != threading.current_thread().ident:
                self._setup_thread.join(timeout=self.SETUP_THREAD_TIMEOUT)
                if self._setup_thread.is_alive():
                    self._log.warning(
                        'The function passed as setup to the icon did not '
                        'finish within {} seconds after icon was '
                        'stopped'.format(
                            self.SETUP_THREAD_TIMEOUT))
            self._running = False

    def update_menu(self):
        """Updates the menu.

        If the properties of the menu descriptor are dynamic, that is, any are
        defined by callables and not constants, and the return values of these
        callables change by actions other than the menu item activation
        callbacks, calling this function is required to keep the menu in sync.

        This is required since not all supported platforms allow the menu to be
        generated when shown.

        For simple use cases where menu changes are triggered by interaction
        with the menu, this method is not necessary.
        """
        self._update_menu()

    def notify(self, message, title=None):
        """Displays a notification.

        The notification will generally be visible until
        :meth:`remove_notification` is called.

        The class field :attr:`HAS_NOTIFICATION` indicates whether this feature
        is supported on the current platform.

        :param str message: The message of the notification.

        :param str title: The title of the notification. This will be replaced
            with :attr:`title` if ``None``.
        """

        self._notify(message, title)

    def remove_notification(self):
        """Remove a notification.
        """
        self._remove_notification()

    def _mark_ready(self):
        """Marks the icon as ready.

        The setup callback passed to :meth:`run` will not be called until this
        method has been invoked.

        Before the setup method is scheduled to be called, :meth:`update_menu`
        is called.
        """
        self._running = True
        try:
            self.update_menu()
        finally:
            self.__queue.put(True)

    def _handler(self, callback):
        """Generates a callback handler.

        This method is used in platform implementations to create callback
        handlers. It will return a function taking any parameters, which will
        call ``callback`` with ``self`` and then call :meth:`update_menu`.

        :param callable callback: The callback to wrap.

        :return: a wrapped callback
        """
        @functools.wraps(callback)
        def inner(*args, **kwargs):
            try:
                callback(self)
            finally:
                self.update_menu()

        return inner

    def _show(self):
        """The implementation of the :meth:`show` method.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _hide(self):
        """The implementation of the :meth:`hide` method.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _update_icon(self):
        """Updates the image for an already shown icon.

        This method should self :attr:`_icon_valid` to ``True`` if the icon is
        successfully updated.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _update_title(self):
        """Updates the title for an already shown icon.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _update_menu(self):
        """Updates the native menu state to mimic :attr:`menu`.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _run(self):
        """Runs the event loop.

        This method must call :meth:`_mark_ready` once the loop is ready.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _run_detached(self):
        """Runs detached.

        This method must call :meth:`_mark_ready` once ready.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _start_setup(self, setup):
        """Starts the setup thread.

        :param callable setup: The thread handler.
        """
        def setup_handler():
            self.__queue.get()
            if setup:
                setup(self)
            else:
                self.visible = True

        self._setup_thread = threading.Thread(target=setup_handler)
        self._setup_thread.start()

    def _stop(self):
        """Stops the event loop.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _notify(self, message, title=None):
        """Show a notification.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()

    def _remove_notification(self):
        """Remove a notification.

        This is a platform dependent implementation.
        """
        raise NotImplementedError()


class MenuItem(object):
    """A single menu item.

    A menu item is immutable.

    It has a text and an action. The action is either a callable of a menu. It
    is callable; when called, the activation callback is called.

    The :attr:`visible` attribute is provided to make menu creation easier; all
    menu items with this value set to ``False`` will be discarded when a
    :class:`Menu` is constructed.
    """
    def __init__(
            self, text, action, checked=None, radio=False, default=False,
            visible=True, enabled=True):
        self.__name__ = str(text)
        self._text = self._wrap(text or '')
        self._action = self._assert_action(action)
        self._checked = self._assert_callable(checked, lambda _: None)
        self._radio = self._wrap(radio)
        self._default = self._wrap(default)
        self._visible = self._wrap(visible)
        self._enabled = self._wrap(enabled)

    def __call__(self, icon):
        if not isinstance(self._action, Menu):
            return self._action(icon, self)

    def __str__(self):
        if isinstance(self._action, Menu):
            return '%s =>\n%s' % (self.text, str(self._action))
        else:
            return self.text

    @property
    def text(self):
        """The menu item text.
        """
        return self._text(self)

    @property
    def checked(self):
        """Whether this item is checked.

        This can be either ``True``, which implies that the item is checkable
        and checked, ``False``, which implies that the item is checkable but
        not checked, and ``None`` for uncheckable items.

        Depending on platform, uncheckable items may be rendered differently
        from unchecked items.
        """
        return self._checked(self)

    @property
    def radio(self):
        """Whether this item is a radio button.

        This is only used for checkable items. It is always set to ``False``
        for uncheckable items.
        """
        if self.checked is not None:
            return self._radio(self)
        else:
            return False

    @property
    def default(self):
        """Whether this is the default menu item.
        """
        return self._default(self)

    @property
    def visible(self):
        """Whether this menu item is visible.

        If the action for this menu item is a menu, that also has to be visible
        for this property to be ``True``.
        """
        if isinstance(self._action, Menu):
            return self._visible(self) and self._action.visible
        else:
            return self._visible(self)

    @property
    def enabled(self):
        """Whether this menu item is enabled.
        """
        return self._enabled(self)

    @property
    def submenu(self):
        """The submenu used by this menu item, or ``None``.
        """
        return self._action if isinstance(self._action, Menu) else None

    def _assert_action(self, action):
        """Ensures that a callable can be called with the expected number of
        arguments.

        :param callable action: The action to modify. If this callable takes
            less than the expected number of arguments, a wrapper will be
            returned.

        :raises ValueError: if ``action`` requires more than the expected
            number of arguments

        :return: a callable
        """
        if action is None:
            return lambda *_: None

        elif not hasattr(action, '__code__'):
            return action

        else:
            argcount = action.__code__.co_argcount - (
                1 if inspect.ismethod(action) else 0)

            if argcount == 0:
                @functools.wraps(action)
                def wrapper0(*args):
                    return action()
                return wrapper0

            elif argcount == 1:
                @functools.wraps(action)
                def wrapper1(icon, *args):
                    return action(icon)
                return wrapper1

            elif argcount == 2:
                return action

            else:
                raise ValueError(action)

    def _assert_callable(self, value, default):
        """Asserts that a value is callable.

        If the value is a callable, it will be returned. If the value is
        ``None``, ``default`` will be returned, otherwise a :class:`ValueError`
        will be raised.

        :param value: The callable to check.

        :param callable default: The default value to return if ``value`` is
            ``None``

        :return: a callable
        """
        if value is None:
            return default
        elif callable(value):
            return value
        else:
            raise ValueError(value)

    def _wrap(self, value):
        """Wraps a value in a callable.

        If the value already is a callable, it is returned unmodified

        :param value: The value or callable to wrap.
        """
        return value if callable(value) else lambda _: value


class Menu(object):
    """A description of a menu.

    A menu description is immutable.

    It is created with a sequence of :class:`Menu.Item` instances, or a single
    callable which must return a generator for the menu items.

    First, non-visible menu items are removed from the list, then any instances
    of :attr:`SEPARATOR` occurring at the head or tail of the item list are
    removed, and any consecutive separators are reduced to one.
    """
    #: A representation of a simple separator
    SEPARATOR = MenuItem('- - - -', None)

    def __init__(self, *items):
        self._items = tuple(items)

    @property
    def items(self):
        """All menu items.
        """
        if (True
                and len(self._items) == 1
                and not isinstance(self._items[0], MenuItem)
                and callable(self._items[0])):
            return self._items[0]()
        else:
            return self._items

    @property
    def visible(self):
        """Whether this menu is visible.
        """
        return bool(self)

    def __call__(self, icon):
        try:
            return next(
                menuitem
                for menuitem in self.items
                if menuitem.default)(icon)
        except StopIteration:
            pass

    def __iter__(self):
        return iter(self._visible_items())

    def __bool__(self):
        return len(self._visible_items()) > 0

    __nonzero__ = __bool__

    def __str__(self):
        return '\n'.join(
            '\n'.join(
                '    %s' % l
                for l in str(i).splitlines())
            for i in self)

    def _visible_items(self):
        """Returns all visible menu items.

        This method also filters redundant separators as is described in the
        class documentation.

        :return: a tuple containing all currently visible items
        """
        def cleaned(items):
            was_separator = False
            for i in items:
                if not i.visible:
                    continue

                if i is self.SEPARATOR:
                    if was_separator:
                        continue
                    was_separator = True
                else:
                    was_separator = False
                yield i

        def strip_head(items):
            return itertools.dropwhile(lambda i: i is self.SEPARATOR, items)

        def strip_tail(items):
            return reversed(list(strip_head(reversed(list(items)))))

        return tuple(strip_tail(strip_head(cleaned(self.items))))
