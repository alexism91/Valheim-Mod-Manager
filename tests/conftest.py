"""
Stub out GTK / GLib before any vmm module is imported.
This lets unit tests run without a display server or PyGObject.
"""
import sys
import types
from unittest.mock import MagicMock


def _make_gi_stubs():
    # Top-level gi package
    gi_mod = types.ModuleType("gi")
    gi_mod.require_version = lambda *a, **kw: None

    # gi.repository with the widgets / objects we reference in logic
    repo = types.ModuleType("gi.repository")

    glib = types.ModuleType("gi.repository.GLib")
    glib.idle_add = lambda fn, *a, **kw: fn(*a, **kw)
    glib.timeout_add = MagicMock(return_value=0)
    glib.source_remove = MagicMock()

    repo.GLib = glib
    repo.Gtk = MagicMock()
    repo.Gdk = MagicMock()
    repo.Gio = MagicMock()
    repo.Adw = MagicMock()
    repo.Pango = MagicMock()

    gi_mod.repository = repo

    sys.modules.setdefault("gi", gi_mod)
    sys.modules.setdefault("gi.repository", repo)
    sys.modules.setdefault("gi.repository.GLib", glib)
    sys.modules.setdefault("gi.repository.Gtk", repo.Gtk)
    sys.modules.setdefault("gi.repository.Gdk", repo.Gdk)
    sys.modules.setdefault("gi.repository.Gio", repo.Gio)
    sys.modules.setdefault("gi.repository.Adw", repo.Adw)
    sys.modules.setdefault("gi.repository.Pango", repo.Pango)


_make_gi_stubs()
