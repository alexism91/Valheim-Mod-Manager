import logging
from gi.repository import Gtk, Gdk, Pango
from vmm.logic import fetch_icon_async
from vmm.utils import fmt_number

logger = logging.getLogger("ValheimModManager")

class ModCard(Gtk.Box):
    __gtype_name__ = "ModCard"

    def __init__(self, package: dict, manager, on_click, show_toast):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.pkg        = package
        self.manager    = manager
        self.on_click   = on_click
        self.show_toast = show_toast
        self.add_css_class("mod-card")
        self._build()

        gc = Gtk.GestureClick()
        gc.connect("released", lambda *_: self.on_click(self.pkg))
        self.add_controller(gc)

        self._motion = Gtk.EventControllerMotion()
        self._motion.connect("enter", self._on_enter)
        self._motion.connect("leave", self._on_leave)
        self.add_controller(self._motion)

    def _on_enter(self, *args):
        self.set_cursor(Gdk.Cursor.new_from_name("pointer", None))

    def _on_leave(self, *args):
        self.set_cursor(None)

    def _build(self):
        pkg    = self.pkg
        latest = pkg["versions"][0] if pkg.get("versions") else {}
        is_inst = self.manager.is_installed(pkg["full_name"])
        has_upd = self.manager.has_update(pkg)

        if has_upd:
            self.add_css_class("has-update")
        elif is_inst:
            self.add_css_class("is-installed")

        # ── Icon / Rune ─────────────────────────────────────
        self._icon_frame = Gtk.Box()
        self._icon_frame.add_css_class("mod-icon-frame")
        self._icon_frame.set_size_request(64, 64)
        self._icon_frame.set_valign(Gtk.Align.CENTER)

        self._rune_lbl = Gtk.Label(label=pkg["name"][0].upper())
        self._rune_lbl.set_halign(Gtk.Align.CENTER)
        self._rune_lbl.set_valign(Gtk.Align.CENTER)
        self._rune_lbl.set_hexpand(True)
        self._rune_lbl.set_vexpand(True)
        self._icon_frame.append(self._rune_lbl)
        self.append(self._icon_frame)

        # ── Info ────────────────────────────────────────────
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info.set_hexpand(True)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        name_lbl = Gtk.Label(label=pkg["name"])
        name_lbl.add_css_class("mod-name")

        author_lbl = Gtk.Label()
        author_lbl.set_markup(f'<span foreground="#5a4f3d">par</span> {pkg["owner"]}')
        author_lbl.add_css_class("mod-author")

        ver_lbl = Gtk.Label(label=f"v{latest.get('version_number','?')}")
        ver_lbl.add_css_class("mod-version")
        ver_lbl.set_hexpand(True); ver_lbl.set_halign(Gtk.Align.END)

        row1.append(name_lbl); row1.append(author_lbl); row1.append(ver_lbl)
        info.append(row1)

        desc_lbl = Gtk.Label(label=latest.get("description") or "Aucune description.")
        desc_lbl.add_css_class("mod-desc")
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.set_wrap(True)
        desc_lbl.set_lines(2)
        desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        info.append(desc_lbl)

        meta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        rating   = pkg.get("rating_score", 0)
        total_dl = sum(v.get("downloads", 0) for v in pkg.get("versions", []))

        for txt, glyph in [(f"{rating}", "★"), (f"{fmt_number(total_dl)}", "↓")]:
            m_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            g = Gtk.Label(label=glyph); g.set_opacity(0.6)
            t = Gtk.Label(label=txt)
            m_box.append(g); m_box.append(t)
            m_box.add_css_class("mod-stat")
            meta.append(m_box)

        cat_tag = Gtk.Label(label=(pkg.get("categories") or ["Mod"])[0])
        cat_tag.add_css_class("tag")
        meta.append(cat_tag)

        if is_inst:
            inst_tag = Gtk.Label(label="Installé")
            inst_tag.add_css_class("tag"); inst_tag.add_css_class("gold")
            meta.append(inst_tag)

        info.append(meta)
        self.append(info)

        # ── Actions ─────────────────────────────────────────
        actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        actions.set_valign(Gtk.Align.CENTER)

        if has_upd:
            self._inst_btn = Gtk.Button(label="↑ Mettre à jour")
            self._inst_btn.add_css_class("primary"); self._inst_btn.add_css_class("sm")
            self._inst_btn.connect("clicked", lambda _: self._on_install())
        elif is_inst:
            self._inst_btn = Gtk.Button(label="✓ Installé")
            self._inst_btn.add_css_class("ghost"); self._inst_btn.add_css_class("sm")
            self._inst_btn.set_sensitive(False)
        else:
            self._inst_btn = Gtk.Button(label="+ Installer")
            self._inst_btn.add_css_class("primary"); self._inst_btn.add_css_class("sm")
            self._inst_btn.connect("clicked", lambda _: self._on_install())

        det_btn = Gtk.Button(label="Détails →")
        det_btn.add_css_class("ghost"); det_btn.add_css_class("sm")
        det_btn.connect("clicked", lambda *_: self.on_click(self.pkg))

        actions.append(self._inst_btn); actions.append(det_btn)
        self.append(actions)

        if url := latest.get("icon"):
            fetch_icon_async(url, self._set_icon)

    def _set_icon(self, path: str):
        try:
            img = Gtk.Image.new_from_file(path)
            img.set_pixel_size(64)
            child = self._icon_frame.get_first_child()
            if child: self._icon_frame.remove(child)
            self._icon_frame.append(img)
        except Exception as e:
            logger.error(f"Erreur d'affichage de l'icone {path}: {e}")

    def _on_install(self):
        self._inst_btn.set_sensitive(False)
        latest = self.pkg["versions"][0]
        self.manager.install_async(
            self.pkg, latest,
            lambda f, t: self._inst_btn.set_label(f"Forgeron : {int(f * 100)}%"),
            self._on_install_ok,
            self._on_install_err,
        )

    def _on_install_ok(self, pkg):
        self._inst_btn.set_label("✓ Installé")
        self.add_css_class("is-installed")
        self.remove_css_class("has-update")
        self.show_toast(f"{pkg['name']} est prêt !", "success")

    def _on_install_err(self, msg):
        self._inst_btn.set_sensitive(True)
        self._inst_btn.set_label("+ Installer")
        self.show_toast(f"Échec : {msg}", "error")
