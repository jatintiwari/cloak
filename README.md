# Cloak - Pro Stealth Browser for macOS

A native macOS application that is **completely invisible to screen sharing and recording**.

## Advanced Features
- **True Stealth:** Uses `NSWindowSharingNone` to ensure the window is not captured by Zoom, Google Meet, QuickTime, or other screen recorders.
- **HUD Interface:** Uses `NSVisualEffectView` for a native, blurred "glass" background.
- **Non-Activating Panel:** Operates as a system overlay that doesn't appear in the Dock or `Cmd+Tab`.
- **Multi-Space Persistence:** The window follows you across all macOS Desktops/Spaces automatically.
- **Native Browser:** Uses `WKWebView` (Safari engine) for high performance and low memory.
- **Global Hotkey:** Toggle the window instantly using `Cmd + Option + O`.
- **Status Bar Icon:** A discrete `⦿` icon in the menu bar for quick access.
- **Silent Mode**: Optimized for quiet operation with disabled logging.

## Build & Distribution

1. **Activate Environment**: `source venv/bin/activate`
2. **Run Build Script**:
   ```bash
   chmod +x build_dmg.sh
   ./build_dmg.sh
   ```
3. **Find your DMG**: The installer will be located in the `dist/` directory as `Cloak_Installer.dmg`.

## Prerequisites
- **macOS** (Required for native APIs)
- **Python 3.9+**

## Installation

1. **Clone or Download** this directory to your Mac.
2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the app**:
   ```bash
   python main.py
   ```
2. **Toggle Visibility**: Press `Cmd + Option + O` to show or hide the overlay.
3. **Permissions**: On first run, macOS will ask for **Accessibility** permissions. Grant these in `System Settings` to enable the global hotkey.

## How it Works
The app uses the `pyobjc` bridge to interface with macOS `AppKit` and `WebKit`. By setting the window's `sharingType` to `None`, the macOS window server is instructed to skip this window when generating screen capture streams for other applications.
