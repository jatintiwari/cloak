"""
Script to build the macOS .app bundle using py2app.
"""
from setuptools import setup

APP = ['main.py']
DATA_FILES = ['cloak.png']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'cloak.icns',
    'plist': {
        'LSUIElement': True,  # Accessory app (no Dock icon)
        'NSAppleEventsUsageDescription': 'Please give Cloak permission to use Apple Events.',
        'NSAccessibilityUsageDescription': 'Please give Cloak permission to use Accessibility for global hotkeys.',
        'CFBundleName': 'Cloak',
        'CFBundleDisplayName': 'Cloak',
        'CFBundleIdentifier': 'com.stealth.cloak',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    },
    'packages': [],
}

setup(
    name='Cloak',
    version='1.0.0',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
