#!/usr/bin/env bash
# =============================================================================
#  Onze — captures the store screenshots in a real Plasma 6 session
#
#  Run it inside Kubuntu / KDE Plasma 6 with the Onze theme already installed:
#
#      ./take-screenshots.sh /path/to/onze-theme-1.4
#
#  (the argument is the extracted package folder: it is used for the installer
#  screenshot and to open its README.md in Kate)
#
#  It takes, into screenshots/<edition>/:
#    01-installer.png          installer menus (light variant, centered taskbar, English)
#    02-desktop-light.png      empty desktop with Home and Trash, light
#    03-desktop-dark.png       same, dark
#    04-start-menu-light.png   Start menu open, light
#    05-start-menu-dark.png    Start menu open, dark
#    06-apps-light.png         Dolphin (Home), Konsole (fastfetch), Kate (README), light
#    07-apps-dark.png          same, dark
#
#  Options:
#    --manual    pause before every screenshot, so you can arrange things by hand
#
#  Do not touch the mouse or keyboard while it runs (about 2 minutes).
#  Your current global theme (light or dark) is restored at the end.
# =============================================================================
set -Eeuo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG=""
MANUAL=0
for a in "$@"; do
    case "$a" in
        --manual) MANUAL=1 ;;
        -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) PKG="$a" ;;
    esac
done
[[ -n "$PKG" && -f "$PKG/install.sh" && -f "$PKG/README.md" ]] ||
    { echo "Usage: $0 /path/to/onze-theme-1.4   (the extracted package folder)" >&2; exit 1; }
PKG="$(cd "$PKG" && pwd)"

has() { command -v "$1" >/dev/null 2>&1; }
QDBUS="$(command -v qdbus6 || command -v qdbus || true)"
missing=()
for c in spectacle konsole dolphin kate python3 plasma-apply-lookandfeel kreadconfig6; do
    has "$c" || missing+=("$c")
