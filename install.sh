#!/usr/bin/env bash
# =============================================================================
#  Onze — Windows 11 style global theme for KDE Plasma 6 (Kubuntu 26.04)
#  Installer (per user, no sudo required)
#
#  Usage:  ./install.sh [options]
#    -l, --light            Apply the light variant
#    -d, --dark             Apply the dark variant
#                           (without -l/-d, the installer asks which one you want)
#    -L, --lang LANG        Language of the theme's widgets: "en" (English, default)
#                           or "pt-BR" (Português do Brasil); asked if not given
#    -s, --start POS        Start button and apps position: "center" (Windows 11)
#                           or "left" (Windows 10); asked if not given
#    -k, --keep-layout      Do not recreate the taskbar (keeps your panels)
#    -H, --height N         Taskbar height in pixels (default: 40)
#    -D, --desktop-icons N  Desktop icon size in pixels: 22, 32, 48, 64 or 96
#                           (default: 48, one level below Plasma's 64)
#    -i, --no-icons         Do not install the icon theme (uses Breeze)
#    -N, --no-desktop-shortcuts
#                           Do not add the Home folder and Trash icons to the desktop
#    -A, --no-scroll-arrows Do not show the arrow buttons at the ends of
#                           scrollbars (shown by default, as in Windows 11)
#    -o, --offline          Never download anything; use only the copy in vendor/
#    -n, --no-apply         Only copy the files; apply later in
#                           System Settings > Global Theme
#    -y, --yes              Do not ask for confirmation
#    -h, --help             Show this help
# =============================================================================
set -Eeuo pipefail

VERSION="1.4"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$DIR/src"

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/onze-theme"
BACKUP="$STATE/backup"
MANIFEST="$STATE/manifest"

ICON_REPO="yeyushengfan258/Win11-icon-theme"
ICON_LOCAL="$DIR/vendor/Win11-icon-theme"
ONZE_ICONS="$SRC/icons"

# Edition of this package: "original" (Onze Icons, 100% original artwork)
# or "win11icons" (Win11 icon theme by yeyushengfan258). Set by tools/build-packages.sh.
EDITION="$(tr -d '[:space:]' < "$DIR/EDITION" 2>/dev/null || true)"
if [[ "$EDITION" != original && "$EDITION" != win11icons ]]; then
    if [[ -d "$DIR/vendor" ]]; then EDITION="win11icons"; else EDITION="original"; fi
fi
ICON_ARCHIVE="$DIR/vendor/Win11-icon-theme-main.tar.gz"

VARIANT=""          # light | dark
RESET_LAYOUT=1
INSTALL_ICONS=1
APPLY=1
ASK=1
OFFLINE=0
HEIGHT=40
DESKTOP_ICONS=48
SCROLL_ARROWS=1
DESKTOP_SHORTCUTS=1
START=""            # center | left
LANG_UI=""          # en | pt-BR

# --- output ----------------------------------------------------------------------
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

usage() { sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0; }

# Portuguese option names from earlier versions are still accepted as aliases.
while [[ $# -gt 0 ]]; do
    case "$1" in
        -l|--light|-c|--claro) VARIANT="light" ;;
        -d|--dark|-e|--escuro) VARIANT="dark" ;;
        -k|--keep-layout|-m|--manter-layout) RESET_LAYOUT=0 ;;
        -L|--lang)
            [[ $# -ge 2 ]] || die "$1 needs a value: en or pt-BR"
            LANG_UI="$2"; shift ;;
        --lang=*) LANG_UI="${1#*=}" ;;
        -s|--start)
            [[ $# -ge 2 ]] || die "$1 needs a value: center or left"
            START="$2"; shift ;;
        --start=*) START="${1#*=}" ;;
        -H|--height|-a|--altura)
            [[ $# -ge 2 ]] || die "$1 needs a number (e.g. --height 40)"
            HEIGHT="$2"; shift ;;
        --height=*|--altura=*) HEIGHT="${1#*=}" ;;
        -D|--desktop-icons)
            [[ $# -ge 2 ]] || die "$1 needs a size in pixels (22, 32, 48, 64 or 96)"
            DESKTOP_ICONS="$2"; shift ;;
        --desktop-icons=*) DESKTOP_ICONS="${1#*=}" ;;
        -i|--no-icons|--sem-icones) INSTALL_ICONS=0 ;;
        -A|--no-scroll-arrows) SCROLL_ARROWS=0 ;;
        -N|--no-desktop-shortcuts) DESKTOP_SHORTCUTS=0 ;;
        -n|--no-apply|--nao-aplicar) APPLY=0 ;;
        -o|--offline) OFFLINE=1 ;;
        -y|--yes|--sim) ASK=0 ;;
        -h|--help|--ajuda) usage ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
    shift
