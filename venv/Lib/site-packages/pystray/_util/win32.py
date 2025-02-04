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

import ctypes

from ctypes import wintypes

windll = ctypes.LibraryLoader(ctypes.WinDLL)


WM_CREATE = 0x0001
WM_DISPLAYCHANGE = 0x007E
WM_NCCREATE = 0x0081
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_USER = 0x400

WM_STOP = WM_USER + 10
WM_NOTIFY = WM_USER + 11

LR_DEFAULTSIZE = 0x00000040
LR_LOADFROMFILE = 0x00000010

MFS_CHECKED = 0x00000008
MFS_DEFAULT = 0x00001000
MFS_DISABLED = 0x00000003
MFS_ENABLED = 0x00000000
MFS_GRAYED = 0x00000003
MFS_HILITE = 0x00000080
MFS_UNCHECKED = 0x00000000
MFS_UNHILITE = 0x00000000

MFT_BITMAP = 0x00000004
MFT_MENUBARBREAK = 0x00000020
MFT_MENUBREAK = 0x00000040
MFT_OWNERDRAW = 0x00000100
MFT_RADIOCHECK = 0x00000200
MFT_RIGHTJUSTIFY = 0x00004000
MFT_RIGHTORDER = 0x00002000
MFT_SEPARATOR = 0x00000800
MFT_STRING = 0x00000000

MIIM_BITMAP = 0x00000080
MIIM_CHECKMARKS = 0x00000008
MIIM_DATA = 0x00000020
MIIM_FTYPE = 0x00000100
MIIM_ID = 0x00000002
MIIM_STATE = 0x00000001
MIIM_STRING = 0x00000040
MIIM_SUBMENU = 0x00000004
MIIM_TYPE = 0x00000010

MSGFLT_ALLOW = 1
MSGFLT_DISALLOW = 2
MSGFLT_RESET = 0

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_STATE = 0x00000008
NIF_INFO = 0x00000010
NIF_GUID = 0x00000020
NIF_REALTIME = 0x00000040
NIF_SHOWTIP = 0x00000080

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIM_SETFOCUS = 0x00000003
NIM_SETVERSION = 0x00000004

TPM_CENTERALIGN = 0x0004
TPM_LEFTALIGN = 0x0000
TPM_RIGHTALIGN = 0x0008
TPM_BOTTOMALIGN = 0x0020
TPM_TOPALIGN = 0x0000
TPM_VCENTERALIGN = 0x0010
TPM_NONOTIFY = 0x0080
TPM_RETURNCMD = 0x0100
TPM_LEFTBUTTON = 0x0000
TPM_RIGHTBUTTON = 0x0002
TPM_HORNEGANIMATION = 0x0800
TPM_HORPOSANIMATION = 0x0400
TPM_NOANIMATION = 0x4000
TPM_VERNEGANIMATION = 0x2000
TPM_VERPOSANIMATION = 0x1000
TPM_HORIZONTAL = 0x0000
TPM_VERTICAL = 0x0040

WS_POPUP = 0x80000000


PM_NOREMOVE = 0
COLOR_WINDOW = 5
HWND_MESSAGE = -3
IMAGE_ICON = 1


LPMSG = ctypes.POINTER(wintypes.MSG)

LPPOINT = ctypes.POINTER(wintypes.POINT)

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.HRESULT,
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class MENUITEMINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.UINT),
        ('fMask', wintypes.UINT),
        ('fType', wintypes.UINT),
        ('fState', wintypes.UINT),
        ('wID', wintypes.UINT),
        ('hSubMenu', wintypes.HMENU),
        ('hbmpChecked', wintypes.HBITMAP),
        ('hbmpUnchecked', wintypes.HBITMAP),
        ('dwItemData', wintypes.LPVOID),
        ('dwTypeData', wintypes.LPCWSTR),
        ('cch', wintypes.UINT),
        ('hbmpItem', wintypes.HBITMAP)]

LPMENUITEMINFO = ctypes.POINTER(MENUITEMINFO)


