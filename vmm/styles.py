CSS = """
/* === VALHEIM MOD MANAGER — Design System (Mockup V2.1) === */

@define-color bg_0 #0b0805;
@define-color bg_1 #14100a;
@define-color bg_2 #1c1610;
@define-color bg_3 #261e15;
@define-color bg_card #15110b;
@define-color bg_card_hover #1d1810;

@define-color line_1 rgba(139, 90, 43, 0.18);
@define-color line_2 rgba(139, 90, 43, 0.32);
@define-color line_3 rgba(212, 160, 76, 0.45);

@define-color gold #d4a04c;
@define-color gold_hi #f0c878;
@define-color gold_dim #8a6a30;
@define-color bronze #8b5a2b;
@define-color bronze_dim #5a3a1e;

@define-color ink_0 #f4e9d0;
@define-color ink_1 #c9b896;
@define-color ink_2 #8a7a5e;
@define-color ink_3 #5a4f3d;

@define-color warn #d49a3c;
@define-color danger #a8331f;
@define-color success #6b8a3a;

/* Overrides Adwaita */
@define-color accent_color @gold;
@define-color accent_bg_color #2a1e0d;
@define-color window_bg_color @bg_0;
@define-color window_fg_color @ink_1;
@define-color view_bg_color @bg_0;
@define-color view_fg_color @ink_1;
@define-color headerbar_bg_color #1a140d;
@define-color headerbar_fg_color @gold;
@define-color card_bg_color @bg_card;
@define-color dialog_bg_color @bg_1;
@define-color popover_bg_color @bg_1;

/* ─── Base ───────────────────────────────────────────────────── */
* {
    font-family: 'Nunito', 'Cantarell', sans-serif;
    -gtk-icon-style: symbolic;
}

.display-font, .main-title, .sb-brand-title, .detail-name, .rune {
    font-family: 'Cinzel', 'DejaVu Serif', serif;
}

window, .background {
    background-color: @bg_0;
    color: @ink_1;
}

/* ─── Header Bar ─────────────────────────────────────────────── */
headerbar {
    background: linear-gradient(180deg, #1a140d 0%, #110c07 100%);
    border-bottom: 1px solid @line_2;
    padding: 0 12px;
    min-height: 38px;
}
headerbar label.title {
    font-family: 'Cinzel', 'DejaVu Serif', serif;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.18em;
    color: @gold;
    text-transform: uppercase;
}

/* ─── Sidebar ─────────────────────────────────────────────── */
.sidebar {
    background: linear-gradient(180deg, @bg_1 0%, @bg_0 100%);
    border-right: 1px solid @line_2;
    padding: 14px 0;
}
.sb-brand-title { font-size: 13px; letter-spacing: 0.14em; color: @gold; text-transform: uppercase; font-weight: 600; }
.sb-brand-sub   { font-size: 10px; color: @ink_2; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 500; }

.sb-nav-item {
    padding: 9px 16px;
    color: @ink_1;
    font-size: 12.5px;
    font-weight: 500;
    border-radius: 4px;
    margin: 2px 10px;
}
.sb-nav-item:hover { background-color: @bg_2; color: @ink_0; }
.sb-nav-item.active {
    background: linear-gradient(90deg, rgba(212, 160, 76, 0.12), rgba(212, 160, 76, 0.02));
    border: 1px solid @line_2;
    color: @gold;
}
.sb-nav-item .rune { font-size: 11px; margin-right: 12px; color: @ink_3; }
.sb-nav-item.active .rune { color: @gold; }

.sb-stats     { margin: 0 14px 18px; padding: 14px 10px; background: @bg_2; border: 1px solid @line_1; border-radius: 4px; }
.sb-stat-val  { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 18px; color: @gold; font-weight: 500; }
.sb-stat-lbl  { font-size: 9px; color: @ink_2; letter-spacing: 0.14em; text-transform: uppercase; margin-top: 2px; }

.sb-section-label { font-family: 'Cinzel', 'DejaVu Serif', serif; font-size: 10px; letter-spacing: 0.18em; color: @ink_2; text-transform: uppercase; padding: 0 22px; margin: 4px 0 8px; }

.sb-footer { padding: 12px 18px; }
.dot       { color: @success; font-size: 16px; }

/* ─── Main Content ───────────────────────────────────────────── */
.main-header { padding: 24px 32px 16px; background: linear-gradient(180deg, @bg_1 0%, transparent 100%); border-bottom: 1px solid @line_1; }
.main-title  { font-size: 24px; font-weight: 500; color: @ink_0; letter-spacing: 0.06em; }
.main-sub    { font-size: 11px; color: @ink_2; letter-spacing: 0.16em; text-transform: uppercase; margin-top: 4px; }

.rune-divider { font-family: 'Cinzel', 'DejaVu Serif', serif; color: rgba(212, 160, 76, 0.25); font-size: 14px; letter-spacing: 0.4em; margin: 4px 0 12px; }
.rune-deco    { font-size: 12px; color: rgba(212, 160, 76, 0.25); }

/* ─── Browse toolbar ─────────────────────────────────────────── */
.sort-pill       { background: @bg_2; border: 1px solid @line_1; border-radius: 4px; padding: 4px 10px; }
.sort-pill .label { font-size: 11px; color: @ink_2; }
.results-count   { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 11px; color: @ink_2; }

/* ─── Cards ─────────────────────────────────────────────────── */
.mod-card       { background-color: @bg_card; border: 1px solid @line_1; border-radius: 4px; padding: 14px 16px; }
.mod-card:hover { background-color: @bg_card_hover; border-color: @line_2; }
.mod-card.is-installed { border-color: rgba(107, 138, 58, 0.35); }
.mod-card.has-update   { border-color: rgba(212, 160, 76, 0.45); }

.mod-name    { font-size: 14px; font-weight: 600; color: @ink_0; letter-spacing: 0.02em; }
.mod-author  { font-size: 11px; color: @ink_2; }
.mod-desc    { font-size: 12px; color: @ink_1; line-height: 1.5; }
.mod-version { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 10px; color: @ink_3; }
.mod-stat    { font-size: 11px; color: @ink_2; }
.mod-icon-frame { background: linear-gradient(135deg, @bronze_dim, @bg_3); border: 1px solid @line_2; border-radius: 4px; color: @gold; font-size: 20px; }

.tag      { padding: 2px 10px; background: rgba(139, 90, 43, 0.12); border: 1px solid @line_2; border-radius: 12px; font-size: 10px; color: @ink_1; font-weight: 600; }
.tag.gold { color: @gold; border-color: @gold_dim; background: rgba(212, 160, 76, 0.08); }

/* ─── Empty state ────────────────────────────────────────────── */
.empty-icon  { font-size: 48px; color: rgba(212, 160, 76, 0.28); margin-bottom: 8px; }
.empty-title { font-family: 'Cinzel', 'DejaVu Serif', serif; font-size: 16px; color: @ink_2; letter-spacing: 0.1em; }
.empty-body  { font-size: 12px; color: @ink_3; }

/* ─── Toast ──────────────────────────────────────────────────── */
.toast-box     { background: @bg_2; border: 1px solid @line_2; border-radius: 6px; padding: 10px 18px; min-width: 280px; }
.toast-icon    { font-size: 16px; color: @gold; }
.toast-success { border-color: rgba(107, 138, 58, 0.5); background: rgba(107, 138, 58, 0.1); }
.toast-error   { border-color: rgba(168, 51, 31, 0.5); background: rgba(168, 51, 31, 0.12); }
.toast-warning { border-color: rgba(212, 154, 60, 0.4); background: rgba(212, 154, 60, 0.08); }

/* ─── Detail Page ────────────────────────────────────────────── */
.detail-hero    { padding: 32px; background: linear-gradient(180deg, @bg_2 0%, @bg_1 100%); border: 1px solid @line_2; border-radius: 6px; }
.detail-name    { font-size: 32px; font-weight: 500; color: @ink_0; letter-spacing: 0.02em; }
.detail-author  { font-size: 14px; color: @ink_2; }
.detail-icon    { background: linear-gradient(135deg, @bronze, @bg_3); border: 1px solid @gold_dim; border-radius: 4px; color: @gold; font-size: 48px; }
.detail-stat-val { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 20px; color: @gold; }
.detail-stat-lbl { font-size: 10px; color: @ink_2; letter-spacing: 0.12em; text-transform: uppercase; }
.detail-section { background: @bg_card; border: 1px solid @line_1; border-radius: 4px; padding: 18px 20px; }
.detail-desc    { font-size: 14px; line-height: 1.7; color: @ink_1; }

.info-card      { background: @bg_card; border: 1px solid @line_1; border-radius: 4px; padding: 20px; }
.section-label  { font-family: 'Cinzel', 'DejaVu Serif', serif; font-size: 11px; color: @gold; letter-spacing: 0.18em; text-transform: uppercase; }

/* ─── Dependencies ───────────────────────────────────────────── */
.dep-row  { background: @bg_2; border: 1px solid @line_1; border-radius: 4px; padding: 10px 12px; }
.dep-icon { background: @bg_3; border: 1px solid @line_2; border-radius: 4px; color: @gold; font-size: 14px; }
.dep-name { font-size: 13px; color: @ink_0; font-weight: 500; }
.dep-meta { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 10px; color: @ink_3; }
.dep-status          { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
.dep-status.installed { color: #80c840; }
.dep-status.required  { color: @warn; }

/* ─── Changelog ──────────────────────────────────────────────── */
.changelog-item { padding: 12px 0; border-bottom: 1px solid @line_1; }
.ver-tag  { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 12px; color: @gold; background: rgba(212, 160, 76, 0.08); border: 1px solid @gold_dim; padding: 2px 8px; border-radius: 4px; }
.ver-date { font-size: 11px; color: @ink_3; }

/* ─── Buttons ────────────────────────────────────────────────── */
button.primary { background: linear-gradient(180deg, #a87a32 0%, #7a5722 100%); border: 1px solid @gold_dim; color: #1a1208; font-weight: 700; border-radius: 4px; }
button.primary:hover { background: linear-gradient(180deg, #c89a48 0%, #a07535 100%); border-color: @gold; }
button.ghost       { background: transparent; border: 1px solid transparent; color: @ink_2; }
button.ghost:hover { background: @bg_2; color: @ink_0; }
button.danger       { background: linear-gradient(180deg, #8a2518 0%, #5a1a10 100%); border: 1px solid rgba(168, 51, 31, 0.6); color: #f4c4b4; font-weight: 600; border-radius: 4px; }
button.danger:hover { background: linear-gradient(180deg, #a83020 0%, #7a2518 100%); border-color: rgba(200, 70, 50, 0.8); }
button.sm { padding: 5px 12px; font-size: 11px; }

/* ─── Warning Bar ────────────────────────────────────────────── */
.warn-bar { background: linear-gradient(180deg, rgba(168, 51, 31, 0.12), rgba(168, 51, 31, 0.06)); border-bottom: 1px solid rgba(168, 51, 31, 0.3); padding: 8px 16px; color: @ink_1; font-size: 12.5px; }

/* ─── Profiles ───────────────────────────────────────────────── */
.profiles-bar  { padding: 12px 0; border-bottom: 1px solid @line_1; margin-bottom: 16px; }
.profile-chip  { padding: 6px 14px; border: 1px solid @line_2; background: @bg_2; color: @ink_1; border-radius: 14px; font-size: 11px; margin-right: 8px; }
.profile-chip.active { background: rgba(212, 160, 76, 0.1); border-color: @gold_dim; color: @gold; }

/* ─── Settings ───────────────────────────────────────────────── */
.settings-card        { background: alpha(black, 0.15); border: 1px solid @line_1; border-radius: 6px; padding: 24px; margin-bottom: 20px; }
.settings-group-title { font-family: 'Cinzel', 'DejaVu Serif', serif; font-size: 13px; color: @gold; letter-spacing: 0.18em; }
.settings-hint        { font-size: 11px; color: @ink_2; font-style: italic; }

/* ─── Misc ───────────────────────────────────────────────────── */
.nav-count { font-family: 'JetBrains Mono', 'Hack', 'DejaVu Sans Mono', monospace; font-size: 10px; color: @ink_3; }
.active .nav-count { color: @gold_dim; }

/* cat-item : identique aux nav items, pas de style supplémentaire requis */
.cat-item { font-size: 11.5px; }

/* win-frame: fenêtre principale */
.win-frame { }
"""