done

case "${LANG_UI,,}" in
    "") ;;
    en|en_us|en-us|english|1) LANG_UI="en" ;;
    pt|pt-br|pt_br|portugues|português|2) LANG_UI="pt-BR" ;;
    *) die "Invalid --lang value: $LANG_UI (use en or pt-BR)" ;;
esac

case "${START,,}" in
    "") ;;
    center|centre|c|middle|meio|centro) START="center" ;;
    left|l|esquerda|e) START="left" ;;
    *) die "Invalid --start value: $START (use center or left)" ;;
esac

case "$DESKTOP_ICONS" in
    22) ICON_LEVEL=0 ;; 32) ICON_LEVEL=1 ;; 48) ICON_LEVEL=2 ;; 64) ICON_LEVEL=3 ;; 96) ICON_LEVEL=4 ;;
    *) die "Invalid --desktop-icons value: $DESKTOP_ICONS (use 22, 32, 48, 64 or 96)" ;;
esac

[[ "$HEIGHT" =~ ^[0-9]+$ ]] && (( HEIGHT >= 24 && HEIGHT <= 96 )) ||
    die "Invalid height: $HEIGHT (use a number between 24 and 96)"

has() { command -v "$1" >/dev/null 2>&1; }
dark_suffix() { if [[ "$1" == dark ]]; then echo "-dark"; fi; }
icon_source() {
    if [[ $INSTALL_ICONS -eq 0 ]]; then echo "no (Breeze)"
    elif [[ $EDITION == original ]]; then echo "Onze Icons (original, included)"
    elif [[ -f "$ICON_LOCAL/install.sh" ]]; then echo "local copy (vendor/)"
    elif [[ -f "$ICON_ARCHIVE" ]]; then echo "local archive (vendor/$(basename "$ICON_ARCHIVE"))"
    elif [[ $OFFLINE -eq 1 ]]; then echo "no local copy and --offline was used (Breeze)"
    else echo "download from GitHub"
    fi
}

record() {  # record <path> — remembers what was installed, without duplicates
    mkdir -p "$STATE"
    touch "$MANIFEST"
    grep -qxF "$1" "$MANIFEST" || printf '%s\n' "$1" >> "$MANIFEST"
}

copy_package() {  # copy_package <source> <destination>
    rm -rf "$2"
    mkdir -p "$(dirname "$2")"
    cp -r "$1" "$2"
    record "$2"
}

# --- checks ------------------------------------------------------------------------
if [[ $EUID -eq 0 && -z "${ONZE_ALLOW_ROOT:-}${ONZE_PERMITIR_ROOT:-}" ]]; then
    die "Do not run as root. The theme is installed for your user only."
fi
[[ -d "$SRC" ]] || die "Folder 'src' not found next to the installer."

if has plasmashell; then
    PV="$(plasmashell --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true)"
    PMAJ="${PV%%.*}"
    if [[ -n "$PV" && "$PMAJ" -lt 6 ]]; then
        die "Plasma $PV detected. Onze requires Plasma 6 (tested for 6.6)."
    fi
    [[ -n "$PV" ]] && info "Plasma $PV detected"
else
    warn "plasmashell not found — files will be installed, but nothing will be applied."
    APPLY=0
fi

if [[ $APPLY -eq 1 ]]; then
    for c in kwriteconfig6 plasma-apply-lookandfeel; do
        has "$c" || die "Command '$c' not found (package plasma-workspace / kf6-kconfig)."
    done
    if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]] || ! pgrep -u "$USER" -x plasmashell >/dev/null 2>&1; then
        warn "No running Plasma session detected — files will be installed without applying them."
        APPLY=0
    fi
fi

