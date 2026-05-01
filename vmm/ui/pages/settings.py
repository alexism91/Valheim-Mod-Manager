import shutil
import logging
from gi.repository import Gtk, Gdk
from vmm.constants import APP_NAME, APP_VERSION, CONFIG_DIR, ICON_CACHE_DIR, DOWNLOAD_DIR
from vmm.utils import fmt_size
from vmm.ui.common import make_rune_sep

logger = logging.getLogger("ValheimModManager")

class SettingsPage(Gtk.Box):
    __gtype_name__ = "SettingsPage"

    def __init__(self, manager, show_toast):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.manager    = manager
        self.show_toast = show_toast
        self._build()

    def _build(self):
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        banner.add_css_class("main-header")

        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        t = Gtk.Label()
        t.set_markup(
            '<span foreground="#d4a04c" font_size="small">ᛟ ᛟ ᛟ</span>'
            '  <span font_weight="bold">Runes de Configuration</span>  '
            '<span foreground="#d4a04c" font_size="small">ᛟ ᛟ ᛟ</span>'
        )
        t.add_css_class("main-title")
        t.set_halign(Gtk.Align.START)
        titles.append(t)
        
        s = Gtk.Label(label="Paramètres du gestionnaire")
        s.add_css_class("main-sub")
        s.set_halign(Gtk.Align.START)
        titles.append(s)
        banner.append(titles)
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

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        center_box.set_margin_start(32); center_box.set_margin_end(32); center_box.set_margin_top(24); center_box.set_margin_bottom(32)
        center_box.set_hexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        center_box.append(content)

        # ── Groupe : Intégration Steam ────────────────────────
        steam_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        steam_card.add_css_class("settings-card")

        t = Gtk.Label(label="ᚠ Intégration Steam"); t.add_css_class("settings-group-title"); t.set_halign(Gtk.Align.START)
        h = Gtk.Label(label="Configuration requise pour charger BepInEx automatiquement"); h.add_css_class("settings-hint"); h.set_halign(Gtk.Align.START)
        steam_card.append(t); steam_card.append(h)

        cmd = f"{self.manager.valheim_path}/start_game_bepinex.sh %command%"
        cmd_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        entry = Gtk.Entry(); entry.set_text(cmd); entry.set_editable(False); entry.set_hexpand(True)
        cmd_row.append(entry)

        copy_btn = Gtk.Button(label="\u2750 Copier")
        copy_btn.connect("clicked", lambda _: self._copy_to_clipboard(cmd))
        cmd_row.append(copy_btn)
        steam_card.append(cmd_row)

        instr = Gtk.Label(label="1. Clic-droit sur Valheim dans Steam > Propriétés\n2. Collez cette commande dans 'Options de lancement'")
        instr.add_css_class("settings-hint"); instr.set_halign(Gtk.Align.START)
        steam_card.append(instr)

        content.append(steam_card)

        # ── Groupe : Chemin Valheim ───────────────────────────
        valheim_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        
        path_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._path_entry = Gtk.Entry()
        self._path_entry.set_text(str(self.manager.valheim_path))
        self._path_entry.set_hexpand(True)
        path_row.append(self._path_entry)
        br = Gtk.Button(label="Parcourir...")
        br.connect("clicked", self._browse)
        path_row.append(br)
        valheim_card.append(path_row)

        self._bep_lbl = Gtk.Label(); self._bep_lbl.set_halign(Gtk.Align.START)
        valheim_card.append(self._bep_lbl)
        self._refresh_bepinex_status()

        save_btn = Gtk.Button(label="⚒ Enregistrer les modifications")
        save_btn.add_css_class("primary"); save_btn.add_css_class("sm")
        save_btn.set_halign(Gtk.Align.START)
        save_btn.connect("clicked", self._save)
        valheim_card.append(save_btn)
        
        content.append(valheim_card)

        # ── Groupe : Cache ────────────────────────────────────
        cache_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        cache_card.add_css_class("settings-card")
        
        t = Gtk.Label(label="ᚲ Gestion du cache"); t.add_css_class("settings-group-title"); t.set_halign(Gtk.Align.START)
        h = Gtk.Label(label="Icônes et archives téléchargées"); h.add_css_class("settings-hint"); h.set_halign(Gtk.Align.START)
        cache_card.append(t); cache_card.append(h)
        
        cache_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        size_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._cache_size_lbl = Gtk.Label(label=self._get_cache_size())
        self._cache_size_lbl.set_halign(Gtk.Align.START); self._cache_size_lbl.add_css_class("sb-stat-val")
        size_box.append(self._cache_size_lbl)
        sub_hint = Gtk.Label(label="Nettoyage automatique désactivé"); sub_hint.add_css_class("settings-hint")
        size_box.append(sub_hint)
        cache_row.append(size_box)
        
        clr_btn = Gtk.Button(label="Vider le cache"); clr_btn.add_css_class("danger")
        clr_btn.connect("clicked", self._clear_cache)
        cache_row.append(clr_btn)
        cache_card.append(cache_row)
        
        content.append(cache_card)

        # ── A propos ──────────────────────────────────────────
        about_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        about_card.add_css_class("settings-card")
        
        t = Gtk.Label(label="ᚦ À propos"); t.add_css_class("settings-group-title"); t.set_halign(Gtk.Align.START)
        about_card.append(t)
        about = Gtk.Label()
        about.set_markup(
            f'Valheim Mod Manager <span foreground="#5a4f3d">v{APP_VERSION}</span>\n\n'
            'Une application artisanale pour les guerriers du Nord.\n'
            'Mods fournis par Thunderstore.io\n'
            'Source sous licence MIT'
        )
        about.set_halign(Gtk.Align.START); about.set_wrap(True)
        about_card.append(about)
        
        content.append(about_card)

        scroll.set_child(center_box)
        self.append(scroll)


    def _get_cache_size(self) -> str:
        cache_root = CONFIG_DIR / "cache"
        return fmt_size(cache_root) if cache_root.exists() else "0 Ko"

    def _refresh_bepinex_status(self):
        if self.manager.has_bepinex:
            self._bep_lbl.set_markup(
                '<span foreground="#80c840">\u2726 BepInEx détecté — prêt pour les mods !</span>'
            )
        else:
            self._bep_lbl.set_markup(
                '<span foreground="#d06040">'
                '\u26a0 BepInEx non détecté dans ce dossier.\n'
                'Installez BepInExPack_Valheim depuis Thunderstore avant d\'utiliser des mods.'
                '</span>'
            )

    def _browse(self, _):
        dlg = Gtk.FileChooserDialog(
            title="Choisir le dossier Valheim",
            transient_for=self.get_root(),
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            modal=True,
        )
        dlg.add_button("Annuler",      Gtk.ResponseType.CANCEL)
        dlg.add_button("Selectionner", Gtk.ResponseType.ACCEPT)
        dlg.connect("response", self._on_browse_response)
        dlg.present()

    def _on_browse_response(self, dlg, response):
        if response == Gtk.ResponseType.ACCEPT:
            self._path_entry.set_text(dlg.get_file().get_path())
        dlg.destroy()

    def _save(self, _):
        self.manager.set_valheim_path(self._path_entry.get_text().strip())
        self._refresh_bepinex_status()
        self.show_toast("\u2726 Parametres sauvegardes !", "success")

    def _clear_cache(self, _):
        try:
            if ICON_CACHE_DIR.exists():
                shutil.rmtree(ICON_CACHE_DIR); ICON_CACHE_DIR.mkdir(parents=True)
            if DOWNLOAD_DIR.exists():
                shutil.rmtree(DOWNLOAD_DIR); DOWNLOAD_DIR.mkdir(parents=True)
            self._cache_size_lbl.set_text("0 Ko")
            self.show_toast("Cache vide avec succes", "success")
        except Exception as e:
            logger.error(f"Erreur lors de la vidange du cache: {e}")
            self.show_toast(f"Erreur : {e}", "error")

    def _copy_to_clipboard(self, text):
        display = Gdk.Display.get_default()
        clipboard = display.get_clipboard()
        clipboard.set(text)
        self.show_toast("Commande copiée !", "success")