class NOTIFYICONDATAW(ctypes.Structure):
    class VERSION_OR_TIMEOUT(ctypes.Union):
        _fields_ = [
            ('uTimeout', wintypes.UINT),
            ('uVersion', wintypes.UINT)]

    class GUID(ctypes.Structure):
        _fields_ = [
            ('Data1', wintypes.ULONG),
            ('Data2', wintypes.WORD),
            ('Data3', wintypes.WORD),
            ('Data4', wintypes.BYTE * 8)]

    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('hWnd', wintypes.HWND),
        ('uID', wintypes.UINT),
        ('uFlags', wintypes.UINT),
        ('uCallbackMessage', wintypes.UINT),
        ('hIcon', wintypes.HICON),
        ('szTip', wintypes.WCHAR * 128),
        ('dwState', wintypes.DWORD),
        ('dwStateMask', wintypes.DWORD),
        ('szInfo', wintypes.WCHAR * 256),
        ('version_or_timeout', VERSION_OR_TIMEOUT),
        ('szInfoTitle', wintypes.WCHAR * 64),
        ('dwInfoFlags', wintypes.DWORD),
        ('guidItem', GUID),
        ('hBalloonIcon', wintypes.HICON)]

    _anonymous_ = [
        'version_or_timeout']

LPNOTIFYICONDATAW = ctypes.POINTER(NOTIFYICONDATAW)


class TPMPARAMS(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.UINT),
        ('rcExclude', wintypes.RECT)]

LPTPMPARAMS = ctypes.POINTER(TPMPARAMS)


class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.UINT),
        ('style', wintypes.UINT),
        ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', wintypes.INT),
        ('cbWndExtra', wintypes.INT),
        ('hInstance', wintypes.HANDLE),
        ('hIcon', wintypes.HICON),
        ('hCursor', wintypes.HANDLE),
        ('hbrBackground', wintypes.HBRUSH),
        ('lpszMenuName', wintypes.LPCWSTR),
        ('lpszClassName', wintypes.LPCWSTR),
        ('hIconSm', wintypes.HICON)]


def _err(result, func, arguments):
    """A *ctypes* ``errchecker`` that ensures truthy values.
    """
    if not result:
        raise ctypes.WinError()
    else:
        return result


LPWNDCLASSEX = ctypes.POINTER(WNDCLASSEX)


CreatePopupMenu = windll.user32.CreatePopupMenu
CreatePopupMenu.argtypes = ()
CreatePopupMenu.restype = wintypes.HMENU
CreatePopupMenu.errcheck = _err


CreateWindowEx = windll.user32.CreateWindowExW
CreateWindowEx.argtypes = (
    wintypes.DWORD, wintypes.ATOM, wintypes.LPCWSTR, wintypes.DWORD,
    wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.HWND,
    wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID)
CreateWindowEx.restype = wintypes.HWND
CreateWindowEx.errcheck = _err