# --- choose the variant (light or dark) ------------------------------------------------
if [[ -z "$VARIANT" ]]; then
    if [[ $ASK -eq 1 && -t 0 ]]; then
        cat <<EOF

  ${B}Which theme variant do you want?${N}
    1) Light  — background #F3F3F3, blue accent #0067C0
    2) Dark   — background #202020, blue accent #4CC2FF

EOF
        while true; do
            read -r -p "Choose [1/2] (Enter = 1): " r
            case "${r,,}" in
                ""|1|l|light|c|claro) VARIANT="light"; break ;;
                2|d|dark|e|escuro)    VARIANT="dark"; break ;;
                *) echo "  Type 1 for light or 2 for dark." ;;
            esac
        done
    else
        VARIANT="light"   # non-interactive mode (-y or no terminal)
    fi
fi

# --- choose the Start button position ----------------------------------------------------
if [[ -z "$START" ]]; then
    if [[ $RESET_LAYOUT -eq 1 && $ASK -eq 1 && -t 0 ]]; then
        cat <<EOF

  ${B}Where should the Start button and apps be on the taskbar?${N}
    1) Center  — Windows 11 default
    2) Left    — Windows 10 style

EOF
        while true; do
            read -r -p "Choose [1/2] (Enter = 1): " r
            case "${r,,}" in
                ""|1|c|center|centro) START="center"; break ;;
                2|l|left|e|esquerda)  START="left"; break ;;
                *) echo "  Type 1 for center or 2 for left." ;;
            esac
        done
    else
        START="center"   # non-interactive mode, or --keep-layout
    fi
elif [[ $RESET_LAYOUT -eq 0 ]]; then
    warn "--start only takes effect when the taskbar is recreated (it is ignored with --keep-layout now,"
    warn "but will be used the next time you apply the Onze layout)."
fi

# --- choose the widgets' language -----------------------------------------------------------
if [[ -z "$LANG_UI" ]]; then
    if [[ $ASK -eq 1 && -t 0 ]]; then
        cat <<EOF

  ${B}Language of the theme's widgets (Search, Task View, Show Desktop):${N}
    1) English (default)
    2) Português (Brasil)

EOF
        while true; do
            read -r -p "Choose [1/2] (Enter = 1): " r
            case "${r,,}" in
                ""|1|en|english) LANG_UI="en"; break ;;
                2|pt|pt-br|portugues|português) LANG_UI="pt-BR"; break ;;
                *) echo "  Type 1 for English or 2 for Português (Brasil)." ;;
            esac
        done
    else
        LANG_UI="en"
    fi
fi

# Internal package names (kept for compatibility with existing installs)
if [[ "$VARIANT" == "light" ]]; then
    LNF="org.kde.onze.claro.desktop"; SCHEME="OnzeClaro"; ICONS="Win11"; DECO="Onze-Claro"
else
    LNF="org.kde.onze.escuro.desktop"; SCHEME="OnzeEscuro"; ICONS="Win11-dark"; DECO="Onze-Escuro"
fi
CURSOR="Onze-cursors"

cat <<EOF

  ${B}Onze ${VERSION}${N} — Windows 11 style theme for KDE Plasma 6
  Variant: ${B}${VARIANT}${N}
  Icons: $(icon_source)
  Taskbar height: ${HEIGHT} px
  Desktop icons: ${DESKTOP_ICONS} px
  Scrollbar arrows: $([[ $SCROLL_ARROWS -eq 1 ]] && echo "yes" || echo "no")
  Home and Trash on the desktop: $([[ $DESKTOP_SHORTCUTS -eq 1 ]] && echo "yes" || echo "no")
  Start button and apps: $([[ $START == left ]] && echo "left (Windows 10 style)" || echo "center (Windows 11)")
  Widgets language: $([[ $LANG_UI == pt-BR ]] && echo "Português (Brasil)" || echo "English")
  Recreate taskbar: $([[ $RESET_LAYOUT -eq 1 ]] && echo "yes (your current panels will be replaced)" || echo "no")
  Apply now: $([[ $APPLY -eq 1 ]] && echo "yes" || echo "no")

  Your current settings will be saved to:
    $BACKUP
  and can be restored with ./uninstall.sh

EOF

if [[ $ASK -eq 1 ]]; then
    read -r -p "Continue? [Y/n] " r
    [[ -z "$r" || "$r" =~ ^[YySs] ]] || { echo "Cancelled."; exit 0; }
