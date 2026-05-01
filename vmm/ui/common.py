import gi
from gi.repository import Gtk, GLib

class ToastOverlay(Gtk.Overlay):
    __gtype_name__ = "ToastOverlay"

    def __init__(self, child: Gtk.Widget):
        super().__init__()
        self.set_child(child)
        self._tid = None
        self._build()

    def _build(self):
        self._revealer = Gtk.Revealer()
        self._revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self._revealer.set_transition_duration(260)
        self._revealer.set_halign(Gtk.Align.CENTER)
        self._revealer.set_valign(Gtk.Align.END)
        self._revealer.set_margin_bottom(20)
        self._revealer.set_can_target(False)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        inner.add_css_class("toast-box")
        self._icon_lbl  = Gtk.Label(); self._icon_lbl.add_css_class("toast-icon")
        self._msg_lbl   = Gtk.Label(); self._msg_lbl.set_wrap(True)
        inner.append(self._icon_lbl)
        inner.append(self._msg_lbl)
        self._toast_box = inner
        self._revealer.set_child(inner)
        self.add_overlay(self._revealer)

    def show(self, message: str, kind: str = "info", duration: int = 3200):
        icons = {"success": "\u26a1", "error": "\u26a0", "warning": "\u26a0", "info": "\u16ac"}
        for k in ("toast-success", "toast-error", "toast-warning"):
            self._toast_box.remove_css_class(k)
        if kind != "info":
            self._toast_box.add_css_class(f"toast-{kind}")
        self._icon_lbl.set_text(icons.get(kind, "\u16ac"))
        self._msg_lbl.set_text(message)
        self._revealer.set_reveal_child(True)
        if self._tid:
            GLib.source_remove(self._tid)
        self._tid = GLib.timeout_add(duration, self._hide)

    def _hide(self):
        self._revealer.set_reveal_child(False)
        self._tid = None
        return False

def make_rune_sep() -> Gtk.Box:
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    box.set_hexpand(True)
    left  = Gtk.Separator(); left.set_hexpand(True); left.set_valign(Gtk.Align.CENTER)
    rune  = Gtk.Label(label="\u16ac\u16c8\u16d2\u16ac")
    rune.add_css_class("rune-deco"); rune.set_margin_start(12); rune.set_margin_end(12)
    right = Gtk.Separator(); right.set_hexpand(True); right.set_valign(Gtk.Align.CENTER)
    box.append(left); box.append(rune); box.append(right)
    return box

def make_empty_state(icon: str, title: str, body: str = "") -> Gtk.Box:
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_halign(Gtk.Align.CENTER); box.set_valign(Gtk.Align.CENTER)
    box.set_hexpand(True); box.set_vexpand(True)
    ic = Gtk.Label(label=icon); ic.add_css_class("empty-icon")
    t  = Gtk.Label(label=title); t.add_css_class("empty-title")
    box.append(ic); box.append(t)
    if body:
        b = Gtk.Label(label=body); b.add_css_class("empty-body")
        b.set_wrap(True); b.set_halign(Gtk.Align.CENTER)
        box.append(b)
    return box
