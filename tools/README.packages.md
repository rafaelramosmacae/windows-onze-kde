# Onze — Windows 11 style global theme for KDE Plasma 6

A complete theme for **KDE Plasma 6.6 / Kubuntu 26.04** that recreates the look
of Windows 11: centered taskbar, grid Start menu, rounded corners, wide window
buttons with a red "close", Fluent light and dark palettes, plus matching icons
and cursors.

![Preview](src/look-and-feel/org.kde.onze.claro.desktop/contents/previews/preview.png)

Its icons are **Onze Icons**, an original icon theme made for Onze (100%
original artwork).

## Installation

```bash
tar xzf onze-theme-1.4.tar.gz
cd onze-theme-1.4
./install.sh                       # asks: light or dark? center or left? language?
./install.sh --dark --start left   # answers questions up front
```

Do not use `sudo`: everything is installed into `~/.local/share` for your user
only. The installer asks for confirmation, saves your current settings and
applies the theme right away. Log out and back in to see the new cursor and
splash screen.

| Option | Effect |
|---|---|
| `-l`, `--light` | Apply the light variant (without `-l`/`-d`, the installer asks) |
| `-d`, `--dark` | Apply the dark variant |
| `-s`, `--start POS` | Start button and apps position: `center` (Windows 11) or `left` (Windows 10 style); asked if not given |
| `-L`, `--lang LANG` | Language of the theme's widgets: `en` (English, default) or `pt-BR` (Português do Brasil); asked if not given |
| `-H`, `--height N` | Taskbar height in pixels (default: **40**) |
| `-D`, `--desktop-icons N` | Desktop icon size in pixels: 22, 32, 48, 64 or 96 (default: **48**, one level below Plasma's 64) |
| `-k`, `--keep-layout` | Do not recreate the taskbar; keep your panels and widgets |
| `-i`, `--no-icons` | Do not install Onze Icons (uses Breeze) |
| `-N`, `--no-desktop-shortcuts` | Do not add the Home folder and Trash icons to the desktop |
| `-A`, `--no-scroll-arrows` | Do not show arrow buttons at the ends of scrollbars |
| `-n`, `--no-apply` | Install only; apply later in *System Settings › Global Theme* |
| `-y`, `--yes` | Do not ask for confirmation |

> **Note:** without `--keep-layout`, your current taskbar and widgets are
> replaced by the Onze layout (the backup lets you go back).

## Uninstalling

```bash
./uninstall.sh               # restores the state from before the installation
./uninstall.sh --no-restore  # applies Breeze instead of restoring
./uninstall.sh --keep-icons  # keeps the installed icon theme
```

A copy of the uninstaller is kept at `~/.local/share/onze-theme/uninstall.sh`.
It only deletes what the installer recorded in
`~/.local/share/onze-theme/manifest`.

## What's included

| Component | Name | Location |
|---|---|---|
| Global theme (light/dark) | Onze Light, Onze Dark | `plasma/look-and-feel/org.kde.onze.*.desktop` |
| Color scheme | Onze Light, Onze Dark | `color-schemes/OnzeClaro.colors`, `OnzeEscuro.colors` |
| Plasma style | Onze | `plasma/desktoptheme/Onze` |
| Window decoration (Aurorae) | Onze Light, Onze Dark | `aurorae/themes/Onze-*` |
| Layout | 40 px bottom taskbar, items centered or on the left | global theme layout script |
| Plasmoids | Search, Task View, Show Desktop | `plasma/plasmoids/org.kde.onze.*` |
| Splash screen | blue ring + spinning dots | `contents/splash/Splash.qml` |
| Wallpaper | Onze — blue folded-sheet sculpture, light and dark versions, 16:9 and 16:10 up to 3840 px (switches with light/dark) | `wallpapers/Onze` |
| Cursors | Onze — thin white arrow with a 1 px black outline | `icons/Onze-cursors` |
| Icons | Onze Icons, Onze Icons Dark — original Fluent-style icon theme | `icons/OnzeIcons`, `icons/OnzeIcons-Dark` |

### Details

**Colors** — Fluent Design values: background `#F3F3F3`/`#202020`, content
`#FFFFFF`/`#272727`, accent `#0067C0` (light) and `#4CC2FF` (dark, with black
text on the accent, as in Windows 11). Inactive windows are not dimmed.

**Plasma style** — menus, popups and tooltips with 8 px corners, a thin border,
a soft downward shadow and an acrylic effect (blur + transparency). The taskbar
is flat, with only a thin line on top. Task buttons have the Windows 11 "pill":
long and blue for the focused app, short and gray for apps running in the
background. It also works with vertical or top panels. All colors come from the
active color scheme, so a single style serves both light and dark.

**Window decoration** — 32 px title bar in the window color, left-aligned title,
46 × 31 px buttons with thin glyphs (minimize, maximize, restore, close), a red
`#C42B1C` "close" on hover with a rounded top-right corner, 8 px corners at the
top **and at the bottom**, and a large shadow. The sides and bottom have a 4 px
frame in the window color (border size **Normal**): it is what lets the bottom
corners be rounded, since KWin does not round the contents of windows drawn by
an Aurorae theme. Where an app paints a different color right up to the edge
(e.g. a terminal), the frame shows as a thin band. Maximized windows have no
frame. You resize windows from the frame or from the invisible area around it.

**Taskbar** — `[ Start | Search | Task View | pinned apps ]` in the center
(or on the left, Windows 10 style, if you choose so during installation);
system tray, clock (time above date) and the "show desktop" strip on the right.
The choice is stored in the installed layout script, so it is kept if you
reapply the Onze layout later from System Settings.
The clock uses a fixed 10 pt font (Plasma's automatic size made the time and
date too large). Taskbar height and clock font are also adjusted when you use
`--keep-layout`. Pinned apps: Dolphin, default web browser, Discover, Konsole
and System Settings. The **Meta** key opens the Start menu.

**Home and Trash on the desktop** — Kubuntu starts with an empty desktop. The
installer adds two standard KDE shortcuts to your Desktop folder (found with
`xdg-user-dir`, so it also works when the folder has a translated name):
your Home folder (with the Dolphin file manager icon, a yellow folder with a
blue band) and the Trash, whose icon switches between empty and full by
itself. Their names follow the system language ("Pasta pessoal" and
"Lixeira" in Brazilian Portuguese). Home comes first, then Trash; new files
go after them. Existing files are never overwritten, and
the uninstaller removes only the shortcuts Onze created. Use
`--no-desktop-shortcuts` to skip them.

**Desktop icons** — 48 px, one level below Plasma's default (64 px) and close
to Windows 11's "Medium icons". Change it with `--desktop-icons`; it is also
applied with `--keep-layout`.

**Scrollbars** — arrow buttons at both ends of application scrollbars, as in
Windows 11 (an official option of the Breeze application style, saved in
`~/.config/breezerc`). The arrows are Breeze's small chevrons rather than
Windows' filled triangles. Use `--no-scroll-arrows` to keep the default.
Scrollbars inside Plasma popups and in apps with their own scrollbars
(e.g. Firefox) are not affected.

**Custom plasmoids**
- *Search*: rounded box that opens KRunner (with an "icon only" option).
- *Task View*: opens the KWin Overview (all windows and virtual desktops).
- *Show Desktop*: thin strip in the right corner, as in Windows 11.

Their texts are in English by default. The installer asks for the language
(or use `--lang pt-BR`) and applies the translations from
`src/plasmoids/translations/pt_BR.tsv`, a simple English → Portuguese table
that can be extended with new strings.

**Onze Icons** — an icon theme drawn from scratch for Onze, in a Fluent /
Windows 11 spirit: yellow folders with a sheet of paper peeking out and a
colored badge on special folders (Documents, Downloads, Music, Pictures…),
file types as pages with a folded corner and a colored label, devices, the
KDE and system apps (Files, Terminal, Settings, Discover, Kate, Okular,
Gwenview, Ark, Spectacle…), application categories, dialogs, security
shields and the Start menu's session buttons (Sleep, Restart, Shut Down,
Lock, Log Out, Switch User, as monochrome glyphs that follow the color
scheme) — about 130 drawings under some 600 icon names, all scalable (SVG).
Icons it does not provide (third-party app logos, toolbar and tray icons)
come from the apps themselves or from Breeze / Breeze Dark. KDE looks for a
shorter name inside the current theme before trying Breeze
(`network-wired-activated` → `network-wired`), which would put an unrelated
Onze drawing on tray icons, battery levels or System Settings pages; for
those names the theme has links (`breeze-links/`) to the Breeze files already
installed on the system, so they look exactly as with Breeze. The Start button
uses Onze's own logo: four diamonds, a 45° rotated grid. Everything is
generated by `tools/gerar_icones.py`; `tools/previa-icones.png` shows all of
them on light and dark backgrounds, and `tools/onze-icons-showcase.png` (made by
`tools/make-icon-showcase.py`) the main ones:

![Onze Icons](tools/onze-icons-showcase.png)

**Alt+Tab** uses the thumbnail grid (*thumbnail_grid*).

**Cursors** — the drawing is scaled to 85% of the canvas: at the default
size (24) the arrow measures 12 × 17 px, with a pixel-sharp 1 px outline.

## Offline installation

Nothing is ever downloaded: every part of the theme, including the icons,
is in the package.

## Automatic light/dark switching

On Plasma 6.5 or newer, open *System Settings › Global Theme* and pick
**Onze Light** for the day and **Onze Dark** for the night. The wallpaper
follows the switch as well.

## Customizing

The SVGs, color schemes and previews are generated by
`tools/gerar_tema.py`; the cursors by `tools/gerar_cursores.py` (the
`SCALE` constant sets the cursor size); the wallpaper package by
`tools/prepare_wallpaper.py`, from `tools/wallpaper/source.png`
(upscaling, 16:9 version and dark version — see the script's header).
The icon theme is generated by `tools/gerar_icones.py`.
To change the accent color, corner radii or shadows, edit the constants at
the top of the file and run:

```bash
pip install numpy pillow shapely scipy matplotlib cairosvg
python3 tools/gerar_tema.py
python3 tools/gerar_cursores.py
./install.sh
```

The package is built from the source folder with `tools/build-packages.sh`.

## Known limitations

- **Rounded bottom corners**: they come from the 4 px window frame, not from
  rounding the app itself, so the app's own corner stays square inside the
  curve. It is only noticeable where the app paints a dark color up to the edge
  (e.g. Konsole with the light theme). The community effect
  [KDE-Rounded-Corners](https://github.com/matinlotfali/KDE-Rounded-Corners)
  rounds the window contents too, at some GPU cost.
- **Application style**: controls inside apps keep the Breeze style (with the
  Onze colors). For Fluent-style controls, see Kvantum with the
  [Fluent-kde](https://github.com/vinceliuice/Fluent-kde) theme.
- **Icon coverage**: Onze Icons covers folders, file types, devices, KDE and
  system apps, categories and dialogs. Toolbar and tray icons come from
  Breeze, and third-party apps keep their own logos.
- **Login screen (SDDM)** is not changed, as that would require `sudo`.
- The icons, cursors and splash screen are original artwork; the wallpaper
  was created by the author (see Credits). No Microsoft files or logos are
  included.

## Credits

**Onze theme**, version 1.4 — a **Projeto Onze** project, created by
**Rafael Carvalho Ramos**
([rafaelramosmacae@gmail.com](mailto:rafaelramosmacae@gmail.com)):
color schemes, Plasma style, window decorations, layout, plasmoids, splash
screen, cursors, the Onze Icons theme and installation scripts.
The wallpaper was created by him with the help of ChatGPT (image generation)
and prepared for the theme (neural upscaling, 16:9 and dark versions).

Text labels on some file-type icons use outlines of the
[Inter](https://rsms.me/inter/) font by Rasmus Andersson (SIL Open Font
License 1.1).

## License

Onze code and artwork, including Onze Icons: GPL-3.0-or-later (full text in `LICENSE`).

Wallpaper (`src/wallpapers/Onze`, and its source image in
`tools/wallpaper/source.png`): [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)
— dedicated to the public domain; you may copy, modify and redistribute it,
even commercially, without asking permission.

"Windows" and "Windows 11" are trademarks of Microsoft; this project is not
affiliated with or endorsed by Microsoft.

## Changelog

- **1.4** — Windows with rounded bottom corners: 4 px frame in the window
  color around the sides and bottom (border size "Normal"). Desktop: Home
  folder above Trash in every language (icons sorted by date, folders not
  forced first).
  Onze Icons: monochrome "Favorites" icon in the Start menu, like the other
  icons in its sidebar.
- **1.3** — New original **Onze Icons** icon theme.
  New wallpaper by the author, in light and dark versions, 16:9 and 16:10, up to 3840 px.
  Widgets in English or Portuguese (`--lang`, asked during installation).
  Home folder and Trash icons on the desktop (`--no-desktop-shortcuts` to
  skip). Start button keeps the same logo at any taskbar height. Scrollbar arrow
  buttons at both ends (`--no-scroll-arrows` to disable). Desktop icons one
  level smaller (48 px, `--desktop-icons` to change). Cursors 15% smaller.
  README and scripts translated to English (the previous Portuguese option
  names still work as aliases); themes now show up as "Onze Light" and
  "Onze Dark". The installer asks whether the Start button and apps should
  be centered (Windows 11) or on the left (Windows 10 style).
  Onze Icons: own icons for the Start menu's Sleep, Restart, Shut Down, Lock,
  Log Out and Switch User buttons (they all showed a computer before), and
  tray, battery and System Settings icons no longer replaced by unrelated
  Onze drawings.
- **1.2** — the installer asks whether you want the light or dark variant
  (with `-y` and no explicit choice, it uses light).
- **1.1** — new wallpaper (layered sheets, less saturated blue); custom cursors
  with a thin outline; 40 px taskbar (`--height` to change it); smaller clock
  font.
- **1.0** — first release.