fi

# --- 1. backup (first install only, to keep the original state) ---------------------
if [[ ! -d "$BACKUP" ]]; then
    info "Saving current settings"
    mkdir -p "$BACKUP"
    for f in kdeglobals kwinrc plasmarc kcminputrc ksplashrc kscreenlockerrc \
             plasma-org.kde.plasma.desktop-appletsrc plasmashellrc breezerc; do
        [[ -f "$CONF/$f" ]] && cp -p "$CONF/$f" "$BACKUP/$f"
        echo "$f" >> "$BACKUP/.checked"   # files covered by this backup
    done
    date -Iseconds > "$BACKUP/.data"
    ok "Backup created"
else
    info "Existing backup found — keeping the original state saved on $(cat "$BACKUP/.data" 2>/dev/null || echo '?')"
fi

# --- 2. theme files ------------------------------------------------------------------
info "Installing theme components"
mkdir -p "$DATA/color-schemes"
for f in "$SRC"/color-schemes/*.colors; do
    cp "$f" "$DATA/color-schemes/"
    record "$DATA/color-schemes/$(basename "$f")"
done
ok "Color schemes: Onze Light, Onze Dark"

copy_package "$SRC/desktoptheme/Onze" "$DATA/plasma/desktoptheme/Onze"
ok "Plasma style: Onze"

for d in "$SRC"/aurorae/*/; do
    n="$(basename "$d")"
    copy_package "$d" "$DATA/aurorae/themes/$n"
done
ok "Window decorations: Onze Light, Onze Dark"

for d in "$SRC"/plasmoids/*/; do
    [[ -f "$d/metadata.json" ]] || continue   # skip non-widget folders (translations/)
    n="$(basename "$d")"
    copy_package "$d" "$DATA/plasma/plasmoids/$n"
done
ok "Plasmoids: Search, Task View, Show Desktop"

# Widgets language: the sources are in English; pt-BR is applied from the table
TRANSLATIONS="$SRC/plasmoids/translations/pt_BR.tsv"
if [[ $LANG_UI == pt-BR ]]; then
    has perl || die "perl is required to translate the widgets (it is part of every Ubuntu system)."
    find "$DATA"/plasma/plasmoids/org.kde.onze.* \( -name '*.qml' -o -name 'metadata.json' \) -print0 |
        xargs -0 perl -CSD -i -e '
            my $tsv = shift @ARGV;
            open(my $fh, "<:encoding(UTF-8)", $tsv) or die "$tsv: $!";
            my @pairs;
            while (<$fh>) { chomp; next if /^#/ || !/\t/; push @pairs, [split /\t/, $_, 2]; }
            @pairs = sort { length($b->[0]) <=> length($a->[0]) } @pairs;
            local $/; while (<>) { for my $p (@pairs) { s/\Q$p->[0]\E/$p->[1]/g } print }
        ' "$TRANSLATIONS"
    ok "Widgets translated to Português (Brasil)"
fi


for d in "$SRC"/look-and-feel/*/; do
    n="$(basename "$d")"
    copy_package "$d" "$DATA/plasma/look-and-feel/$n"
done
ok "Global themes: Onze Light, Onze Dark (with splash screen)"

# Write the chosen alignment into the installed layout scripts
for js in "$DATA"/plasma/look-and-feel/org.kde.onze.*.desktop/contents/layouts/org.kde.plasma.desktop-layout.js; do
    [[ -f "$js" ]] || continue
    sed -i -e "s/^var startAlignment = \"[a-z]*\";/var startAlignment = \"$START\";/" \
           -e "s/^var desktopIconSize = [0-9]*;/var desktopIconSize = $ICON_LEVEL;/" "$js"
done

copy_package "$SRC/wallpapers/Onze" "$DATA/wallpapers/Onze"
ok "Wallpaper: Onze (light and dark)"

copy_package "$SRC/cursors/Onze-cursors" "$DATA/icons/Onze-cursors"
ok "Cursors: Onze (thin arrow, Windows 11 style)"

