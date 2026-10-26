#!/usr/bin/env bash
# =============================================================================
#  Onze — uninstaller
#
#  Usage:  ./uninstall.sh [options]
#    -r, --no-restore       Do not restore the backup; apply the default Breeze theme
#    -k, --keep-icons       Keep the installed icon theme (Onze Icons or Win11)
#    -y, --yes              Do not ask for confirmation
#    -h, --help             Show this help
# =============================================================================
set -Eeuo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/onze-theme"
BACKUP="$STATE/backup"
MANIFEST="$STATE/manifest"

RESTORE=1
KEEP_ICONS=0
ASK=1

if [[ -t 1 ]]; then
    B=$'\e[1m'; BL=$'\e[38;5;39m'; GR=$'\e[32m'; YE=$'\e[33m'; RD=$'\e[31m'; N=$'\e[0m'
else
    B=""; BL=""; GR=""; YE=""; RD=""; N=""
fi
info() { printf '%s==>%s %s\n' "$BL$B" "$N" "$*"; }
ok()   { printf '%s ✓%s %s\n' "$GR" "$N" "$*"; }
warn() { printf '%s !%s %s\n' "$YE" "$N" "$*" >&2; }
die()  { printf '%s ✗ %s%s\n' "$RD" "$*" "$N" >&2; exit 1; }
trap 'die "Failed at line $LINENO (command: $BASH_COMMAND)"' ERR

usage() { sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0; }

# Portuguese option names from earlier versions are still accepted as aliases.
while [[ $# -gt 0 ]]; do
    case "$1" in
        -r|--no-restore|--sem-restaurar) RESTORE=0 ;;
        -k|--keep-icons|--manter-icones) KEEP_ICONS=1 ;;
        -y|--yes|--sim) ASK=0 ;;
        -h|--help|--ajuda) usage ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
    shift
done

has() { command -v "$1" >/dev/null 2>&1; }
dbus_call() { dbus-send --session --type=method_call "$@" >/dev/null 2>&1 || true; }

if [[ $EUID -eq 0 && -z "${ONZE_ALLOW_ROOT:-}${ONZE_PERMITIR_ROOT:-}" ]]; then
    die "Do not run as root."
fi
[[ -f "$MANIFEST" ]] || die "Onze does not seem to be installed (manifest not found in $STATE)."

IN_SESSION=0
if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] && pgrep -u "$USER" -x plasmashell >/dev/null 2>&1; then
    IN_SESSION=1
fi
[[ -d "$BACKUP" ]] || RESTORE=0

cat <<EOF

  ${B}Uninstall Onze${N}
  Restore previous settings: $([[ $RESTORE -eq 1 ]] && echo "yes (backup from $(cat "$BACKUP/.data" 2>/dev/null || echo '?'))" || echo "no — Breeze will be applied")
  Remove the installed icon theme: $([[ $KEEP_ICONS -eq 1 ]] && echo "no" || echo "yes")

EOF
if [[ $ASK -eq 1 ]]; then
    read -r -p "Continue? [Y/n] " r
    [[ -z "$r" || "$r" =~ ^[YySs] ]] || { echo "Cancelled."; exit 0; }
fi

read_key() {  # read_key <file> <group> <key> — reads a key from a (restored) config file
    if has kreadconfig6; then
        kreadconfig6 --file "$1" --group "$2" --key "$3" 2>/dev/null || true
    fi
}

