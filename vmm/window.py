from gi.repository import Gtk, Gdk, GLib
import subprocess
from vmm.constants import APP_NAME
from vmm.utils import fmt_number
from vmm.ui.common import ToastOverlay
from vmm.ui.pages.browse import BrowsePage
from vmm.ui.pages.installed import InstalledPage
from vmm.ui.pages.settings import SettingsPage
from vmm.ui.pages.detail import DetailPage

class AppWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "ValheimModManagerWindow"

    def __init__(self, app, manager):
        super().__init__(application=app)
        self.manager = manager
        self.set_title(APP_NAME)
        self.set_default_size(1280, 840)
        self.add_css_class("win-frame")
        self._build_ui()
        self._setup_keys()

    def _build_ui(self):
        # ── Header Bar (GTK native area) ────────────────────
        hb = Gtk.HeaderBar()
        hb.set_show_title_buttons(True)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.add_css_class("display-font")
        t = Gtk.Label(label="\u2694  Valheim Mod Manager")
        t.add_css_class("title")
        title_box.append(t)
        hb.set_title_widget(title_box)

        self._refresh_btn = Gtk.Button()
        self._refresh_btn.set_icon_name("view-refresh-symbolic")
        self._refresh_btn.set_tooltip_text("Recharger depuis Thunderstore (F5)")
        self._refresh_btn.connect("clicked", lambda _: self._reload())
        hb.pack_end(self._refresh_btn)

        # Lancer le jeu
        self._launch_btn = Gtk.Button(label="\u2694 Lancer")
        self._launch_btn.add_css_class("primary")
        self._launch_btn.set_tooltip_text("Lancer Valheim avec BepInEx")
        self._launch_btn.connect("clicked", self._launch_game)
        hb.pack_end(self._launch_btn)

        self.set_titlebar(hb)

        # ── Main Layout ────────────────────────────────────
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Warning Bar (BepInEx)
        self._bep_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._bep_bar.add_css_class("warn-bar")
        self._bep_bar.set_visible(False)
        
        warn_icon = Gtk.Label(label="\u26a0")
        warn_icon.set_margin_start(4)
        
        warn_msg = Gtk.Label(label="BepInEx non détecté — les mods ne se chargeront pas.")
        warn_msg.set_hexpand(True); warn_msg.set_halign(Gtk.Align.START)

        warn_install = Gtk.Button(label="⬇ Installer BepInEx (Linux)")
        warn_install.add_css_class("primary"); warn_install.add_css_class("sm")
        warn_install.connect("clicked", self._install_bepinex)

        warn_close = Gtk.Button()
        warn_close.set_icon_name("window-close-symbolic")
        warn_close.add_css_class("flat")
        warn_close.connect("clicked", lambda _: self._bep_bar.set_visible(False))

        self._bep_bar.append(warn_icon)
        self._bep_bar.append(warn_msg)
        self._bep_bar.append(warn_install)
        self._bep_bar.append(warn_close)
        
        root.append(self._bep_bar)

        # Body grid: Sidebar + Content
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        body.set_vexpand(True)
        
        # ── Sidebar ────────────────────────────────────────
        self._sidebar = self._build_sidebar()
        body.append(self._sidebar)
        
        # ── Content Stack ──────────────────────────────────
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(250)
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)
        
        self._browse_page = BrowsePage(self.manager, self._show_toast, self._on_refresh_installed, self._on_open_mod)
        
        self._detail_page = DetailPage(self.manager, self._show_toast, self._on_back_to_browse,
                                       on_install_done=self._on_mod_installed)
        self._installed_page = InstalledPage(self.manager, lambda: self._browse_page.all_packages, self._show_toast, self._on_installed_changed)
        self._settings_page = SettingsPage(self.manager, self._show_toast)
        
        self._stack.add_named(self._browse_page, "browse")
        self._stack.add_named(self._detail_page, "detail")
        self._stack.add_named(self._installed_page, "installed")
        self._stack.add_named(self._settings_page, "settings")
        
        # Add a detail overlay for browsing
        self._toast = ToastOverlay(self._stack)
        self._toast.set_vexpand(True)
        body.append(self._toast)
        
        root.append(body)
        self.set_child(root)

    def _build_sidebar(self) -> Gtk.Box:
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sb.add_css_class("sidebar")
        sb.set_size_request(220, -1)

        # Brand
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        brand.set_margin_top(16); brand.set_margin_bottom(16); brand.set_margin_start(18); brand.set_margin_end(18)
        
        b_title = Gtk.Label(label="\u2694  VALHEIM")
        b_title.add_css_class("sb-brand-title")
        b_title.set_halign(Gtk.Align.START)
        
        b_sub = Gtk.Label(label="Mod Manager")
        b_sub.add_css_class("sb-brand-sub")
        b_sub.set_halign(Gtk.Align.START)
        
        brand.append(b_title); brand.append(b_sub)
        sb.append(brand)

        # Stats
        stats = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        stats.add_css_class("sb-stats")
        
        self._stat_mods = self._make_sb_stat("—", "Mods")
        self._stat_active = self._make_sb_stat("—", "Actifs")
        self._stat_upd = self._make_sb_stat("—", "MAJ")
        
        stats.append(self._stat_mods); stats.append(self._stat_active); stats.append(self._stat_upd)
        sb.append(stats)

        # Navigation
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        nav.set_margin_start(10); nav.set_margin_end(10)
        
        self._nav_items = {}
        for id, label, rune in [
            ("browse", "Parcourir", "ᛒ"),
            ("installed", "Mes mods", "ᛗ"),
            ("settings", "Paramètres", "ᛟ"),
        ]:
            btn = Gtk.Button()
            btn.add_css_class("sb-nav-item")
            if id == "browse": btn.add_css_class("active")
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            r_lbl = Gtk.Label(label=rune); r_lbl.add_css_class("rune")
            l_lbl = Gtk.Label(label=label); l_lbl.set_hexpand(True); l_lbl.set_halign(Gtk.Align.START)
            box.append(r_lbl); box.append(l_lbl)
            
            btn.set_child(box)
            btn.connect("clicked", lambda _, i=id: self._switch_tab(i))
            nav.append(btn)
            self._nav_items[id] = btn
            
        sb.append(nav)

        # Categories
        cat_sep = Gtk.Label(label="Catégories")
        cat_sep.add_css_class("sb-section-label")
        cat_sep.set_margin_top(20); cat_sep.set_margin_bottom(8)
        sb.append(cat_sep)

        cat_scroll = Gtk.ScrolledWindow()
        cat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        cat_scroll.set_vexpand(True)
        self._cat_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        cat_scroll.set_child(self._cat_container)
        sb.append(cat_scroll)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.add_css_class("sb-footer")
        
        dot = Gtk.Label(label="\u2022")
        dot.add_css_class("dot")
        status = Gtk.Label(label="Thunderstore \u00b7 Connecté")
        footer.append(dot); footer.append(status)
        sb.append(footer)

        return sb

    def _make_sb_stat(self, val, lbl) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_hexpand(True)
        v = Gtk.Label(label=val); v.add_css_class("sb-stat-val")
        l = Gtk.Label(label=lbl); l.add_css_class("sb-stat-lbl")
        box.append(v); box.append(l)
        box._val_lbl = v
        return box

    def _switch_tab(self, id):
        nav_id = "browse" if id == "detail" else id
        for k, btn in self._nav_items.items():
            if k == nav_id: btn.add_css_class("active")
            else: btn.remove_css_class("active")
        
        self._stack.set_visible_child_name(id)
        if id == "installed":
            self._installed_page.refresh()
        elif id == "settings":
            self._check_bepinex_bar()
        
        self._cat_container.set_visible(id == "browse" or id == "detail")

    def _on_open_mod(self, pkg):
        self._detail_page.load(pkg)
        self._switch_tab("detail")

    def _on_back_to_browse(self):
        self._switch_tab("browse")

    def _show_toast(self, msg, kind="info"):
        self._toast.show(msg, kind)

    def _check_bepinex_bar(self):
        self._bep_bar.set_visible(not self.manager.has_bepinex)

    def _install_bepinex(self, _):
        BEPINEX = "denikson-BepInExPack_Valheim"
        pkg = next((p for p in self._browse_page.all_packages
                    if p.get("full_name") == BEPINEX), None)
        if pkg:
            self._on_open_mod(pkg)
        else:
            import subprocess
            subprocess.Popen(["xdg-open",
                "https://thunderstore.io/c/valheim/p/denikson/BepInExPack_Valheim/"])

    def _on_refresh_installed(self):
        self._update_installed_badge()
        if not self._cat_container.get_first_child():
            self._browse_page.populate_sidebar_cats(self._cat_container)

    def _on_mod_installed(self):
        self._check_bepinex_bar()
        self._on_installed_changed()

    def _on_installed_changed(self):
        self._browse_page.refresh_all()
        self._update_installed_badge()

    def _update_installed_badge(self):
        n_total = len(self._browse_page.all_packages)
        n_inst = len(self.manager.installed)
        n_upd = self.manager.count_updates(self._browse_page.all_packages)
        
        self._stat_mods._val_lbl.set_text(fmt_number(n_total))
        self._stat_active._val_lbl.set_text(str(n_inst))
        self._stat_upd._val_lbl.set_text(str(n_upd))

    def _setup_keys(self):
        kc = Gtk.EventControllerKey()
        kc.connect("key-pressed", self._on_key)
        self.add_controller(kc)

    def _on_key(self, controller, keyval, keycode, state):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and keyval == Gdk.KEY_f:
            self._switch_tab("browse")
            self._browse_page.focus_search()
            return True
        if keyval == Gdk.KEY_F5:
            self._reload()
            return True
        if keyval == Gdk.KEY_Escape:
            if self._stack.get_visible_child_name() == "detail":
                self._on_back_to_browse()
                return True
            return self._browse_page.escape_pressed()
        return False

    def _launch_game(self, _):
        from vmm.utils_patch import patch_launch_script
        patch_launch_script(self.manager.valheim_path)
        
        try:
            # Lancement via le script BepInEx en utilisant le protocole Steam pour attacher Steamworks
            subprocess.Popen(["steam", "steam://run/892970"])
            self._show_toast("Lancement via Steam...", "success")
        except Exception as e:
            self._show_toast(f"Erreur lancement : {e}", "error")

    def _reload(self):
        self._refresh_btn.set_sensitive(False)
        self._browse_page.start_load()
        GLib.timeout_add(500, lambda: self._refresh_btn.set_sensitive(True) or False)

    def start_load(self):
        self._check_bepinex_bar()
        self._browse_page.start_load()