# --- desktop shortcuts: Home folder and Trash ------------------------------------------
# Plasma's desktop shows the contents of the user's Desktop folder, which starts
# empty on Kubuntu. Two standard KDE link files add the Home folder and the
# Trash (whose icon switches between empty and full by itself). Names follow
# the system language. Files we create carry X-Onze-Shortcut=true, so the
# uninstaller only removes our own files; existing files are never overwritten.
desktop_dir() {
    local d=""
    if has xdg-user-dir; then d="$(xdg-user-dir DESKTOP 2>/dev/null || true)"; fi
    if [[ -z "$d" || "$d" == "$HOME" ]] && [[ -f "$CONF/user-dirs.dirs" ]]; then
        d="$(sed -n 's/^XDG_DESKTOP_DIR="\(.*\)"$/\1/p' "$CONF/user-dirs.dirs" | head -n1)"
        d="${d/\$HOME/$HOME}"
    fi
    if [[ -z "$d" || "$d" == "$HOME" ]]; then d="$HOME/Desktop"; fi
    echo "$d"
}
add_shortcut() {  # add_shortcut <file name> <contents>
    local f="$DESKTOP_DIR/$1"
    if [[ -e "$f" ]] && ! grep -q '^X-Onze-Shortcut=true' "$f" 2>/dev/null; then
        warn "Keeping your existing $f"
        return 0
    fi
    printf '%s\n' "$2" > "$f"
    chmod +x "$f"
    grep -qxF "$f" "$STATE/desktop-shortcuts" 2>/dev/null || echo "$f" >> "$STATE/desktop-shortcuts"
}
if [[ $DESKTOP_SHORTCUTS -eq 1 ]]; then
    DESKTOP_DIR="$(desktop_dir)"
    mkdir -p "$DESKTOP_DIR" "$STATE"
    add_shortcut "onze-home.desktop" "[Desktop Entry]
Type=Link
URL=file://$HOME
Icon=org.kde.dolphin
Name=Home
Name[pt_BR]=Pasta pessoal
Name[pt]=Pasta pessoal
Name[es]=Carpeta personal
Comment=Your personal folder
Comment[pt_BR]=Sua pasta pessoal
X-Onze-Shortcut=true"
    add_shortcut "onze-trash.desktop" "[Desktop Entry]
Type=Link
URL=trash:/
Icon=user-trash-full
EmptyIcon=user-trash
Name=Trash
Name[pt_BR]=Lixeira
Name[pt]=Lixo
Name[es]=Papelera
Comment=Contains removed files
Comment[pt_BR]=Contém os arquivos removidos
X-Onze-Shortcut=true"
    # fixed dates keep Home before Trash (the desktop sorts them by date, see below)
    touch -d "2001-10-25 00:00:00" "$DESKTOP_DIR/onze-home.desktop" 2>/dev/null || true
    touch -d "2001-10-25 00:00:01" "$DESKTOP_DIR/onze-trash.desktop" 2>/dev/null || true
    ok "Desktop: Home folder and Trash icons"
fi

rm -f -- "$DATA/icons/hicolor/scalable/apps/onze-start.svg"
if [[ -f "$MANIFEST" ]]; then
    grep -vxF "$DATA/icons/hicolor/scalable/apps/onze-start.svg" "$MANIFEST" > "$MANIFEST.tmp" || true
    mv "$MANIFEST.tmp" "$MANIFEST"
fi

# Remove things earlier versions installed and this one no longer uses
# (Fluent cursors from 1.0, the Onze icon overlay themes from a 1.3 preview)
if [[ -f "$MANIFEST" ]]; then
    for old in Fluent-cursors Fluent-dark-cursors Onze-icons Onze-icons-dark; do
        if grep -qxF "$DATA/icons/$old" "$MANIFEST"; then
            rm -rf -- "${DATA:?}/icons/$old"
            grep -vxF "$DATA/icons/$old" "$MANIFEST" > "$MANIFEST.tmp" || true
            mv "$MANIFEST.tmp" "$MANIFEST"
        fi
    done
fi

# --- 3. icons (GPL community project) ---------------------------------------------------
TMP=""
cleanup() { if [[ -n "$TMP" && -d "$TMP" ]]; then rm -rf "$TMP"; fi; return 0; }
trap cleanup EXIT