done
[[ -n "$QDBUS" ]] || missing+=("qdbus6")
if (( ${#missing[@]} )); then
    echo "Missing programs: ${missing[*]}" >&2
    exit 1
fi
if ! has fastfetch; then
    echo "fastfetch is not installed (it is used in the terminal screenshot)."
    echo "Install it with:  sudo apt install fastfetch"
    read -r -p "Continue without it? [y/N] " r
    [[ "$r" =~ ^[YySs] ]] || exit 1
fi

STATE="${XDG_DATA_HOME:-$HOME/.local/share}/onze-theme"
EDITION="$(cat "$STATE/edition" 2>/dev/null || echo unknown)"
OUT="$KIT/screenshots/$EDITION"
mkdir -p "$OUT"
TMP="$(mktemp -d)"
PIDS=()
ORIG_LNF="$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage 2>/dev/null || true)"

cleanup() {
    for p in "${PIDS[@]-}"; do [[ -n "$p" ]] && kill "$p" 2>/dev/null || true; done
    show_desktop false
    if [[ -n "$ORIG_LNF" ]]; then plasma-apply-lookandfeel -a "$ORIG_LNF" >/dev/null 2>&1 || true; fi
    rm -rf "$TMP"
}
trap cleanup EXIT

show_desktop() {  # show_desktop true|false
    "$QDBUS" org.kde.KWin /KWin org.kde.KWin.showDesktop "$1" >/dev/null 2>&1 ||
        "$QDBUS" org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut \
            "Show Desktop" >/dev/null 2>&1 || true
}
kwin_js() {  # kwin_js <file> — runs a KWin script once
    "$QDBUS" org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript onze-shot >/dev/null 2>&1 || true
    local id
    id="$("$QDBUS" org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$1" onze-shot 2>/dev/null || true)"
    [[ -n "$id" ]] || return 1
    "$QDBUS" org.kde.KWin "/Scripting/Script$id" org.kde.kwin.Script.run >/dev/null 2>&1 ||
        "$QDBUS" org.kde.KWin "/$id" org.kde.kwin.Script.run >/dev/null 2>&1 || true
    sleep 1
    "$QDBUS" org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript onze-shot >/dev/null 2>&1 || true
}
minimize_all() {  # hides every window open now (including this terminal)
    cat > "$TMP/minimize.js" <<'EOF'
var wins = workspace.windowList();
for (var i = 0; i < wins.length; i++) {
    if (wins[i].normalWindow && wins[i].minimizable) wins[i].minimized = true;
}
EOF
    kwin_js "$TMP/minimize.js" || true
}
toggle_menu() {
    "$QDBUS" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu >/dev/null 2>&1 || true
}
variant() {  # variant light|dark
    local pkg="org.kde.onze.claro.desktop"
    [[ $1 == dark ]] && pkg="org.kde.onze.escuro.desktop"
    echo "==> Switching to $1"
    plasma-apply-lookandfeel -a "$pkg" >/dev/null 2>&1 || true
    sleep 5
}
shot() {  # shot <name>
    if [[ $MANUAL -eq 1 ]]; then read -r -p "Ready for $1? Press Enter " _; fi
    sleep 1
    spectacle --background --nonotify --fullscreen --output "$OUT/$1.png" >/dev/null 2>&1
    sleep 1.5
    if [[ -s "$OUT/$1.png" ]]; then echo " ✓ $1.png"; else echo " ✗ $1.png was not saved" >&2; fi
}
arrange() {  # arrange <mode>: "installer" or "apps"
    cat > "$TMP/arrange.js" <<EOF
var mode = "$1";
var area = workspace.clientArea(KWin.PlacementArea, workspace.activeScreen, workspace.currentDesktop);
function place(w, fx, fy, fw, fh) {
    w.frameGeometry = { x: Math.round(area.x + area.width * fx), y: Math.round(area.y + area.height * fy),
                        width: Math.round(area.width * fw), height: Math.round(area.height * fh) };
}
var wins = workspace.windowList();
var front = null, order = [];
for (var i = 0; i < wins.length; i++) {
    var w = wins[i];
    if (w.minimized || !w.normalWindow) continue;
    var c = String(w.resourceClass).toLowerCase();
    if (mode === "installer" && c.indexOf("konsole") !== -1) { place(w, 0.17, 0.08, 0.66, 0.80); front = w; }
    if (mode === "apps") {
        if (c.indexOf("kate") !== -1)    { place(w, 0.47, 0.05, 0.49, 0.80); order[0] = w; }
        if (c.indexOf("dolphin") !== -1) { place(w, 0.04, 0.05, 0.52, 0.60); order[1] = w; }
        if (c.indexOf("konsole") !== -1) { place(w, 0.10, 0.38, 0.47, 0.54); order[2] = w; }
    }
}
for (var j = 0; j < order.length; j++) { if (order[j]) workspace.activeWindow = order[j]; }
if (front) workspace.activeWindow = front;
EOF
    kwin_js "$TMP/arrange.js" ||
        echo " ! Could not arrange the windows automatically; use --manual to arrange them yourself." >&2
}

echo "Onze screenshots — edition: $EDITION — saving to $OUT"
echo "Do not touch the mouse or keyboard until it finishes."
echo "(All open windows, including this terminal, will be minimized.)"
sleep 4
minimize_all
sleep 1

# ---- light ----------------------------------------------------------------------
variant light

# 01 installer: runs the installer in a terminal and answers the menus
#    (1 = light, 1 = center, 1 = English); it stops at "Continue?", before
#    anything is changed, and is closed after the screenshot.
cat > "$TMP/drive-installer.py" <<'EOF'
import os, pty, select, sys, time
pkg = sys.argv[1]
answers = [b"1\r", b"1\r", b"1\r"]
pid, fd = pty.fork()
if pid == 0:
    os.chdir(pkg)
    os.execvp("bash", ["bash", "./install.sh"])
buf = b""
while True:
    r, _, _ = select.select([fd], [], [], 30)
    if not r:
        break
    try:
        data = os.read(fd, 4096)
    except OSError:
        break
    if not data:
        break
    os.write(1, data)
    buf += data
    if b"Choose [1/2]" in buf and answers:
        time.sleep(0.8)
        os.write(fd, answers.pop(0))
        buf = b""
    elif b"Continue? [Y/n]" in buf:
        break
time.sleep(3600)
EOF
konsole --separate --hide-menubar --workdir "$PKG" -e python3 "$TMP/drive-installer.py" "$PKG" >/dev/null 2>&1 &
PIDS+=("$!")
sleep 7
arrange installer
sleep 1
shot 01-installer
kill "${PIDS[-1]}" 2>/dev/null || true
sleep 2

# 02 / 04 desktop and Start menu (all windows hidden)
show_desktop true
sleep 2
shot 02-desktop-light
toggle_menu
sleep 2
shot 04-start-menu-light
toggle_menu
sleep 1
show_desktop false

# 06 apps
dolphin --new-window "$HOME" >/dev/null 2>&1 &
PIDS+=("$!")
if has fastfetch; then
    konsole --separate --workdir "$HOME" -e bash -c 'clear; fastfetch; exec bash' >/dev/null 2>&1 &
else
    konsole --separate --workdir "$HOME" >/dev/null 2>&1 &
fi
PIDS+=("$!")
kate --new "$PKG/README.md" >/dev/null 2>&1 &
PIDS+=("$!")
sleep 8
arrange apps
sleep 2
shot 06-apps-light

# ---- dark ------------------------------------------------------------------------
variant dark
arrange apps
sleep 2
shot 07-apps-dark
show_desktop true
sleep 2
shot 03-desktop-dark
toggle_menu
sleep 2
shot 05-start-menu-dark
toggle_menu
sleep 1

echo
echo "Done. Screenshots in: $OUT"
echo "Check them, and run it again (or with --manual) if something looks off."