# --- 1. restore, or go back to Breeze ------------------------------------------------
if [[ $RESTORE -eq 1 ]]; then
    info "Restoring saved settings"
    for f in "$BACKUP"/*; do
        [[ -f "$f" ]] || continue
        cp -p "$f" "$CONF/$(basename "$f")"
    done
    # files that did not exist before the installation go back to not existing
    # (only files this backup covered; older backups did not include breezerc)
    if [[ -f "$BACKUP/.checked" ]]; then
        mapfile -t checked < "$BACKUP/.checked"
    else
        checked=(kdeglobals kwinrc plasmarc kcminputrc ksplashrc kscreenlockerrc
                 plasma-org.kde.plasma.desktop-appletsrc plasmashellrc)
    fi
    for f in "${checked[@]}"; do
        [[ -f "$BACKUP/$f" ]] || rm -f "$CONF/$f"
    done
    # backups made before breezerc was covered: just undo our scrollbar setting
    if [[ ! " ${checked[*]} " == *" breezerc "* ]] && has kwriteconfig6; then
        kwriteconfig6 --file breezerc --group Style --key ScrollBarSubLineButtons --delete
        kwriteconfig6 --file breezerc --group Style --key ScrollBarAddLineButtons --delete
    fi
    ok "Configuration files restored"

    if [[ $IN_SESSION -eq 1 ]]; then
        SCHEME="$(read_key kdeglobals General ColorScheme)"
        PSTYLE="$(read_key plasmarc Theme name)"
        CUR="$(read_key kcminputrc Mouse cursorTheme)"
        ICO="$(read_key kdeglobals Icons Theme)"
        has plasma-apply-colorscheme  && plasma-apply-colorscheme "${SCHEME:-BreezeLight}" >/dev/null 2>&1 || true
        has plasma-apply-desktoptheme && plasma-apply-desktoptheme "${PSTYLE:-default}" >/dev/null 2>&1 || true
        has plasma-apply-cursortheme  && plasma-apply-cursortheme "${CUR:-breeze_cursors}" >/dev/null 2>&1 || true
        CHANGEICONS="$(ls /usr/lib/*/libexec/plasma-changeicons /usr/libexec/plasma-changeicons 2>/dev/null | head -n1 || true)"
        [[ -n "$CHANGEICONS" ]] && { "$CHANGEICONS" "${ICO:-breeze}" >/dev/null 2>&1 || true; }
        dbus_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure
        info "Restarting the desktop to reload the panels"
        if systemctl --user is-active --quiet plasma-plasmashell.service 2>/dev/null; then
            systemctl --user restart plasma-plasmashell.service || true
        elif has kquitapp6 && has kstart; then
            kquitapp6 plasmashell >/dev/null 2>&1 || true
            sleep 1
            kstart plasmashell >/dev/null 2>&1 || true
        else
            warn "Log out and back in to reload the panels."
        fi
    fi
else
    if [[ $IN_SESSION -eq 1 ]] && has plasma-apply-lookandfeel; then
        info "Applying the Breeze global theme"
        plasma-apply-lookandfeel -a org.kde.breeze.desktop --resetLayout >/dev/null || true
        has plasma-apply-cursortheme && plasma-apply-cursortheme breeze_cursors >/dev/null 2>&1 || true
        if has kwriteconfig6; then
            kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
            kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme Breeze
            kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSizeAuto true
            kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "IAX"
            kwriteconfig6 --file breezerc --group Style --key ScrollBarSubLineButtons --delete
            kwriteconfig6 --file breezerc --group Style --key ScrollBarAddLineButtons --delete
        fi
        dbus_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure
        ok "Breeze applied"
    else
        warn "No Plasma session detected: pick another theme in System Settings after logging in."
    fi
fi

# --- 2. remove installed files -------------------------------------------------------
info "Removing Onze files"
removed=0
while IFS= read -r target; do
    [[ -n "$target" ]] || continue
    # safety: only remove paths inside the user's data folder
    case "$target" in
        "$DATA"/*) ;;
        *) warn "Skipping path outside $DATA: $target"; continue ;;
    esac
    if [[ $KEEP_ICONS -eq 1 && ( "$target" == "$DATA/icons/Win11"* || "$target" == "$DATA/icons/OnzeIcons"* ) ]]; then
        continue
    fi
    if [[ -e "$target" ]]; then
        rm -rf -- "$target"
        removed=$((removed + 1))
    fi
done < "$MANIFEST"
ok "$removed items removed"
# remove folders left empty (e.g. the one holding the Start button icon)
for d in "$DATA/icons/hicolor/scalable/apps" "$DATA/icons/hicolor/scalable" "$DATA/icons/hicolor"; do
    rmdir -- "$d" 2>/dev/null || true
done

# desktop shortcuts (Home, Trash): only files created by Onze
if [[ -f "$STATE/desktop-shortcuts" ]]; then
    while IFS= read -r f; do
        [[ -n "$f" && -f "$f" ]] || continue
        if grep -q '^X-Onze-Shortcut=true' "$f" 2>/dev/null; then
            rm -f -- "$f"
        fi
    done < "$STATE/desktop-shortcuts"
    ok "Desktop shortcuts removed"
fi

rm -rf -- "${STATE:?}"
ok "Onze backup and records deleted"

echo
echo "${GR}${B}Onze uninstalled.${N} Log out and back in to finish (cursor and splash screen)."
echo