fetch_repo() {  # fetch_repo <owner/repo> <destination>
    local repo="$1" dest="$2"
    if has git; then
        git clone -q --depth 1 "https://github.com/$repo.git" "$dest"
    else
        local url="https://github.com/$repo/archive/HEAD.tar.gz"
        mkdir -p "$dest"
        if has curl; then
            curl -fsSL "$url" | tar -xz -C "$dest" --strip-components=1
        elif has wget; then
            wget -qO- "$url" | tar -xz -C "$dest" --strip-components=1
        else
            return 1
        fi
    fi
}

if [[ $INSTALL_ICONS -eq 1 && $EDITION == original ]]; then
    [[ -f "$ONZE_ICONS/OnzeIcons/index.theme" ]] || die "Onze Icons not found in src/icons."
    mkdir -p "$DATA/icons"
    for t in OnzeIcons OnzeIcons-Dark; do
        copy_package "$ONZE_ICONS/$t" "$DATA/icons/$t"
        if has gtk-update-icon-cache; then
            gtk-update-icon-cache -f -q "$DATA/icons/$t" >/dev/null 2>&1 || true
        fi
    done
    ok "Icons: Onze Icons (light and dark, original artwork)"
fi

if [[ $INSTALL_ICONS -eq 1 && $EDITION == win11icons ]]; then
    TMP="$(mktemp -d)"
    mkdir -p "$DATA/icons"

    ORIGIN=""
    if [[ -f "$ICON_LOCAL/install.sh" ]]; then
        info "Installing Win11 icons from the local copy (vendor/)"
        ORIGIN="$ICON_LOCAL"
    elif [[ -f "$ICON_ARCHIVE" ]]; then
        info "Installing Win11 icons from the local archive (vendor/$(basename "$ICON_ARCHIVE"))"
        mkdir -p "$TMP/win11"
        if tar -xzf "$ICON_ARCHIVE" -C "$TMP/win11" --strip-components=1 &&
           [[ -f "$TMP/win11/install.sh" ]]; then
            ORIGIN="$TMP/win11"
        else
            warn "Could not extract $(basename "$ICON_ARCHIVE"); Breeze will be used."
        fi
    elif [[ $OFFLINE -eq 1 ]]; then
        warn "No local copy of the icons and --offline mode: Breeze will be used."
        warn "To bundle the icons, run tools/fetch-dependencies.sh with internet access."
    else
        info "Downloading Win11 icons (github.com/$ICON_REPO)"
        if fetch_repo "$ICON_REPO" "$TMP/win11" 2>/dev/null; then
            ORIGIN="$TMP/win11"
        else
            warn "Could not download the icons (no internet, git, curl or wget?)."
        fi
    fi
    if [[ -n "$ORIGIN" ]]; then
        existing=()
        for t in Win11 Win11-dark; do [[ -d "$DATA/icons/$t" ]] && existing+=("$t"); done
        # their installer calls gtk-update-icon-cache; provide a stub if it is missing
        mkdir -p "$TMP/bin"
        if ! has gtk-update-icon-cache; then
            printf '#!/bin/sh\nexit 0\n' > "$TMP/bin/gtk-update-icon-cache"
            chmod +x "$TMP/bin/gtk-update-icon-cache"
        fi
        if (cd "$ORIGIN" && PATH="$TMP/bin:$PATH" bash ./install.sh -d "$DATA/icons" >/dev/null 2>&1); then
            for t in Win11 Win11-dark; do
                [[ " ${existing[*]-} " == *" $t "* ]] || record "$DATA/icons/$t"
            done
            ok "Icons: Win11 and Win11-dark"
        else
            warn "The icon installer failed; Breeze will be used."
        fi
    fi
fi

icon_theme_for() {  # icon_theme_for <light|dark> — best available icon theme
    local sfx; sfx="$(dark_suffix "$1")"
    if [[ $INSTALL_ICONS -eq 1 && $EDITION == original && -f "$DATA/icons/OnzeIcons${sfx/-dark/-Dark}/index.theme" ]]; then
        echo "OnzeIcons${sfx/-dark/-Dark}"
    elif [[ $INSTALL_ICONS -eq 1 && $EDITION == win11icons && ( -d "$DATA/icons/Win11$sfx" || -d "/usr/share/icons/Win11$sfx" ) ]]; then
        echo "Win11$sfx"
    else
        echo "breeze$sfx"
    fi
}
ICONS="$(icon_theme_for "$VARIANT")"
[[ -d "$DATA/icons/$CURSOR" || -d "/usr/share/icons/$CURSOR" ]] || CURSOR=""

