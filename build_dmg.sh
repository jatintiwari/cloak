#!/bin/bash

# Exit on error
set -e

# 1. Check OS
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "❌ Error: This build script must be run on macOS."
  exit 1
fi

echo "🚀 Starting build process..."

# 2. Install/Update build dependencies
echo "📦 Installing dependencies..."
pip install --use-pep517 -r requirements.txt
pip install --use-pep517 py2app

# 3. Generate icon if missing
if [ ! -f "cloak.icns" ] && [ -f "cloak.png" ]; then
  echo "🎨 Generating app icon from cloak.png..."
  mkdir -p cloak.iconset
  sips -z 16 16     cloak.png --out cloak.iconset/icon_16x16.png > /dev/null 2>&1
  sips -z 32 32     cloak.png --out cloak.iconset/icon_16x16@2x.png > /dev/null 2>&1
  sips -z 32 32     cloak.png --out cloak.iconset/icon_32x32.png > /dev/null 2>&1
  sips -z 64 64     cloak.png --out cloak.iconset/icon_32x32@2x.png > /dev/null 2>&1
  sips -z 128 128   cloak.png --out cloak.iconset/icon_128x128.png > /dev/null 2>&1
  sips -z 256 256   cloak.png --out cloak.iconset/icon_128x128@2x.png > /dev/null 2>&1
  sips -z 256 256   cloak.png --out cloak.iconset/icon_256x256.png > /dev/null 2>&1
  sips -z 512 512   cloak.png --out cloak.iconset/icon_256x256@2x.png > /dev/null 2>&1
  sips -z 512 512   cloak.png --out cloak.iconset/icon_512x512.png > /dev/null 2>&1
  sips -z 1024 1024 cloak.png --out cloak.iconset/icon_512x512@2x.png > /dev/null 2>&1
  iconutil -c icns cloak.iconset
  rm -R cloak.iconset
fi

# 4. Clear previous builds
rm -rf build dist

# 5. Build the .app bundle
echo "📦 Building .app bundle..."
python setup.py py2app

# 6. Create DMG
# We use hdiutil (native macOS tool) to create the disk image
APP_NAME="Cloak"
DMG_NAME="Cloak_Installer.dmg"

echo "Disk Image (DMG) creation..."

# Create a temporary directory for the DMG content
mkdir -p dist/dmg_content
cp -R "dist/${APP_NAME}.app" dist/dmg_content/

# Optional: Add a symlink to Applications folder
ln -s /Applications dist/dmg_content/Applications

# Create the DMG
hdiutil create -volname "${APP_NAME}" -srcfolder dist/dmg_content -ov -format UDZO "dist/${DMG_NAME}"

echo "✅ Success! DMG created at: dist/${DMG_NAME}"
echo "You can now distribute this DMG to other Macs."
