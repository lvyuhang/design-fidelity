#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${REVIEW_PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" && -x "$ROOT/../.venv-fidelity/bin/python" ]]; then PYTHON="$ROOT/../.venv-fidelity/bin/python"; fi
BUILD="$ROOT/build/macos"
APP="$ROOT/dist/设计验收.app"
CONTENTS="$APP/Contents"
RESOURCES="$CONTENTS/Resources"

if [[ ! -x "$PYTHON" ]]; then
  echo "未找到打包 Python：$PYTHON" >&2
  exit 1
fi

rm -rf "$BUILD" "$APP"
mkdir -p "$BUILD" "$CONTENTS/MacOS" "$RESOURCES/platform-tools" "$ROOT/dist"

"$PYTHON" -m PyInstaller --noconfirm --clean --onedir --name review-server \
  --distpath "$BUILD/server-dist" --workpath "$BUILD/work" --specpath "$BUILD" \
  --add-data "$ROOT/static:static" --add-data "$ROOT/lanhu_bridge.py:." \
  --add-data "$ROOT/REVIEW_RULES.md:." \
  "$ROOT/server.py"

xcrun swiftc -O -parse-as-library \
  -framework Cocoa -framework WebKit \
  "$ROOT/macos/DesignReviewApp.swift" -o "$CONTENTS/MacOS/DesignReview"

cp "$ROOT/macos/Info.plist" "$CONTENTS/Info.plist"
ditto "$BUILD/server-dist/review-server" "$RESOURCES/review-server"
ADB="${REVIEW_ADB:-$(cd "$ROOT" && "$PYTHON" -c 'import capture; print(capture.find_adb() or "")')}"
cp "$ADB" "$RESOURCES/platform-tools/adb"
cp "$ROOT/.tools/scrcpy-server-v4.1" "$RESOURCES/scrcpy-server-v4.1"
chmod +x "$CONTENTS/MacOS/DesignReview" "$RESOURCES/platform-tools/adb" "$RESOURCES/review-server/review-server"

mkdir -p "$RESOURCES/SeedData"
# Only include seed data when explicitly requested by the packager.
if [[ -n "${REVIEW_SEED_DIR:-}" ]]; then ditto --norsrc --noextattr "$REVIEW_SEED_DIR" "$RESOURCES/SeedData"; fi

ICONSET="$BUILD/DesignReview.iconset"
mkdir -p "$ICONSET"
"$PYTHON" "$ROOT/macos/make_icon.py" "$ICONSET/icon_512x512@2x.png"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$ICONSET/icon_512x512@2x.png" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$ICONSET/icon_512x512@2x.png" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$RESOURCES/DesignReview.icns"

codesign --force --deep --sign - "$APP"
echo "$APP"