# Start button icon: the Win11 pack's own Start logo. The pack ships it only
# at 32 px; at 16/22/24 px its "start-here" icon is an Apple logo, so asking
# for "start-here" shows an Apple logo on taskbars shorter than ~40 px.
# An identical copy of that 32 px file is installed under a unique name in the
# generic "hicolor" icon folder. No icon theme has an icon with that name, so
# Plasma always uses this single SVG and just scales it, at any taskbar height.
# The icon pack itself is only read, never changed.
# (Onze Icons draws its own Start logo as a scalable icon, so the original
# edition simply uses the standard name.)
START_ICON="start-here-kde-plasma"
START_FILE="$DATA/icons/hicolor/scalable/apps/onze-start-here.svg"
WIN11_THEMES=()
if [[ $INSTALL_ICONS -eq 1 && $EDITION == win11icons ]]; then
    WIN11_THEMES=("$ICONS" Win11 Win11-dark)
else
    rm -f -- "$START_FILE"
    if [[ -f "$MANIFEST" ]]; then
        grep -vxF "$START_FILE" "$MANIFEST" > "$MANIFEST.tmp" || true
        mv "$MANIFEST.tmp" "$MANIFEST"
    fi
fi
for t in "${WIN11_THEMES[@]}"; do
    for base in "$DATA/icons" /usr/share/icons; do
        if [[ -f "$base/$t/status/32/start-here.svg" ]]; then
            mkdir -p "$(dirname "$START_FILE")"
            cp "$base/$t/status/32/start-here.svg" "$START_FILE"
            record "$START_FILE"
            START_ICON="onze-start-here"
            break 2
        fi
    done
done
rm -f "${XDG_CACHE_HOME:-$HOME/.cache}/icon-cache.kcache"
for js in "$DATA"/plasma/look-and-feel/org.kde.onze.*.desktop/contents/layouts/org.kde.plasma.desktop-layout.js; do
    [[ -f "$js" ]] || continue
    sed -i "s|^var startIcon = \".*\";|var startIcon = \"$START_ICON\";|" "$js"
done

# Point the packages' "defaults" to the icons/cursors that are actually available
for v in light dark; do
    pkg="org.kde.onze.$([[ $v == light ]] && echo claro || echo escuro).desktop"
    def="$DATA/plasma/look-and-feel/$pkg/contents/defaults"
    [[ -f "$def" ]] || continue
    sed -i "/^\[kdeglobals\]\[Icons\]/,/^\[/ s/^Theme=.*/Theme=$(icon_theme_for "$v")/" "$def"
    if [[ -z "$CURSOR" ]]; then
        sed -i 's/^cursorTheme=Onze-cursors$/cursorTheme=breeze_cursors/' "$def"
    fi
done

# --- 4. apply ---------------------------------------------------------------------------
kw() { kwriteconfig6 "$@"; }
dbus_call() { dbus-send --session --type=method_call "$@" >/dev/null 2>&1 || true; }

