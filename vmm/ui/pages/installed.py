import subprocess
from pathlib import Path
from gi.repository import Gtk, GLib, Pango
from vmm.utils import fmt_size, fmt_number
from vmm.ui.common import make_rune_sep, make_empty_state

class InstalledPage(Gtk.Box):
    __gtype_name__ = "InstalledPage"

    def __init__(self, manager, all_packages_getter, show_toast, on_changes):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.manager            = manager
        self.get_all_packages   = all_packages_getter
        self.show_toast         = show_toast
        self.on_changes         = on_changes
        self._build()

    def _build(self):
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        banner.add_css_class("main-header")

        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        t = Gtk.Label()
        t.set_markup(
            '<span foreground="#d4a04c" font_size="small">ᛗ ᛟ ᛞ</span>'
            '  <span font_weight="bold">Équipement Installé</span>  '
            '<span foreground="#d4a04c" font_size="small">ᛞ ᛟ ᛗ</span>'
        )
        t.add_css_class("main-title")
        t.set_halign(Gtk.Align.START)
        titles.append(t)

        s = Gtk.Label(label="Vos artefacts actifs dans les dix royaumes")
        s.add_css_class("main-sub")
        s.set_halign(Gtk.Align.START)
        titles.append(s)
        banner.append(titles)

        self._count_lbl = Gtk.Label()
        self._count_lbl.add_css_class("results-count")
        self._count_lbl.set_hexpand(True); self._count_lbl.set_halign(Gtk.Align.END)
        banner.append(self._count_lbl)

        self.append(banner)

        # Rune Divider
        div = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        div.set_halign(Gtk.Align.CENTER)
        div.set_margin_top(-10)
        rune_div = Gtk.Label(label="\u16ac \u16c8 \u16d2 \u16ac")
        rune_div.add_css_class("rune-divider")
        div.append(rune_div)
        self.append(div)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_margin_start(32); container.set_margin_end(32); container.set_margin_top(24); container.set_margin_bottom(32)

        # Profiles Bar
        profiles = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        profiles.add_css_class("profiles-bar")
        l = Gtk.Label(label="Profil"); l.set_opacity(0.6)
        profiles.append(l)

        for p in ["ᚠ Aventure principale", "ᛏ Test"]:
            c = Gtk.Button(label=p); c.add_css_class("profile-chip")
            if "Aventure" in p: c.add_css_class("active")
            profiles.append(c)

        open_btn = Gtk.Button(label="📁 Ouvrir plugins/")
        open_btn.add_css_class("sm"); open_btn.set_hexpand(True); open_btn.set_halign(Gtk.Align.END)
        open_btn.connect("clicked", self._open_plugins_dir)
        profiles.append(open_btn)

        container.append(profiles)

        self._list = Gtk.ListBox()
        self._list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list.set_margin_top(4)

        container.append(self._list)
        scroll.set_child(container)
        self.append(scroll)

    def refresh(self):
        while (row := self._list.get_row_at_index(0)):
            self._list.remove(row)

        installed = self.manager.installed
        n         = len(installed)
        pkgs_map  = {p["full_name"]: p for p in self.get_all_packages()}
        
        n_upd = 0
        for fn in installed:
            pkg = pkgs_map.get(fn)
            if pkg and self.manager.has_update(pkg):
                n_upd += 1

        self._count_lbl.set_markup(f"<b>{n}</b> actifs \u00b7 <span foreground='#d49a3c'><b>{n_upd}</b></span> mises à jour")

        if not installed:
            empty = make_empty_state(
                "\u2694",
                "Inventaire vide",
                "Explorez les mods disponibles dans l'onglet Parcourir.",
            )
            row = Gtk.ListBoxRow(); row.set_selectable(False); row.set_child(empty)
            self._list.append(row)
            return

        for full_name, info in sorted(installed.items(), key=lambda x: x[1].get("name", "")):
            self._append_row(full_name, info, pkgs_map)

    def _append_row(self, full_name: str, info: dict, pkgs_map: dict):
        row = Gtk.ListBoxRow(); row.set_selectable(False); row.set_margin_bottom(8)
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.add_css_class("mod-card")

        sw = Gtk.Switch(); sw.set_active(info.get("enabled", True)); sw.set_valign(Gtk.Align.CENTER)
        sw.connect("state-set", lambda w, s, fn=full_name: self._on_toggle(fn, s))
        card.append(sw)

        icon_frame = Gtk.Box(); icon_frame.add_css_class("mod-icon-frame")
        icon_frame.set_size_request(48, 48)
        icon_frame.set_halign(Gtk.Align.START); icon_frame.set_valign(Gtk.Align.CENTER)
        rune = Gtk.Label(label=info.get("name", "?")[0].upper())
        rune.set_halign(Gtk.Align.CENTER); rune.set_valign(Gtk.Align.CENTER)
        rune.set_hexpand(True); rune.set_vexpand(True)
        icon_frame.append(rune)
        card.append(icon_frame)

        ib = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); ib.set_hexpand(True); ib.set_valign(Gtk.Align.CENTER)
        nl = Gtk.Label(); nl.set_halign(Gtk.Align.START)
        nl.set_markup(f'<b>{info.get("name", full_name)}</b> <span foreground="#5a4f3d" font_family="monospace" size="small">v{info.get("version","?")}</span>')
        ib.append(nl)
        ml = Gtk.Label(label=f'par {info.get("owner","?")}')
        ml.set_halign(Gtk.Align.START); ml.set_opacity(0.6); ml.add_css_class("nav-count")
        ib.append(ml)
        card.append(ib)

        pkg = pkgs_map.get(full_name)
        if pkg and self.manager.has_update(pkg):
            upd = Gtk.Label(label="↑ MAJ disponible"); upd.add_css_class("tag"); upd.add_css_class("gold"); upd.set_valign(Gtk.Align.CENTER)
            card.append(upd)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); btn_box.set_valign(Gtk.Align.CENTER)
        cfg_btn = Gtk.Button(label="⚙"); cfg_btn.add_css_class("ghost"); cfg_btn.add_css_class("sm")
        btn_box.append(cfg_btn)
        del_btn = Gtk.Button(label="✕"); del_btn.add_css_class("ghost"); del_btn.add_css_class("sm")
        del_btn.connect("clicked", lambda *_: self._uninstall(full_name, info.get("name")))
        btn_box.append(del_btn)
        card.append(btn_box)

        row.set_child(card)
        self._list.append(row)

    def _uninstall(self, full_name: str, display_name: str):
        name = self.manager.uninstall(full_name)
        if name: self.show_toast(f"Retire : {name}", "info")
        self.refresh(); self.on_changes()

    def _on_toggle(self, full_name: str, enabled: bool) -> bool:
        if not self.manager.set_enabled(full_name, enabled):
            self.show_toast("Erreur lors du changement d'état", "error")
            return True
        return False

    def _open_plugins_dir(self, _):
        d = self.manager.plugins_path
        if d.exists():
            try: subprocess.Popen(["xdg-open", str(d)])
            except Exception as e:
                import logging
                logging.getLogger("ValheimModManager").error(f"Erreur dossier plugins: {e}")
                self.show_toast("Erreur d'ouverture", "error")
        else: self.show_toast("Dossier introuvable", "warning")
