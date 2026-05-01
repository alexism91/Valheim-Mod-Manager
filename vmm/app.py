import gi
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gio

try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw
    HAS_ADW = True
except Exception:
    HAS_ADW = False

from vmm.constants import APP_ID, APP_NAME
from vmm.styles import CSS
from vmm.logic import ModManager
from vmm.window import AppWindow

class ValheimModManagerApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        if HAS_ADW:
            Adw.init()

    def do_activate(self):
        manager = ModManager()
        win     = AppWindow(self, manager)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            win.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        win.present()
        win.start_load()

def main():
    import sys
    from vmm.fonts import load_bundled_fonts
    load_bundled_fonts()
    app = ValheimModManagerApp()
    sys.exit(app.run(sys.argv))