if [[ $APPLY -eq 1 ]]; then
    info "Applying global theme $LNF"
    if [[ $RESET_LAYOUT -eq 1 ]]; then
        plasma-apply-lookandfeel -a "$LNF" --resetLayout >/dev/null
    else
        plasma-apply-lookandfeel -a "$LNF" >/dev/null
    fi

    # Reinforce individual components (some keys are not applied by the package)
    has plasma-apply-colorscheme  && plasma-apply-colorscheme "$SCHEME" >/dev/null 2>&1 || true
    has plasma-apply-desktoptheme && plasma-apply-desktoptheme Onze >/dev/null 2>&1 || true
    if [[ -n "$CURSOR" ]] && has plasma-apply-cursortheme; then
        plasma-apply-cursortheme "$CURSOR" >/dev/null 2>&1 || true
    fi
    CHANGEICONS="$(ls /usr/lib/*/libexec/plasma-changeicons /usr/libexec/plasma-changeicons 2>/dev/null | head -n1 || true)"
    if [[ -n "$CHANGEICONS" ]]; then
        "$CHANGEICONS" "$ICONS" >/dev/null 2>&1 || true
    else
        kw --file kdeglobals --group Icons --key Theme "$ICONS"
    fi

    G=(--file kwinrc --group org.kde.kdecoration2)
    kw "${G[@]}" --key library org.kde.kwin.aurorae
    kw "${G[@]}" --key theme "__aurorae__svg__$DECO"
    kw "${G[@]}" --key ButtonsOnLeft ""
    kw "${G[@]}" --key ButtonsOnRight "IAX"
    # "Normal" border size: Aurorae uses the theme's 4 px frame (rounded bottom corners)
    kw "${G[@]}" --key BorderSize "Normal"
    kw "${G[@]}" --key BorderSizeAuto false
    kw --file kwinrc --group WindowSwitcher --key LayoutName thumbnail_grid

    # Scrollbar arrow buttons (Breeze application style): one at each end
    if [[ $SCROLL_ARROWS -eq 1 ]]; then
        kw --file breezerc --group Style --key ScrollBarSubLineButtons 1
        kw --file breezerc --group Style --key ScrollBarAddLineButtons 1
    fi
    kw --file ksplashrc --group KSplash --key Engine KSplashQML
    kw --file ksplashrc --group KSplash --key Theme "$LNF"

    # Wallpaper (desktop and lock screen)
    WP="$DATA/wallpapers/Onze"
    sleep 2
    if has plasma-apply-wallpaperimage; then
        plasma-apply-wallpaperimage "$WP" >/dev/null 2>&1 || warn "Set the wallpaper manually: $WP"
    fi

    # Taskbar height, clock font and desktop icon size (also applied with --keep-layout)
    JS="desktops().forEach(function (d) {
        d.currentConfigGroup = ['General'];
        d.writeConfig('iconSize', ${ICON_LEVEL});
        if (${DESKTOP_SHORTCUTS} === 1) {
            d.writeConfig('arrangement', 1);   // columns, top to bottom (Windows style)
            d.writeConfig('sortMode', 4);      // by date: Home, then Trash, then new files
        }
        d.reloadConfig();
    });
    panels().forEach(function (p) {
        p.widgets('org.kde.plasma.kickoff').forEach(function (w) {
            w.currentConfigGroup = ['General'];
            var icon = String(w.readConfig('icon', 'start-here-kde-plasma'));
            if (icon === '' || icon.indexOf('start-here') === 0 || icon.indexOf('onze-start') !== -1 ||
                /\/start-here\.svg\$/.test(icon)) {
                w.writeConfig('icon', '${START_ICON}');
                w.reloadConfig();
            }
        });
        if (p.location === 'bottom' || p.location === 'top') { p.height = ${HEIGHT}; }
        p.widgets('org.kde.plasma.digitalclock').forEach(function (w) {
            w.currentConfigGroup = ['Appearance'];
            w.writeConfig('autoFontAndSize', false);
            w.writeConfig('fontSize', 10);
            w.writeConfig('fontWeight', 400);
            w.reloadConfig();
        });
    });"
    if has dbus-send; then
        dbus-send --session --type=method_call --dest=org.kde.plasmashell /PlasmaShell \
            org.kde.PlasmaShell.evaluateScript "string:$JS" >/dev/null 2>&1 ||
            warn "Could not adjust the taskbar automatically (Edit Mode > height ${HEIGHT})."
    fi

    LG=(--file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General)
    kw "${LG[@]}" --key Image "file://$WP"
    kw "${LG[@]}" --key PreviewImage "file://$WP"

    dbus_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure
    ok "Theme applied"
else
    info "Files installed. To apply: System Settings > Appearance > Global Theme > Onze"
fi

echo "$VARIANT" > "$STATE/variant"
echo "$START" > "$STATE/start"
echo "$EDITION" > "$STATE/edition"
echo "$LANG_UI" > "$STATE/lang"
cp "$DIR/uninstall.sh" "$STATE/uninstall.sh" 2>/dev/null && chmod +x "$STATE/uninstall.sh" || true

cat <<EOF

${GR}${B}Done!${N}
  • Switch between light and dark in System Settings > Global Theme
    (Plasma 6.5+ can switch automatically between "Onze Light" and "Onze Dark").
  • Apps that are already open may need a restart to pick up the new colors.
  • Some changes (cursor, splash screen) only show up after logging out and back in.
  • To undo everything: ./uninstall.sh  (copy at $STATE/uninstall.sh)

EOF