DefWindowProc = windll.user32.DefWindowProcW
DefWindowProc.argtypes = (
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
DefWindowProc.restype = wintypes.DWORD

DestroyIcon = windll.user32.DestroyIcon
DestroyIcon.argtypes = (
    wintypes.HICON,)
DestroyIcon.restype = wintypes.BOOL
DestroyIcon.errcheck = _err

DestroyMenu = windll.user32.DestroyMenu
DestroyMenu.argtypes = (
    wintypes.HMENU,)
DestroyMenu.restype = wintypes.BOOL
DestroyMenu.errcheck = _err

DestroyWindow = windll.user32.DestroyWindow
DestroyWindow.argtypes = (
    wintypes.HWND,)
DestroyWindow.restype = wintypes.BOOL
DestroyWindow.errcheck = _err

DispatchMessage = windll.user32.DispatchMessageW
DispatchMessage.argtypes = (
    LPMSG,)
DispatchMessage.restype = wintypes.DWORD

GetCursorPos = windll.user32.GetCursorPos
GetCursorPos.argtypes = (
    LPPOINT,)
GetCursorPos.restype = wintypes.BOOL
GetCursorPos.errcheck = _err

GetMessage = windll.user32.GetMessageW
GetMessage.argtypes = (
    LPMSG, wintypes.HWND, wintypes.UINT, wintypes.UINT)
GetMessage.restype = wintypes.BOOL

GetModuleHandle = windll.kernel32.GetModuleHandleW
GetModuleHandle.argtypes = (
    wintypes.LPCWSTR,)
GetModuleHandle.restype = wintypes.HMODULE
GetModuleHandle.errcheck = _err

InsertMenuItem = windll.user32.InsertMenuItemW
InsertMenuItem.argtypes = (
    wintypes.HMENU, wintypes.UINT, wintypes.BOOL, LPMENUITEMINFO)
InsertMenuItem.restype = wintypes.BOOL
InsertMenuItem.errcheck = _err

LoadImage = windll.user32.LoadImageW
LoadImage.argtypes = (
    wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, wintypes.INT,
    wintypes.INT, wintypes.UINT)
LoadImage.restype = wintypes.HANDLE
LoadImage.errcheck = _err

PeekMessage = windll.user32.PeekMessageW
PeekMessage.argtypes = (
    LPMSG, wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT)
PeekMessage.restype = wintypes.BOOL

PostMessage = windll.user32.PostMessageW
PostMessage.argtypes = (
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
PostMessage.restype = wintypes.BOOL
PostMessage.restype = wintypes.BOOL

PostQuitMessage = windll.user32.PostQuitMessage
PostQuitMessage.argtypes = (
    wintypes.INT,)

RegisterClassEx = windll.user32.RegisterClassExW
RegisterClassEx.argtypes = (
    LPWNDCLASSEX,)
RegisterClassEx.restype = wintypes.ATOM
RegisterClassEx.errcheck = _err

SetForegroundWindow = windll.user32.SetForegroundWindow
SetForegroundWindow.argtypes = (
    wintypes.HWND,)
SetForegroundWindow.restype = wintypes.BOOL

Shell_NotifyIcon = windll.shell32.Shell_NotifyIconW
Shell_NotifyIcon.argtypes = (
    wintypes.DWORD, LPNOTIFYICONDATAW)
Shell_NotifyIcon.restype = wintypes.BOOL

TranslateMessage = windll.user32.TranslateMessage
TranslateMessage.argtypes = (
    LPMSG,)
TranslateMessage.restype = wintypes.BOOL

TrackPopupMenuEx = windll.user32.TrackPopupMenuEx
TrackPopupMenuEx.argtypes = (
    wintypes.HMENU, wintypes.UINT, wintypes.INT, wintypes.INT, wintypes.HWND,
    LPTPMPARAMS)

UnregisterClass = windll.user32.UnregisterClassW
UnregisterClass.argtypes = (
    wintypes.ATOM, wintypes.HINSTANCE)
UnregisterClass.restype = wintypes.BOOL
UnregisterClass.errcheck = _err

RegisterWindowMessage = windll.user32.RegisterWindowMessageW
RegisterWindowMessage.argtypes = (
    wintypes.LPCWSTR,)
RegisterWindowMessage.restype = wintypes.UINT
RegisterWindowMessage.errcheck = _err

#: The message broadcast to top-level windows on Explorer restart
WM_TASKBARCREATED = RegisterWindowMessage('TaskbarCreated')

# Ensure that we receive WM_TASKBARCREATED even when running with elevated
# privileges
try:
    ChangeWindowMessageFilterEx = windll.user32.ChangeWindowMessageFilterEx

    ChangeWindowMessageFilterEx.argtypes = (
        wintypes.HWND, wintypes.UINT, wintypes.DWORD, wintypes.LPVOID)
    ChangeWindowMessageFilterEx.restype = wintypes.BOOL
    ChangeWindowMessageFilterEx.errcheck = _err

except KeyError:
    def ChangeWindowMessageFilterEx(
            hWnd, message, action, pCHangeFilterStruct):
        """A dummy implementation of ``ChangeWindowMessageFilterEx`` always
        returning ``TRUE``.

        This is used on version of *Windows* prior to *Windows Vista*.
        """
        return True
