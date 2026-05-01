import logging
import subprocess
from gi.repository import Gtk, GLib, Pango
from vmm.logic import fetch_icon_async
from vmm.utils import fmt_number, fmt_date

logger = logging.getLogger("ValheimModManager")

class DetailPage(Gtk.Box):
    __gtype_name__ = "DetailPage"

    def __init__(self, manager, show_toast, on_back, on_install_done=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.manager          = manager
        self.show_toast       = show_toast
        self.on_back          = on_back
        self._on_install_done = on_install_done
        self._pkg             = None
        self._build()

    def _build(self):
        # ── Header ──────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hdr.add_css_class("main-header")
        
        back_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        back_btn = Gtk.Button(label="← Retour à la bibliothèque")
        back_btn.add_css_class("ghost"); back_btn.add_css_class("sm")
        back_btn.set_halign(Gtk.Align.START)
        back_btn.connect("clicked", lambda _: self.on_back())
        
        sub = Gtk.Label(label="Fiche du mod")
        sub.add_css_class("main-sub"); sub.set_halign(Gtk.Align.START)
        
        back_box.append(back_btn); back_box.append(sub)
        hdr.append(back_box)
        self.append(hdr)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        container.set_margin_start(32); container.set_margin_end(32); container.set_margin_top(24); container.set_margin_bottom(32)
        
        # ── Hero Section ─────────────────────────────────────
        self._hero = self._build_hero()
        container.append(self._hero)
        
        # ── Content Grid ────────────────────────────────────
        grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        
        # Left column
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        left.set_hexpand(True)
        
        self._desc_sec = self._make_section("ᚦ Description", "")
        self._desc_lbl = Gtk.Label(); self._desc_lbl.set_wrap(True); self._desc_lbl.set_halign(Gtk.Align.START)
        self._desc_lbl.add_css_class("detail-desc")
        self._desc_sec._content.append(self._desc_lbl)
        
        self._deps_sec = self._make_section("ᛟ Dépendances", "")
        self._deps_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._deps_sec._content.append(self._deps_list)

        self._changelog_sec = self._make_section("ᛉ Journal des versions", "")
        self._changelog_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._changelog_sec._content.append(self._changelog_list)
        
        left.append(self._desc_sec); left.append(self._deps_sec); left.append(self._changelog_sec)
        grid.append(left)
        
        # Right column
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        right.set_size_request(220, -1)
        self._info_card = self._build_info_card()
        right.append(self._info_card)
        grid.append(right)
        
        container.append(grid)
        scroll.set_child(container)
        self.append(scroll)

    def _build_hero(self) -> Gtk.Box:
        hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        hero.add_css_class("detail-hero")
        self._icon_frame = Gtk.Box(); self._icon_frame.add_css_class("detail-icon"); self._icon_frame.set_size_request(140, 140)
        self._rune_lbl = Gtk.Label(label="ᚱ"); self._icon_frame.append(self._rune_lbl)
        hero.append(self._icon_frame)
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); info.set_hexpand(True)
        self._name_lbl = Gtk.Label(); self._name_lbl.add_css_class("detail-name"); self._name_lbl.set_halign(Gtk.Align.START)
        self._author_lbl = Gtk.Label(); self._author_lbl.add_css_class("detail-author"); self._author_lbl.set_halign(Gtk.Align.START)
        self._tags_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        stats = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=32); stats.set_margin_top(12)
        self._stat_rating = self._make_hero_stat("Notes", "★"); self._stat_dl = self._make_hero_stat("Téléchargements", "↓")
        self._stat_deps = self._make_hero_stat("Dépendances", "⌬")
        stats.append(self._stat_rating); stats.append(self._stat_dl); stats.append(self._stat_deps)
        info.append(self._name_lbl); info.append(self._author_lbl); info.append(self._tags_box); info.append(stats)
        hero.append(info)
        actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); actions.set_valign(Gtk.Align.CENTER)
        self._install_btn = Gtk.Button(label="+ Installer le mod"); self._install_btn.add_css_class("primary")
        self._thunder_btn = Gtk.Button(label="⌘ Voir sur Thunderstore")
        actions.append(self._install_btn); actions.append(self._thunder_btn)
        hero.append(actions)
        return hero

    def _make_hero_stat(self, label, icon) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        v = Gtk.Label(); v.add_css_class("detail-stat-val")
        l = Gtk.Label(label=f"{icon} {label}"); l.add_css_class("detail-stat-lbl")
        box.append(v); box.append(l); box._val = v
        return box

    def _make_section(self, title, footer_text) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); box.add_css_class("detail-section")
        t = Gtk.Label(label=title); t.set_halign(Gtk.Align.START); t.add_css_class("section-label")
        sep = Gtk.Separator(); sep.set_margin_bottom(4)
        box.append(t); box.append(sep); box._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); box.append(box._content)
        return box

    def _build_info_card(self) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14); card.add_css_class("info-card")
        t = Gtk.Label(label="Informations"); t.set_halign(Gtk.Align.START); t.add_css_class("section-label")
        card.append(t); self._info_rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); card.append(self._info_rows)
        card.append(Gtk.Separator()); lt = Gtk.Label(label="Liens runiques"); lt.set_halign(Gtk.Align.START)
        lt.add_css_class("section-label"); card.append(lt)
        self._links_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); card.append(self._links_box)
        return card

    def _add_info_row(self, key, value):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        kl = Gtk.Label(label=key); kl.add_css_class("detail-stat-lbl"); kl.set_opacity(0.7)
        vl = Gtk.Label(label=value); vl.add_css_class("nav-count"); vl.set_hexpand(True); vl.set_halign(Gtk.Align.END)
        row.append(kl); row.append(vl); self._info_rows.append(row)

    def _add_dep_row(self, dep_str):
        # Format Thunderstore: Author-Name-Major.Minor.Patch
        # Le nom peut contenir des tirets — on prend tout entre le 1er et le dernier segment
        parts = dep_str.split('-')
        if len(parts) >= 3:
            author = parts[0]
            name   = '-'.join(parts[1:-1])
            meta   = f"v{parts[-1]}"
        elif len(parts) == 2:
            author, name, meta = parts[0], parts[1], ""
        else:
            author, name, meta = "", dep_str, ""

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("dep-row")

        icon = Gtk.Box(); icon.add_css_class("dep-icon")
        icon.set_size_request(32, 32)
        icon.set_halign(Gtk.Align.START); icon.set_valign(Gtk.Align.CENTER)
        lbl_icon = Gtk.Label(label=name[0].upper() if name else "?")
        lbl_icon.set_halign(Gtk.Align.CENTER); lbl_icon.set_valign(Gtk.Align.CENTER)
        lbl_icon.set_vexpand(True)
        icon.append(lbl_icon); row.append(icon)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); info.set_hexpand(True)
        nl = Gtk.Label(label=name); nl.add_css_class("dep-name"); nl.set_halign(Gtk.Align.START)
        ml = Gtk.Label(label=meta); ml.add_css_class("dep-meta"); ml.set_halign(Gtk.Align.START)
        info.append(nl); info.append(ml); row.append(info)

        is_inst = self.manager.is_installed(f"{author}-{name}") if author else False
        status = Gtk.Label(label="\u2713 Installé" if is_inst else "\u2717 Non installé")
        status.add_css_class("dep-status"); status.add_css_class("installed" if is_inst else "required")
        row.append(status)
        self._deps_list.append(row)

    def _add_changelog_row(self, version_obj):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("changelog-item")
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        tag = Gtk.Label(label=f"v{version_obj.get('version_number', '?')}")
        tag.add_css_class("ver-tag"); tag.set_halign(Gtk.Align.START)
        date = Gtk.Label(label=fmt_date(version_obj.get('date_created', "")))
        date.add_css_class("ver-date"); date.set_hexpand(True); date.set_halign(Gtk.Align.END)
        hdr.append(tag); hdr.append(date); box.append(hdr)
        desc = version_obj.get('description', "")
        if desc:
            dl = Gtk.Label(label=desc); dl.set_wrap(True); dl.set_halign(Gtk.Align.START)
            dl.add_css_class("nav-count"); dl.set_opacity(0.8); box.append(dl)
        self._changelog_list.append(box)

    def load(self, pkg: dict):
        self._pkg = pkg; latest = pkg["versions"][0] if pkg.get("versions") else {}
        self._name_lbl.set_text(pkg["name"])
        self._author_lbl.set_markup(f'par <b>{pkg["owner"]}</b> \u00b7 <span font_family="monospace">v{latest.get("version_number","?")}</span>')
        
        # Buttons connection
        try: self._install_btn.disconnect_by_func(self._on_install_clicked)
        except: pass
        self._install_btn.connect("clicked", self._on_install_clicked)
        if self.manager.is_installed(pkg["full_name"]):
            if self.manager.has_update(pkg):
                self._install_btn.set_label("↑ Mettre à jour")
                self._install_btn.set_sensitive(True)
            else:
                self._install_btn.set_label("✓ Déjà installé")
                self._install_btn.set_sensitive(False)
        else:
            self._install_btn.set_label("+ Installer le mod")
            self._install_btn.set_sensitive(True)
        
        url_thunder = f"https://thunderstore.io/c/valheim/p/{pkg['owner']}/{pkg['name']}/"
        try: self._thunder_btn.disconnect_by_func(self._on_thunder_clicked)
        except: pass
        self._thunder_btn.connect("clicked", lambda _: subprocess.Popen(["xdg-open", url_thunder]))

        deps = latest.get("dependencies", []); self._stat_rating._val.set_text(str(pkg.get("rating_score", 0)))
        total_dl = sum(v.get("downloads", 0) for v in pkg.get("versions", [])); self._stat_dl._val.set_text(fmt_number(total_dl))
        self._stat_deps._val.set_text(str(len(deps))); self._desc_lbl.set_text(latest.get("description") or "Aucune description.")
        while (c := self._deps_list.get_first_child()): self._deps_list.remove(c)
        if not deps:
            empty = Gtk.Label(label="Aucune dépendance externe — ce mod est autonome.")
            empty.add_css_class("nav-count"); empty.set_halign(Gtk.Align.START); self._deps_list.append(empty)
        else:
            for d in deps: self._add_dep_row(d)
        
        # Changelog
        while (c := self._changelog_list.get_first_child()): self._changelog_list.remove(c)
        versions = pkg.get("versions", [])
        if not versions:
            empty = Gtk.Label(label="Aucun historique disponible."); empty.add_css_class("nav-count")
            empty.set_halign(Gtk.Align.START); self._changelog_list.append(empty)
        else:
            for v in versions[:5]: self._add_changelog_row(v)

        while (c := self._tags_box.get_first_child()): self._tags_box.remove(c)
        for cat in pkg.get("categories", []):
            tag = Gtk.Label(label=cat); tag.add_css_class("tag"); self._tags_box.append(tag)
        while (c := self._info_rows.get_first_child()): self._info_rows.remove(c)
        self._add_info_row("Auteur", pkg["owner"]); self._add_info_row("Version", latest.get("version_number", "?"))
        self._add_info_row("Catégorie", (pkg.get("categories") or ["?"])[0]); self._add_info_row("Mise à jour", fmt_date(pkg.get("date_updated", "")))
        while (c := self._links_box.get_first_child()): self._links_box.remove(c)
        btn = Gtk.LinkButton(uri=url_thunder, label="\u2197 Page Thunderstore"); btn.add_css_class("ghost"); btn.add_css_class("sm"); btn.set_halign(Gtk.Align.START); self._links_box.append(btn)
        if url := latest.get("icon"): fetch_icon_async(url, self._set_icon)
        else:
            c = self._icon_frame.get_first_child(); 
            if c: self._icon_frame.remove(c)
            self._icon_frame.append(Gtk.Label(label=pkg["name"][0].upper()))

    def _set_icon(self, path: str):
        img = Gtk.Image.new_from_file(path); img.set_pixel_size(140); c = self._icon_frame.get_first_child()
        if c: self._icon_frame.remove(c)
        self._icon_frame.append(img)

    def _on_install_clicked(self, btn):
        btn.set_sensitive(False); latest = self._pkg["versions"][0]
        self.manager.install_async(self._pkg, latest, self._on_progress, self._on_ok, self._on_err)

    def _on_progress(self, f, t): self._install_btn.set_label(f"Forgeron : {int(f*100)}%")
    def _on_ok(self, pkg):
        self._install_btn.set_label("\u2713 Install\u00e9 !")
        if pkg.get("_steam_opts_set"):
            self.show_toast(f"{pkg['name']} install\u00e9 \u2014 options Steam configur\u00e9es automatiquement !", "success")
        else:
            self.show_toast(f"{pkg['name']} est pr\u00eat !", "success")
        self.load(pkg)
        if self._on_install_done:
            self._on_install_done()
    def _on_err(self, msg):
        self._install_btn.set_sensitive(True); self._install_btn.set_label("Ressayer l'installation"); self.show_toast(f"Échec : {msg}", "error")
