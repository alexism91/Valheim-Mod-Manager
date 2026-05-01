import gi
from gi.repository import Gtk, GLib
from vmm.constants import SEARCH_DEBOUNCE, BATCH_SIZE
from vmm.utils import fmt_number
from vmm.ui.cards import ModCard

class BrowsePage(Gtk.Box):
    __gtype_name__ = "BrowsePage"

    def __init__(self, manager, show_toast, on_refresh_installed, on_open_mod=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.manager               = manager
        self.show_toast            = show_toast
        self.on_refresh_installed  = on_refresh_installed
        self.all_packages          = []
        self.display_packages      = []
        self.current_category      = "Tous"
        self.search_query          = ""
        self.sort_key              = 0
        self.display_offset        = 0
        self._search_tid           = None
        self._cat_counts           = {}
        self._cat_container        = None
        self._on_open_mod_callback = on_open_mod
        self._build()

    def _build(self):
        # ── Header ──────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hdr.add_css_class("main-header")
        
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        t = Gtk.Label()
        t.set_markup(
            '<span foreground="#d4a04c" font_size="small">ᛒ ᚱ ᛟ</span>'
            '  <span font_weight="bold">Bibliothèque des Mods</span>  '
            '<span foreground="#d4a04c" font_size="small">ᛟ ᚱ ᛒ</span>'
        )
        t.add_css_class("main-title")
        t.set_halign(Gtk.Align.START)
        titles.append(t)
        
        s = Gtk.Label(label="Explorez les artefacts de Thunderstore")
        s.add_css_class("main-sub")
        s.set_halign(Gtk.Align.START)
        titles.append(s)
        
        hdr.append(titles)
        
        self._count_lbl = Gtk.Label()
        self._count_lbl.add_css_class("results-count")
        self._count_lbl.set_hexpand(True); self._count_lbl.set_halign(Gtk.Align.END)
        hdr.append(self._count_lbl)
        
        self.append(hdr)
        
        # Rune Divider
        div = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        div.set_halign(Gtk.Align.CENTER)
        div.set_margin_top(-10) # Overlap slightly with header shadow
        rune_div = Gtk.Label(label="\u16ac \u16c8 \u16d2 \u16ac")
        rune_div.add_css_class("rune-divider")
        div.append(rune_div)
        self.append(div)

        # ── Body ────────────────────────────────────────────

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        body.set_vexpand(True)
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        toolbar.set_margin_top(18); toolbar.set_margin_bottom(18)
        toolbar.set_margin_start(28); toolbar.set_margin_end(28)

        # Search
        self._search = Gtk.SearchEntry()
        self._search.set_placeholder_text("Chercher un mod, un auteur, un mot-clé…")
        self._search.set_size_request(400, -1)
        self._search.connect("search-changed", self._on_search_changed)
        toolbar.append(self._search)

        # Sort
        sort_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sort_box.add_css_class("sort-pill")
        l = Gtk.Label(label="\u21c5  Tri"); l.add_css_class("label")
        self._sort_drop = Gtk.DropDown.new_from_strings([
            "Popularité", "Récents", "Mieux notés", "A-Z"
        ])

        self._sort_drop.connect("notify::selected", self._on_sort_changed)
        sort_box.append(l); sort_box.append(self._sort_drop)
        toolbar.append(sort_box)
        
        body.append(toolbar)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_vexpand(True)
        
        # Spinner
        spin_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        spin_box.set_halign(Gtk.Align.CENTER); spin_box.set_valign(Gtk.Align.CENTER)
        self._spinner = Gtk.Spinner(); self._spinner.set_size_request(64, 64)
        spin_box.append(self._spinner)
        spin_lbl = Gtk.Label(label="Rassemblement des corbeaux d'Odin...")
        spin_lbl.add_css_class("empty-body")
        spin_box.append(spin_lbl)
        self._stack.add_named(spin_box, "spinner")

        # Scroll / List
        grid_scroll = Gtk.ScrolledWindow()
        grid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid_scroll.set_vexpand(True)
        vadj = grid_scroll.get_vadjustment()
        vadj.connect("value-changed", self._on_scroll)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        container.set_margin_start(28); container.set_margin_end(28); container.set_margin_bottom(28)
        
        self._list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.append(self._list_box)

        self._load_more_btn = Gtk.Button(label="Charger plus d'artefacts...")
        self._load_more_btn.add_css_class("ghost")
        self._load_more_btn.set_margin_top(20)
        self._load_more_btn.connect("clicked", lambda _: self._fill_batch())
        container.append(self._load_more_btn)

        grid_scroll.set_child(container)
        self._stack.add_named(grid_scroll, "list")
        
        body.append(self._stack)
        self.append(body)

    def populate_sidebar_cats(self, container: Gtk.Box):
        self._cat_container = container
        self._refresh_cat_list()

    def _refresh_cat_list(self):
        if not self._cat_container: return
        child = self._cat_container.get_first_child()
        while child:
            nxt = child.get_next_sibling(); self._cat_container.remove(child); child = nxt
        ordered = ["Tous"] + sorted(self._cat_counts, key=lambda c: -self._cat_counts[c])
        for cat in ordered:
            btn = Gtk.Button(); btn.add_css_class("sb-nav-item"); btn.add_css_class("cat-item")
            if cat == self.current_category: btn.add_css_class("active")
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            rune = Gtk.Label(label="ᚦ"); rune.add_css_class("rune")
            label = Gtk.Label(label=cat); label.set_hexpand(True); label.set_halign(Gtk.Align.START)
            count_val = len(self.all_packages) if cat == "Tous" else self._cat_counts.get(cat, 0)
            count = Gtk.Label(label=fmt_number(count_val)); count.add_css_class("nav-count")
            box.append(rune); box.append(label); box.append(count)
            btn.set_child(box)
            btn.connect("clicked", lambda _, c=cat: self._select_cat(c))
            self._cat_container.append(btn)

    def _select_cat(self, cat):
        self.current_category = cat
        self._refresh_cat_list(); self._apply_filters()

    def start_load(self):
        self.all_packages.clear(); self.display_packages.clear(); self._clear_list()
        self._stack.set_visible_child_name("spinner"); self._spinner.start()
        self.manager.fetch_packages_async(self._on_page, self._on_all_done, self._on_error)

    def _on_page(self, results: list):
        self.all_packages.extend(results)
        if len(self.all_packages) == len(results):
            self._populate_cat_counts(); self._apply_filters()
            self._spinner.stop(); self._stack.set_visible_child_name("list")
            self.on_refresh_installed()

    def _on_all_done(self, total: int):
        self._populate_cat_counts(); self._apply_filters()
        self.on_refresh_installed()

    def _on_error(self, err: str):
        self._spinner.stop(); self._stack.set_visible_child_name("list")
        self.show_toast(f"Erreur runique : {err}", "error")

    def _populate_cat_counts(self):
        self._cat_counts = {}
        for pkg in self.all_packages:
            if not pkg.get("is_deprecated"):
                for cat in pkg.get("categories", []):
                    self._cat_counts[cat] = self._cat_counts.get(cat, 0) + 1
        self._refresh_cat_list()

    def _apply_filters(self):
        pkgs = self.all_packages
        if self.current_category != "Tous":
            pkgs = [p for p in pkgs if self.current_category in p.get("categories", [])]
        pkgs = [p for p in pkgs if not p.get("is_deprecated", False)]
        if q := self.search_query:
            def _matches(p):
                latest_desc = (p.get("versions") or [{}])[0].get("description") or ""
                return (
                    q in p.get("name", "").lower()
                    or q in p.get("owner", "").lower()
                    or q in latest_desc.lower()
                    or any(q in cat.lower() for cat in p.get("categories", []))
                )
            pkgs = [p for p in pkgs if _matches(p)]
        if self.sort_key == 0:
            pkgs.sort(key=lambda p: p.get("rating_score", 0), reverse=True)
        elif self.sort_key == 1:
            pkgs.sort(key=lambda p: p.get("date_updated", ""), reverse=True)
        elif self.sort_key == 2:
            pkgs.sort(key=lambda p: sum(v.get("downloads", 0) for v in p.get("versions", [])), reverse=True)
        elif self.sort_key == 3:
            pkgs.sort(key=lambda p: p.get("name", "").lower())
        self.display_packages = pkgs
        self.display_offset   = 0
        self._count_lbl.set_markup(f"<b>{len(pkgs)}</b> / {fmt_number(len(self.all_packages))} mods")
        self._clear_list(); self._fill_batch()

    def _clear_list(self):
        child = self._list_box.get_first_child()
        while child:
            nxt = child.get_next_sibling(); self._list_box.remove(child); child = nxt

    def _fill_batch(self):
        batch = self.display_packages[self.display_offset: self.display_offset + BATCH_SIZE]
        for pkg in batch:
            card = ModCard(pkg, self.manager, self._on_card_clicked, self.show_toast)
            self._list_box.append(card)
        self.display_offset += len(batch)
        self._load_more_btn.set_visible(self.display_offset < len(self.display_packages))

    def _on_scroll(self, adj):
        if adj.get_value() >= adj.get_upper() - adj.get_page_size() - 400:
            if self.display_offset < len(self.display_packages): self._fill_batch()

    def _on_card_clicked(self, pkg: dict):
        if self._on_open_mod_callback: self._on_open_mod_callback(pkg)

    def _on_search_changed(self, entry):
        if self._search_tid: GLib.source_remove(self._search_tid)
        self._search_tid = GLib.timeout_add(SEARCH_DEBOUNCE, self._do_search)

    def _do_search(self):
        self.search_query = self._search.get_text().strip().lower()
        self._apply_filters(); self._search_tid = None
        return False

    def focus_search(self): self._search.grab_focus()
    def _on_sort_changed(self, dd, _):
        self.sort_key = dd.get_selected(); self._apply_filters()
    def refresh_all(self): self._apply_filters()
    def escape_pressed(self):
        if self.search_query: self._search.set_text(""); return True
        return False
