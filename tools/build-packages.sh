#!/usr/bin/env bash
# =============================================================================
#  Onze — builds the release packages from this source folder
#
#    onze-theme-<version>.tar.gz             "original" edition: Onze Icons,
#                                            100% original artwork, no third-party icons
#    onze-theme-win11icons-<version>.tar.gz  "win11icons" edition, built only when vendor/
#                                            holds the Win11 icon theme by yeyushengfan258
#    onze-theme-store-kit.tar.gz             store listing kit
#
#  The packages' README.md comes from tools/README.packages.md (the repository's
#  README.md is the GitHub page). Blocks between
#     <!-- edition:original -->   ...  <!-- /edition:original -->
#     <!-- edition:win11icons --> ...  <!-- /edition:win11icons -->
#  are kept only in the matching package (the marker lines themselves are removed).
#
#  Usage:  tools/build-packages.sh [output folder]   (default: dist/)
# =============================================================================
set -Eeuo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="$(realpath -m "${1:-$DIR/dist}")"
VERSION="$(sed -n 's/^VERSION="\(.*\)"/\1/p' "$DIR/install.sh" | head -n1)"
[[ -n "$VERSION" ]] || { echo "Could not read VERSION from install.sh" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$OUTDIR"

# Reproducible archives: same content -> byte-identical file and checksum
# (fixed dates, sorted entries, numeric owner, normalized permissions, gzip without a timestamp).
EPOCH="2026-10-26 00:00:00 UTC"
pack() {  # pack <output.tar.gz> <folder name inside $TMP>
    tar -C "$TMP" --sort=name --mtime="$EPOCH" --owner=0 --group=0 --numeric-owner --mode=u+rwX,go+rX,go-w \
        --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime -cf - "$2" | gzip -n -9 > "$1"
}

filter_readme() {  # filter_readme <edition> <file>
    local keep="$1" drop
    if [[ $keep == original ]]; then drop=win11icons; else drop=original; fi
    awk -v drop="$drop" '
        $0 ~ "<!-- edition:" drop " -->"   { skip = 1; next }
        $0 ~ "<!-- /edition:" drop " -->"  { skip = 0; next }
        $0 ~ "<!-- /?edition:[a-z0-9]+ -->" { next }
        !skip { print }
    ' "$2" > "$2.tmp" && mv "$2.tmp" "$2"
}

build() {  # build <edition> <folder/package name>
    local edition="$1" name="$2" stage="$TMP/$2"
    mkdir -p "$stage"
    # copy the project (symlinks kept as symlinks), without build output and caches
    tar -C "$DIR" --exclude=./dist --exclude=./tools/store-kit --exclude='__pycache__' --exclude='*.pyc' \
        --exclude=./.git --exclude=./.gitignore -cf - . | tar -C "$stage" -xf -
    mv "$stage/tools/README.packages.md" "$stage/README.md"
    echo "$edition" > "$stage/EDITION"
    if [[ $edition == original ]]; then
        rm -rf "$stage/vendor" "$stage/tools/fetch-dependencies.sh"
        # the global themes point straight to Onze Icons
        sed -i 's/^Theme=Win11$/Theme=OnzeIcons/; s/^Theme=Win11-dark$/Theme=OnzeIcons-Dark/' \
            "$stage"/src/look-and-feel/*/contents/defaults
        # previews shown in System Settings > Global Theme: real screenshots of this edition
        local shots="$DIR/tools/store-kit/screenshots/original"
        if [[ -f "$shots/04-start-menu-light.png" && -f "$shots/05-start-menu-dark.png" ]]; then
            python3 - "$shots" "$stage/src/look-and-feel" <<'PY'
import os, sys
from PIL import Image
shots, lnf = sys.argv[1:3]
for pkg, shot in (("org.kde.onze.claro.desktop", "04-start-menu-light.png"),
                  ("org.kde.onze.escuro.desktop", "05-start-menu-dark.png")):
    im = Image.open(os.path.join(shots, shot)).convert("RGB")
    out = os.path.join(lnf, pkg, "contents", "previews")
    im.resize((512, 288), Image.LANCZOS).save(os.path.join(out, "preview.png"), optimize=True)
    im.save(os.path.join(out, "fullscreenpreview.jpg"), quality=90, optimize=True)
PY
        fi
    else
        if [[ ! -d "$stage/vendor/Win11-icon-theme" ]]; then
            # the repository keeps only the original archive: extract it (unchanged) for offline installs
            (cd "$stage/vendor" && sha256sum -c --quiet Win11-icon-theme-main.tar.gz.sha256)
            mkdir -p "$stage/vendor/Win11-icon-theme"
            tar -xzf "$stage/vendor/Win11-icon-theme-main.tar.gz" -C "$stage/vendor/Win11-icon-theme" --strip-components=1
            if [[ -f "$DIR/vendor/.onze-version" ]]; then cp "$DIR/vendor/.onze-version" "$stage/vendor/Win11-icon-theme/"; fi
        fi
        rm -rf "$stage/src/icons" "$stage/tools/gerar_icones.py" "$stage/tools/previa-icones.png" "$stage/tools/breeze-ref" \
            "$stage/tools/make-icon-showcase.py" "$stage/tools/onze-icons-showcase.png"
    fi
    filter_readme "$edition" "$stage/README.md"
    sed -i "s/@PACKAGE@/$name/g" "$stage/README.md"
    pack "$OUTDIR/$name.tar.gz" "$name"
    echo " ✓ $OUTDIR/$name.tar.gz ($(du -h "$OUTDIR/$name.tar.gz" | cut -f1))"
}

build_store_kit() {  # store kit: listing texts, artwork, screenshot script, checksums
    local name="onze-theme-store-kit" stage="$TMP/onze-theme-store-kit" files="" f
    mkdir -p "$stage"
    tar -C "$DIR/tools/store-kit" --exclude='make-artwork.py' --exclude='__pycache__' -cf - . | tar -C "$stage" -xf -
    (cd "$OUTDIR" && sha256sum "${BUILT[@]}") > "$stage/SHA256SUMS"
    for f in "${BUILT[@]}"; do
        files+="$f  ($(du -h "$OUTDIR/$f" | cut -f1))"$'\n'"    sha256: $(sha256sum "$OUTDIR/$f" | cut -d' ' -f1)"$'\n  '
    done
    python3 - "$stage/store-info.txt" "$VERSION" "$files" <<'PY'
import sys
p, version, files = sys.argv[1:4]
s = open(p).read().replace("@VERSION@", version).replace("@FILES@", files.rstrip())
open(p, "w").write(s)
PY
    chmod +x "$stage/take-screenshots.sh"
    pack "$OUTDIR/$name.tar.gz" "$name"
    echo " ✓ $OUTDIR/$name.tar.gz ($(du -h "$OUTDIR/$name.tar.gz" | cut -f1))"
}

echo "==> Building Onze $VERSION"
BUILT=()
build original "onze-theme-$VERSION"
BUILT+=("onze-theme-$VERSION.tar.gz")
# the win11icons edition is built only when the Win11 icon archive is present in vendor/
if [[ -f "$DIR/vendor/Win11-icon-theme-main.tar.gz" ]]; then
    build win11icons "onze-theme-win11icons-$VERSION"
    BUILT+=("onze-theme-win11icons-$VERSION.tar.gz")
fi
if [[ -d "$DIR/tools/store-kit" ]]; then
    build_store_kit
fi
